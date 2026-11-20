#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit and Integration Tests for Episode Vision Validator & Quality Gate
"""

import os
from pathlib import Path
import sqlite3
import pytest

from scripts.episode_vision_validator import (
    EpisodeVisionValidator,
    SequenceQualityGate,
    DatabaseGateAuditor,
    ValidationResult,
    validate_video_file,
    auto_sort_and_quarantine_batch,
)


# ==============================================================================
# 1. Regex & Pattern Extraction Tests
# ==============================================================================

class TestEpisodeRegexParser:

    @pytest.mark.parametrize(
        "text,expected_ep,expected_total",
        [
            ("1-qism", 1, None),
            ("01 - qism", 1, None),
            ("12_qism", 12, None),
            ("4 qism", 4, None),
            ("16-seriya", 16, None),
            ("2-seria", 2, None),
            ("7-қисм", 7, None),
            ("8 кисм", 8, None),
            ("серия 9", 9, None),
            ("qism: 10", 10, None),
            ("Ep 5", 5, None),
            ("Episode 11", 11, None),
            ("E08", 8, None),
            ("Ajdarkar onasi 1-qism/Jami 70 ta epizod", 1, 70),
            ("16-qism (Jami: 16 qism)", 16, 16),
            ("Baxt qasri 25-qism Uzbek tilida 1080p", 25, None),
            ("5-qism / 24", 5, 24),
            ("Yangi dorama 3-qism 16+ yosh chegarasi", 3, None),
        ],
    )
    def test_valid_patterns(self, text, expected_ep, expected_total):
        ep, total = EpisodeVisionValidator.parse_episode_from_text(text)
        assert ep == expected_ep, f"Failed for text '{text}': got ep {ep}, expected {expected_ep}"
        if expected_total is not None:
            assert total == expected_total, f"Failed for total in '{text}': got {total}, expected {expected_total}"

    @pytest.mark.parametrize(
        "text",
        [
            "1080p Full HD video",
            "Faqat 16+ yoshdagilar uchun",
            "18 yoshdan kattalarga tavsiya etiladi",
            "2024-yil premyerasi",
            "Uzbek tilida tarjima",
        ],
    )
    def test_false_positives_rejection(self, text):
        ep, _ = EpisodeVisionValidator.parse_episode_from_text(text)
        assert ep is None, f"Expected None for false-positive text '{text}', but got {ep}"


# ==============================================================================
# 2. Monotonic Sequence Tests
# ==============================================================================

class TestMonotonicSequence:

    def test_perfect_sequence(self):
        items = [
            ValidationResult(video_source=f"v{i}.mp4", detected_ep=i, status="PASSED")
            for i in range(1, 6)
        ]
        is_valid, issues = SequenceQualityGate.validate_monotonic_sequence(items)
        assert is_valid is True
        assert len(issues) == 0

    def test_gap_detection(self):
        # 1, 2, 4 (missing 3)
        items = [
            ValidationResult(video_source="v1.mp4", detected_ep=1, status="PASSED"),
            ValidationResult(video_source="v2.mp4", detected_ep=2, status="PASSED"),
            ValidationResult(video_source="v4.mp4", detected_ep=4, status="PASSED"),
        ]
        is_valid, issues = SequenceQualityGate.validate_monotonic_sequence(items)
        assert is_valid is False
        assert any("gap" in s.lower() for s in issues)

    def test_duplicate_detection(self):
        # 1, 2, 2, 3
        items = [
            ValidationResult(video_source="v1.mp4", detected_ep=1, status="PASSED"),
            ValidationResult(video_source="v2.mp4", detected_ep=2, status="PASSED"),
            ValidationResult(video_source="v2_dup.mp4", detected_ep=2, status="PASSED"),
            ValidationResult(video_source="v3.mp4", detected_ep=3, status="PASSED"),
        ]
        is_valid, issues = SequenceQualityGate.validate_monotonic_sequence(items)
        assert is_valid is False
        assert any("duplicate" in s.lower() for s in issues)

    def test_out_of_order_detection(self):
        # 3, 1, 2
        items = [
            ValidationResult(video_source="v3.mp4", detected_ep=3, status="PASSED"),
            ValidationResult(video_source="v1.mp4", detected_ep=1, status="PASSED"),
            ValidationResult(video_source="v2.mp4", detected_ep=2, status="PASSED"),
        ]
        is_valid, issues = SequenceQualityGate.validate_monotonic_sequence(items)
        assert is_valid is False


# ==============================================================================
# 3. Auto-Sort & Quarantine Gate Tests
# ==============================================================================

class TestAutoSortAndQuarantine:

    def test_auto_sort_unordered_batch(self):
        # Out-of-order input: Ep 3, Ep 1, Ep 2
        items = [
            ValidationResult(video_source="ep3.mp4", detected_ep=3, assigned_ep=3, status="PASSED"),
            ValidationResult(video_source="ep1.mp4", detected_ep=1, assigned_ep=1, status="PASSED"),
            ValidationResult(video_source="ep2.mp4", detected_ep=2, assigned_ep=2, status="PASSED"),
        ]
        gate_res = SequenceQualityGate.auto_sort_or_quarantine(items)
        assert gate_res["is_clean"] is True
        assert gate_res["approved_count"] == 3
        assert gate_res["quarantined_count"] == 0
        sorted_eps = [r.detected_ep for r in gate_res["approved"]]
        assert sorted_eps == [1, 2, 3]

    def test_quarantine_mismatch(self):
        # Assigned 2, but on-screen detected 5
        items = [
            ValidationResult(video_source="ep1.mp4", detected_ep=1, assigned_ep=1, status="PASSED"),
            ValidationResult(video_source="ep2.mp4", detected_ep=5, assigned_ep=2, status="MISMATCH", reason="Mismatch"),
            ValidationResult(video_source="ep3.mp4", detected_ep=3, assigned_ep=3, status="PASSED"),
        ]
        gate_res = SequenceQualityGate.auto_sort_or_quarantine(items, allow_gaps=True)
        assert gate_res["is_clean"] is False
        assert gate_res["approved_count"] == 2
        assert gate_res["quarantined_count"] == 1
        assert gate_res["quarantined"][0].status == "MISMATCH"

    def test_quarantine_duplicate(self):
        items = [
            ValidationResult(video_source="ep1.mp4", detected_ep=1, assigned_ep=1, status="PASSED"),
            ValidationResult(video_source="ep2_a.mp4", detected_ep=2, assigned_ep=2, status="PASSED"),
            ValidationResult(video_source="ep2_b.mp4", detected_ep=2, assigned_ep=2, status="PASSED"),
        ]
        gate_res = SequenceQualityGate.auto_sort_or_quarantine(items)
        assert gate_res["approved_count"] == 2
        assert gate_res["quarantined_count"] == 1
        assert gate_res["quarantined"][0].status == "DUPLICATE"

    def test_quarantine_strict_ocr_unverified(self):
        items = [
            ValidationResult(video_source="ep1.mp4", detected_ep=1, assigned_ep=1, status="PASSED"),
            ValidationResult(video_source="ep2.mp4", detected_ep=None, assigned_ep=2, status="UNVERIFIED"),
        ]
        # In strict OCR mode, unverified items MUST be quarantined
        gate_res = SequenceQualityGate.auto_sort_or_quarantine(items, strict_ocr=True)
        assert gate_res["quarantined_count"] == 1
        assert gate_res["quarantined"][0].status == "QUARANTINED"


# ==============================================================================
# 4. Database Gate Auditor Tests
# ==============================================================================

class TestDatabaseGateAuditor:

    @pytest.fixture
    def test_db(self, tmp_path):
        db_path = tmp_path / "test_doramas.db"
        with sqlite3.connect(str(db_path)) as conn:
            conn.execute("""
                CREATE TABLE doramas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code INTEGER UNIQUE,
                    title TEXT NOT NULL,
                    total_episodes INTEGER DEFAULT 0
                );
            """)
            conn.execute("""
                CREATE TABLE episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dorama_id INTEGER NOT NULL,
                    episode_number INTEGER NOT NULL,
                    channel_message_id INTEGER NOT NULL,
                    quality TEXT DEFAULT '1080p',
                    file_size INTEGER DEFAULT 0
                );
            """)

            # Dorama 1: Clean (episodes 1, 2, 3)
            conn.execute("INSERT INTO doramas (id, code, title, total_episodes) VALUES (1, 101, 'Clean Dorama', 3);")
            conn.execute("INSERT INTO episodes (dorama_id, episode_number, channel_message_id) VALUES (1, 1, 1001);")
            conn.execute("INSERT INTO episodes (dorama_id, episode_number, channel_message_id) VALUES (1, 2, 1002);")
            conn.execute("INSERT INTO episodes (dorama_id, episode_number, channel_message_id) VALUES (1, 3, 1003);")

            # Dorama 2: Has Gap (episodes 1, 3 - missing 2)
            conn.execute("INSERT INTO doramas (id, code, title, total_episodes) VALUES (2, 102, 'Gapped Dorama', 3);")
            conn.execute("INSERT INTO episodes (dorama_id, episode_number, channel_message_id) VALUES (2, 1, 2001);")
            conn.execute("INSERT INTO episodes (dorama_id, episode_number, channel_message_id) VALUES (2, 3, 2003);")

            # Dorama 3: Has Invalid Msg ID
            conn.execute("INSERT INTO doramas (id, code, title, total_episodes) VALUES (3, 103, 'Invalid Msg Dorama', 1);")
            conn.execute("INSERT INTO episodes (dorama_id, episode_number, channel_message_id) VALUES (3, 1, 0);")

            conn.commit()
        return db_path

    def test_audit_db_sequence(self, test_db):
        auditor = DatabaseGateAuditor(db_path=test_db)
        findings = auditor.audit_db_dorama_sequence()

        # Dorama 1 should NOT be in findings (clean)
        # Dorama 2 and Dorama 3 should be flagged
        flagged_ids = [f["dorama_id"] for f in findings]
        assert 1 not in flagged_ids
        assert 2 in flagged_ids
        assert 3 in flagged_ids

        d2_finding = next(f for f in findings if f["dorama_id"] == 2)
        assert 2 in d2_finding["gaps"]

        d3_finding = next(f for f in findings if f["dorama_id"] == 3)
        assert 0 in d3_finding["invalid_message_ids"]

    def test_record_quarantine_event(self, test_db):
        auditor = DatabaseGateAuditor(db_path=test_db)
        res = ValidationResult(
            video_source="test_mismatch.mp4",
            assigned_ep=2,
            detected_ep=5,
            status="MISMATCH",
            reason="Watermark says 5, assigned 2",
            ocr_raw_text="5-qism Uzbek tilida",
        )
        row_id = auditor.record_quarantine_event(
            dorama_id=1,
            dorama_code=101,
            dorama_title="Clean Dorama",
            channel_message_id=9999,
            result=res,
        )
        assert row_id > 0

        # Verify entry in quarantined_episodes table
        with sqlite3.connect(str(test_db)) as conn:
            row = conn.execute("SELECT status, assigned_episode, detected_episode FROM quarantined_episodes WHERE id = ?", (row_id,)).fetchone()
            assert row[0] == "MISMATCH"
            assert row[1] == 2
            assert row[2] == 5


# ==============================================================================
# 5. Live File OCR End-to-End Test
# ==============================================================================

class TestLiveFileOcr:

    def test_real_video_sample_if_present(self):
        real_video = Path(r"E:\Agent\Drama Bot\posters\candidate_thumbs\vid_102935.mp4")
        if not real_video.exists():
            pytest.skip("Sample video vid_102935.mp4 not found on disk")

        res = validate_video_file(real_video, assigned_ep=1)
        assert res.status == "PASSED"
        assert res.detected_ep == 1
        assert res.detected_total == 70
        assert res.confidence > 0.7
