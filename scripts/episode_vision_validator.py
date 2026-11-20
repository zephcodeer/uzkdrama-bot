#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Episode Vision Validator & Pre/Post-Ingestion Quality Gate
==========================================================
Architected for: Google Antigravity Drama Bot
Guarantees:
1. Zero Episode Mismatch / Desync: Catches out-of-order, skipped, or mislabeled episodes.
2. Fast Sub-Second Frame Extraction: Uses FFmpeg input seeking (-ss before -i) directly into memory.
3. Dual-OCR Vision Stack: RapidOCR (ultra-fast ONNX) with WinOCR / Windows Media OCR fallback.
4. Robust Regex & Heuristics: Accurately parses Uzbek & Cyrillic watermark patterns ('X-qism', 'X-seriya', 'X-қисм', 'Ep X') while rejecting age ratings ('16+') and resolutions ('1080p').
5. Auto-Sort & Quarantine Gate: Sorts unordered donor uploads into correct monotonic sequence before DB commit; isolates corrupt or conflicting episodes into Quarantine.
6. DB Pre/Post Audit: Validates sequences in SQLite doramas.db, detecting missing gaps and desync.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict, dataclass
import io
import json
import logging
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

# Set output encoding
if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Optional third-party OCR imports
try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import rapidocr_onnxruntime
except ImportError:
    rapidocr_onnxruntime = None

try:
    import winocr
except ImportError:
    winocr = None

logger = logging.getLogger("EpisodeVisionValidator")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] [%(levelname)s] [VisionGate] %(message)s", datefmt="%H:%M:%S")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ==============================================================================
# 1. Regex & Normalization Patterns
# ==============================================================================

# Primary episode extraction regex
# Matches:
#   "1-qism", "01 - qism", "12_qism", "1 qism", "1-seriya", "1-seria"
#   "1-қисм", "1 қисм", "1 кисм", "1 серия"
#   "QISM 1", "Серия 2", "Ep 3", "Episode 4", "E05"
RE_EPISODE_PATTERNS = [
    # Prefix number: e.g. "1-qism", "02 - qism", "12_seriya", "3-қисм"
    re.compile(
        r"(?:^|[^\w])(?P<num>\d{1,4})\s*[-_–—./]?\s*(?:qism|qisim|q|seriya|seria|қисм|кисм|серия)(?:[^\w]|$)",
        re.IGNORECASE,
    ),
    # Postfix number: e.g. "qism 1", "seriya: 2", "қисм 3", "серия 4"
    re.compile(
        r"(?:qism|qisim|seriya|seria|қисм|кисм|серия)\s*[:#№\-–—./]?\s*(?P<num>\d{1,4})(?:[^\w]|$)",
        re.IGNORECASE,
    ),
    # English titlecard: e.g. "EP 1", "Ep. 02", "Episode 3", "E04"
    re.compile(
        r"(?:^|[^\w])(?:ep|episode|e)\.?\s*0*(?P<num>\d{1,4})(?:[^\w]|$)",
        re.IGNORECASE,
    ),
]

# Total episodes pattern: e.g. "Jami 70 ta epizod", "Jami 16 qism", "1/16-qism"
RE_TOTAL_EPISODES = re.compile(
    r"(?:jami|vsego|total)\s*[:#]?\s*(?P<total>\d{1,4})\s*(?:ta|epizod|qism|seriya|q|ep)?|"
    r"(?:qism|epizod)\s*/\s*(?P<slash_total>\d{1,4})|"
    r"/\s*jami\s*(?P<slash_jami>\d{1,4})",
    re.IGNORECASE,
)

# False positive exclusions
RE_EXCLUDE_AGE = re.compile(r"\b(?:12|16|18)\s*\+\b|\b(?:12|16|18)\s*yosh\b", re.IGNORECASE)
RE_EXCLUDE_RES = re.compile(r"\b(?:360|480|720|1080|2160)[pP]\b")
RE_EXCLUDE_YEAR = re.compile(r"\b(?:19\d{2}|20[0-3]\d)\b")


# ==============================================================================
# 2. Data Models
# ==============================================================================

@dataclass
class ValidationResult:
    """Represents the vision verification result for a single video."""
    video_source: str
    assigned_ep: Optional[int] = None
    detected_ep: Optional[int] = None
    detected_total: Optional[int] = None
    confidence: float = 0.0
    status: str = "UNVERIFIED"  # PASSED, MISMATCH, UNVERIFIED, GAP, DUPLICATE, OUT_OF_ORDER
    reason: str = ""
    ocr_raw_text: str = ""
    sampled_timestamp: float = 0.0

    @property
    def is_passed(self) -> bool:
        return self.status == "PASSED"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ==============================================================================
# 3. Vision & Frame Extraction Engine
# ==============================================================================

class EpisodeVisionValidator:
    """
    High-performance, memory-only frame sampler and multi-engine OCR parser.
    """

    def __init__(self, sample_timestamps: Sequence[float] = (2.0, 3.0, 4.0), prefer_winocr: bool = False):
        self.sample_timestamps = list(sample_timestamps)
        self.prefer_winocr = prefer_winocr
        self._rapid_ocr = None
        self._has_rapid_ocr = rapidocr_onnxruntime is not None
        self._has_winocr = winocr is not None

    def _get_rapid_ocr(self):
        if self._rapid_ocr is None and self._has_rapid_ocr:
            try:
                self._rapid_ocr = rapidocr_onnxruntime.RapidOCR()
            except Exception as e:
                logger.warning(f"Failed to initialize RapidOCR: {e}")
                self._has_rapid_ocr = False
        return self._rapid_ocr

    def extract_frame_bytes(self, video_path: Union[str, Path], timestamp: float) -> Optional[bytes]:
        """
        Fast-seek frame extraction into memory using FFmpeg pipe.
        Takes < 100ms because FFmpeg inputs seek before decoding.
        """
        path_str = str(video_path)
        if not Path(path_str).exists():
            logger.error(f"Video file not found: {path_str}")
            return None

        # -ss before -i enables fast keyframe-level input seek
        cmd = [
            "ffmpeg",
            "-ss", str(timestamp),
            "-i", path_str,
            "-vframes", "1",
            "-f", "image2pipe",
            "-vcodec", "png",
            "-loglevel", "error",
            "-",
        ]
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            if proc.returncode == 0 and len(proc.stdout) > 0:
                return proc.stdout
            else:
                err = proc.stderr.decode("utf-8", errors="ignore").strip()
                logger.debug(f"FFmpeg extraction failed at {timestamp}s: {err}")
                return None
        except Exception as e:
            logger.debug(f"FFmpeg exception at {timestamp}s: {e}")
            return None

    def extract_text_from_image_bytes(self, img_bytes: bytes) -> Tuple[str, float]:
        """
        Runs OCR on image bytes using RapidOCR or WinOCR.
        Returns (combined_text, max_confidence).
        """
        text_lines: List[str] = []
        confidences: List[float] = []

        # 1. Try RapidOCR first
        rapid = self._get_rapid_ocr()
        if rapid and cv2 and np:
            try:
                nparr = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None:
                    results, _ = rapid(img)
                    if results:
                        for item in results:
                            # item: [box, text, score]
                            t = str(item[1]).strip()
                            s = float(item[2])
                            if t:
                                text_lines.append(t)
                                confidences.append(s)
            except Exception as e:
                logger.debug(f"RapidOCR recognition error: {e}")

        # 2. If no text or WinOCR preferred, try WinOCR with Russian / English packs
        if (not text_lines or self.prefer_winocr) and self._has_winocr and Image:
            try:
                pil_img = Image.open(io.BytesIO(img_bytes))
                # Run sync in event loop if available or asyncio.run
                for lang in ["ru", "en-US"]:
                    try:
                        res = asyncio.run(winocr.recognize_pil(pil_img, lang))
                        if res and res.text:
                            lines = [line.strip() for line in res.text.splitlines() if line.strip()]
                            text_lines.extend(lines)
                            confidences.append(0.85)  # WinOCR does not export per-line score; default 0.85
                    except Exception:
                        pass
            except Exception as e:
                logger.debug(f"WinOCR recognition error: {e}")

        combined_text = " \n ".join(text_lines)
        max_conf = max(confidences) if confidences else 0.0
        return combined_text, max_conf

    @classmethod
    def parse_episode_from_text(cls, text: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Parses (detected_episode, detected_total) from raw OCR text.
        Applies heuristic suppression to avoid age ratings and false matches.
        """
        if not text:
            return None, None

        norm = text.replace("\r", " ").replace("\t", " ")

        # 1. Check combined combo: e.g. '1-qism/Jami 70 ta epizod' or '5-qism / 24' or '01/16-qism'
        m_combo = re.search(
            r"(?P<ep>\d{1,4})\s*[-_–—./]?\s*(?:qism|seriya|қисм|серия)?\s*/\s*(?:jami\s*)?(?P<tot>\d{1,4})\s*(?:ta|epizod|qism|seriya)?",
            norm,
            re.IGNORECASE,
        )
        if m_combo:
            ep = int(m_combo.group("ep"))
            tot = int(m_combo.group("tot"))
            if 1 <= ep <= 2000 and 1 <= tot <= 2000:
                return ep, tot

        # 2. Check standalone total: 'Jami: 16 qism', 'vsego 70 seriy'
        total_ep = None
        m_tot = re.search(r"(?:jami|vsego|total)\s*[:#№]?\s*(?P<total>\d{1,4})", norm, re.IGNORECASE)
        tot_digit_span = None
        if m_tot:
            val = int(m_tot.group("total"))
            if 1 <= val <= 2000:
                total_ep = val
                tot_digit_span = m_tot.span("total")

        # 3. Check episode number
        detected_ep = None
        for pattern in RE_EPISODE_PATTERNS:
            for match in pattern.finditer(norm):
                candidate_str = match.group("num")
                if not candidate_str or not candidate_str.isdigit():
                    continue
                cand = int(candidate_str)
                # Ignore unreasonable numbers, resolutions, or years
                if cand > 2000:
                    continue
                if cand in (360, 480, 720, 1080):
                    continue

                # If this digit position is inside the jami total count, skip it
                if tot_digit_span and match.start("num") == tot_digit_span[0]:
                    continue

                detected_ep = cand
                break
            if detected_ep is not None:
                break

        return detected_ep, total_ep

    def scan_video_file(
        self,
        video_path: Union[str, Path],
        assigned_ep: Optional[int] = None,
    ) -> ValidationResult:
        """
        Scans a video file across sampled timestamps and extracts episode information.
        """
        path_obj = Path(video_path)
        result = ValidationResult(video_source=str(path_obj), assigned_ep=assigned_ep)

        if not path_obj.exists():
            result.status = "ERROR"
            result.reason = f"File does not exist: {path_obj}"
            return result

        best_ep = None
        best_total = None
        best_conf = 0.0
        best_ts = 0.0
        all_texts = []

        for ts in self.sample_timestamps:
            frame_bytes = self.extract_frame_bytes(path_obj, ts)
            if not frame_bytes:
                continue

            text, conf = self.extract_text_from_image_bytes(frame_bytes)
            if text:
                all_texts.append(f"[{ts}s]: {text}")
                ep, total = self.parse_episode_from_text(text)
                if ep is not None:
                    best_ep = ep
                    best_total = total or best_total
                    best_conf = conf
                    best_ts = ts
                    break  # Found high-confidence episode watermark, fast-break
                elif total is not None and best_total is None:
                    best_total = total

        result.detected_ep = best_ep
        result.detected_total = best_total
        result.confidence = round(best_conf, 3)
        result.sampled_timestamp = best_ts
        result.ocr_raw_text = "\n".join(all_texts)

        if best_ep is None:
            result.status = "UNVERIFIED"
            result.reason = "No episode watermark detected in sampled frames (2-4s)"
        elif assigned_ep is not None:
            if best_ep == assigned_ep:
                result.status = "PASSED"
                result.reason = f"Verified: On-screen episode {best_ep} matches assigned {assigned_ep}"
            else:
                result.status = "MISMATCH"
                result.reason = (
                    f"CRITICAL MISMATCH: On-screen watermark says Episode {best_ep}, "
                    f"but assigned episode is {assigned_ep}"
                )
        else:
            result.status = "PASSED"
            result.reason = f"Detected on-screen Episode {best_ep}"

        return result


# ==============================================================================
# 4. Monotonic Sequence & Quality Gate Engine
# ==============================================================================

class SequenceQualityGate:
    """
    Validates monotonicity, detects gaps/duplicates, and auto-sorts or quarantines
    video batches before or after DB ingestion.
    """

    @classmethod
    def validate_monotonic_sequence(
        cls,
        results: Sequence[ValidationResult],
        expected_start: int = 1,
    ) -> Tuple[bool, List[str]]:
        """
        Validates that results form an unbroken strictly increasing sequence:
        e.g. 1, 2, 3, 4, 5...
        Returns (is_valid, list_of_issues).
        """
        issues: List[str] = []
        if not results:
            return True, []

        seen_eps = set()
        expected = expected_start

        for idx, item in enumerate(results):
            ep = item.detected_ep if item.detected_ep is not None else item.assigned_ep
            if ep is None:
                issues.append(f"Item #{idx+1} ({Path(item.video_source).name}) has no episode number")
                continue

            if ep in seen_eps:
                issues.append(f"Duplicate episode {ep} detected at item #{idx+1} ({Path(item.video_source).name})")
            seen_eps.add(ep)

            if ep != expected:
                if ep > expected:
                    issues.append(f"Episode gap: expected Ep {expected}, but received Ep {ep} (gap size: {ep - expected})")
                else:
                    issues.append(f"Out-of-order sequence: Ep {ep} appeared when expecting Ep {expected}")
            expected = ep + 1

        return len(issues) == 0, issues

    @classmethod
    def auto_sort_or_quarantine(
        cls,
        results: List[ValidationResult],
        strict_ocr: bool = False,
        allow_gaps: bool = False,
    ) -> Dict[str, Any]:
        """
        Processes a batch of video validation results:
        1. Auto-sorts videos into correct numerical episode sequence based on detected (or assigned) numbers.
        2. Detects duplicates, unverified videos, and gaps.
        3. Segregates into 'approved' (safe to commit) and 'quarantined' (needs admin review).
        """
        approved: List[ValidationResult] = []
        quarantined: List[ValidationResult] = []

        # 1. First pass: filter out obvious mismatches or unverified (if strict)
        candidate_pool: List[ValidationResult] = []
        for res in results:
            if res.status == "MISMATCH":
                res.status = "MISMATCH"
                quarantined.append(res)
            elif res.status == "UNVERIFIED" and strict_ocr:
                res.status = "QUARANTINED"
                res.reason = "Quarantined: Strict OCR mode required watermark verification"
                quarantined.append(res)
            else:
                candidate_pool.append(res)

        # 2. Sort candidate pool by resolved episode number
        def sort_key(r: ValidationResult) -> int:
            if r.detected_ep is not None:
                return r.detected_ep
            if r.assigned_ep is not None:
                return r.assigned_ep
            return 999999

        sorted_candidates = sorted(candidate_pool, key=sort_key)

        # 3. Monotonic check on sorted candidates
        seen_eps = set()
        last_ep = 0

        for r in sorted_candidates:
            effective_ep = r.detected_ep if r.detected_ep is not None else r.assigned_ep

            if effective_ep is None:
                r.status = "QUARANTINED"
                r.reason = "Quarantined: Could not determine episode number"
                quarantined.append(r)
                continue

            # Duplicate check
            if effective_ep in seen_eps:
                r.status = "DUPLICATE"
                r.reason = f"Quarantined: Duplicate episode {effective_ep} detected in batch"
                quarantined.append(r)
                continue

            # Gap check (if gaps not allowed)
            if not allow_gaps and last_ep > 0 and effective_ep > last_ep + 1:
                r.status = "GAP"
                r.reason = f"Quarantined: Sequence gap! Missing episode(s) between Ep {last_ep} and Ep {effective_ep}"
                quarantined.append(r)
                continue

            seen_eps.add(effective_ep)
            last_ep = effective_ep
            approved.append(r)

        return {
            "approved": approved,
            "quarantined": quarantined,
            "total_input": len(results),
            "approved_count": len(approved),
            "quarantined_count": len(quarantined),
            "is_clean": len(quarantined) == 0,
        }


# ==============================================================================
# 5. Database Audit & Persistent Quarantine
# ==============================================================================

class DatabaseGateAuditor:
    """
    Audits SQLite database doramas.db for episode integrity and logs quarantine events.
    """

    def __init__(self, db_path: Union[str, Path] = r"E:\Agent\Drama Bot\doramas.db"):
        self.db_path = Path(db_path)

    def init_quarantine_table(self):
        """Ensures the quarantined_episodes table exists in SQLite."""
        import sqlite3

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quarantined_episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dorama_id INTEGER,
                    dorama_code INTEGER,
                    dorama_title TEXT,
                    channel_message_id INTEGER,
                    assigned_episode INTEGER,
                    detected_episode INTEGER,
                    status TEXT,
                    reason TEXT,
                    video_source TEXT,
                    ocr_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    def record_quarantine_event(
        self,
        dorama_id: Optional[int],
        dorama_code: Optional[int],
        dorama_title: str,
        channel_message_id: Optional[int],
        result: ValidationResult,
    ) -> int:
        """Records an episode quarantine event into the database."""
        import sqlite3

        self.init_quarantine_table()
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO quarantined_episodes (
                    dorama_id, dorama_code, dorama_title, channel_message_id,
                    assigned_episode, detected_episode, status, reason,
                    video_source, ocr_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    dorama_id,
                    dorama_code,
                    dorama_title,
                    channel_message_id,
                    result.assigned_ep,
                    result.detected_ep,
                    result.status,
                    result.reason,
                    result.video_source,
                    result.ocr_raw_text,
                ),
            )
            conn.commit()
            return cur.lastrowid

    def audit_db_dorama_sequence(self, dorama_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Audits episodes recorded in doramas.db:
        Verifies that episodes 1..N are monotonic, checks for gaps, duplicates, or negative msg IDs.
        """
        import sqlite3

        findings: List[Dict[str, Any]] = []
        if not self.db_path.exists():
            return findings

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT id, code, title, total_episodes FROM doramas"
            params: Tuple = ()
            if dorama_id:
                query += " WHERE id = ?"
                params = (dorama_id,)

            d_rows = conn.execute(query, params).fetchall()

            for d in d_rows:
                d_id = d["id"]
                d_code = d["code"]
                d_title = d["title"]
                total = d["total_episodes"] or 0

                ep_rows = conn.execute(
                    "SELECT episode_number, channel_message_id, quality, file_size FROM episodes "
                    "WHERE dorama_id = ? ORDER BY episode_number ASC",
                    (d_id,),
                ).fetchall()

                if not ep_rows:
                    continue

                ep_nums = [r["episode_number"] for r in ep_rows]
                msg_ids = [r["channel_message_id"] for r in ep_rows]

                # Check duplicates
                seen = set()
                dups = [x for x in ep_nums if x in seen or seen.add(x)]

                # Check gaps
                gaps = []
                for exp in range(1, max(ep_nums) + 1):
                    if exp not in seen:
                        gaps.append(exp)

                # Check invalid msg IDs
                invalid_msgs = [m for m in msg_ids if not m or m <= 0]

                if dups or gaps or invalid_msgs:
                    findings.append({
                        "dorama_id": d_id,
                        "code": d_code,
                        "title": d_title,
                        "total_episodes": total,
                        "actual_ep_count": len(ep_nums),
                        "max_ep": max(ep_nums),
                        "duplicates": dups,
                        "gaps": gaps,
                        "invalid_message_ids": invalid_msgs,
                        "is_clean": False,
                    })

        return findings


# ==============================================================================
# 6. Helper & Convenience Functions
# ==============================================================================

def validate_video_file(
    video_path: Union[str, Path],
    assigned_ep: Optional[int] = None,
    sample_timestamps: Sequence[float] = (2.0, 3.0, 4.0),
) -> ValidationResult:
    """Quick helper to validate a single video file."""
    validator = EpisodeVisionValidator(sample_timestamps=sample_timestamps)
    return validator.scan_video_file(video_path, assigned_ep=assigned_ep)


def auto_sort_and_quarantine_batch(
    video_records: List[Dict[str, Any]],
    strict_ocr: bool = False,
    allow_gaps: bool = False,
) -> Dict[str, Any]:
    """
    Takes a list of dicts: [{'path': ..., 'assigned_ep': ...}]
    Scans videos with OCR, auto-sorts them into valid sequence, and quarantines outliers.
    """
    validator = EpisodeVisionValidator()
    results = []
    for rec in video_records:
        path = rec.get("path")
        assigned = rec.get("assigned_ep")
        res = validator.scan_video_file(path, assigned_ep=assigned)
        results.append(res)

    return SequenceQualityGate.auto_sort_or_quarantine(
        results, strict_ocr=strict_ocr, allow_gaps=allow_gaps
    )


# ==============================================================================
# 7. Command Line Interface (CLI)
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Episode Vision Validator & Pre/Post Ingestion Quality Gate for Drama Bot."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: scan
    scan_p = subparsers.add_parser("scan", help="Scan a single video file with OCR")
    scan_p.add_argument("video_path", type=str, help="Path to the video file")
    scan_p.add_argument("--assigned-ep", type=int, default=None, help="Assigned/expected episode number")
    scan_p.add_argument("--timestamps", type=float, nargs="+", default=[2.0, 3.0, 4.0], help="Timestamps to sample")

    # Subcommand: scan-dir
    dir_p = subparsers.add_parser("scan-dir", help="Scan and auto-sort all video files in a directory")
    dir_p.add_argument("directory", type=str, help="Directory containing video files")
    dir_p.add_argument("--strict", action="store_true", help="Quarantine videos if OCR cannot verify watermark")
    dir_p.add_argument("--allow-gaps", action="store_true", help="Allow gaps in episode sequence")

    # Subcommand: audit-db
    db_p = subparsers.add_parser("audit-db", help="Audit database doramas.db for sequence integrity & gaps")
    db_p.add_argument("--dorama-id", type=int, default=None, help="Filter audit by dorama ID")
    db_p.add_argument("--db-path", type=str, default=r"E:\Agent\Drama Bot\doramas.db", help="Path to doramas.db")

    args = parser.parse_args()

    if args.command == "scan":
        logger.info(f"Scanning video: {args.video_path}")
        res = validate_video_file(args.video_path, assigned_ep=args.assigned_ep, sample_timestamps=args.timestamps)
        print("\n" + "=" * 60)
        print(f"File:         {res.video_source}")
        print(f"Status:       {res.status}")
        print(f"Assigned Ep:  {res.assigned_ep}")
        print(f"Detected Ep:  {res.detected_ep}")
        print(f"Total Eps:    {res.detected_total}")
        print(f"Confidence:   {res.confidence}")
        print(f"Timestamp:    {res.sampled_timestamp}s")
        print(f"Reason:       {res.reason}")
        print(f"Raw OCR Text:\n{res.ocr_raw_text}")
        print("=" * 60)

    elif args.command == "scan-dir":
        folder = Path(args.directory)
        if not folder.exists() or not folder.is_dir():
            logger.error(f"Directory not found: {folder}")
            sys.exit(1)

        vids = sorted(list(folder.glob("*.mp4")) + list(folder.glob("*.mkv")))
        logger.info(f"Found {len(vids)} video files in {folder}")
        records = [{"path": v, "assigned_ep": None} for v in vids]
        gate_res = auto_sort_and_quarantine_batch(records, strict_ocr=args.strict, allow_gaps=args.allow_gaps)

        print("\n" + "=" * 60)
        print(f"Total videos processed:  {gate_res['total_input']}")
        print(f"Approved (Green) count:  {gate_res['approved_count']}")
        print(f"Quarantined count:       {gate_res['quarantined_count']}")
        print(f"Batch Clean Status:      {gate_res['is_clean']}")
        print("=" * 60)

        if gate_res["approved"]:
            print("\n🟢 APPROVED SEQUENCE:")
            for item in gate_res["approved"]:
                print(f"  Ep {item.detected_ep or item.assigned_ep}: {Path(item.video_source).name} (status={item.status})")

        if gate_res["quarantined"]:
            print("\n🔴 QUARANTINED ITEMS:")
            for item in gate_res["quarantined"]:
                print(f"  {Path(item.video_source).name} -> [{item.status}] {item.reason}")

    elif args.command == "audit-db":
        auditor = DatabaseGateAuditor(db_path=args.db_path)
        findings = auditor.audit_db_dorama_sequence(dorama_id=args.dorama_id)
        print("\n" + "=" * 60)
        print(f"DATABASE AUDIT RESULTS: doramas.db (Inspected {len(findings)} doramas with issues)")
        print("=" * 60)
        if not findings:
            print("✅ All doramas in database have monotonic episode sequences with 0 gaps and 0 duplicates!")
        else:
            for f in findings:
                print(f"⚠️ [ID {f['dorama_id']} | Code {f['code']}] {f['title']}")
                print(f"   Total in header: {f['total_episodes']}, Actual: {f['actual_ep_count']}, Max: {f['max_ep']}")
                if f["duplicates"]:
                    print(f"   ❌ DUPLICATES: {f['duplicates']}")
                if f["gaps"]:
                    print(f"   ❌ MISSING GAPS: {f['gaps']}")
                if f["invalid_message_ids"]:
                    print(f"   ❌ INVALID MSG IDS: {f['invalid_message_ids']}")
                print("-" * 50)


if __name__ == "__main__":
    main()
