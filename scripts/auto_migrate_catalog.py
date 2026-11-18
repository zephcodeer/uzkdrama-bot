import argparse
import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
import random
import re
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

TG_AGENT_ROOT = Path(r"C:\Users\MuhammadSodiq\.gemini\antigravity\scratch\TG AI PERSON")
DRAMA_BOT_ROOT = Path(r"E:\Agent\Drama Bot")
REPORT_PATH = Path(
    r"C:\Users\MuhammadSodiq\.gemini\antigravity\brain\680976b1-3abc-4cda-8304-fa727e684760\catalog_missing_report.md"
)
STATE_PATH = DRAMA_BOT_ROOT / "scripts" / "catalog_migration_state.json"
DB_PATH = DRAMA_BOT_ROOT / "doramas.db"
STORAGE_DEST = "-1004336427887"
SOURCE_GROUP = "@Dramalar_Catalogi"
EXCLUDED_TOPICS = {
    118856,  # BTS maktabi (user explicitly excluded)
}

sys.path.insert(0, str(TG_AGENT_ROOT / "src"))

from tg_agent.client import build_telegram_client  # noqa: E402
from tg_agent.config import load_settings  # noqa: E402
from tg_agent.safety import SafetyGuard  # noqa: E402
from tg_agent.topic_forwarder import (  # noqa: E402
    ForwardLedger,
    _default_ledger_path,
    forward_topic_batch_safe,
)
from tg_agent.topics import fetch_topic_messages_paginated  # noqa: E402


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = s.replace("ʻ", "").replace("ʼ", "").replace("‘", "").replace("’", "").replace("'", "")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "dorama"


def parse_missing_topics_from_report() -> list[tuple[int, str]]:
    text = REPORT_PATH.read_text(encoding="utf-8")
    # Only Section 1 (ANIQ YO'Q)
    sec1 = text.split("## 2.")[0]
    items: list[tuple[int, str]] = []
    for line in sec1.splitlines():
        m = re.match(r"^\|\s*\d+\s*\|\s*`(\d+)`\s*\|\s*(.+?)\s*\|\s*\[Ochish\]", line)
        if m:
            tid = int(m.group(1))
            title = m.group(2).replace("\\|", "|").strip()
            if tid not in EXCLUDED_TOPICS:
                items.append((tid, title))
    return items


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"migrated": {}, "skipped": {}, "errors": {}}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def guess_metadata(title: str, raw_messages: list) -> dict:
    all_text = "\n".join((getattr(m, "message", None) or "") for m in raw_messages[:5])
    low = all_text.lower()
    title_low = title.lower()

    # Country / Category
    country = "Janubiy Koreya"
    category = "korea"
    if any(k in low or k in title_low for k in ["xitoy", "china", "cdrama", "xitoycha"]):
        country = "Xitoy"
        category = "china"
    elif any(k in low or k in title_low for k in ["turk", "turkiya"]):
        country = "Turkiya"
        category = "turk"
    elif any(k in low or k in title_low for k in ["yapon", "anime", "japan"]):
        country = "Yaponiya"
        category = "foreign"
    elif any(k in low or k in title_low for k in ["tailand", "thailand", "lakorn"]):
        country = "Tailand"
        category = "foreign"

    # Genre
    genre_m = re.search(r"(?:janr[i]?|genre)\s*[:\-➺•]\s*([^\n#]+)", all_text, re.I)
    genre = genre_m.group(1).strip(" .|")[:90] if genre_m else "Dorama, Drama"

    # Year
    year_m = re.search(r"\b(201\d|202[0-6])\b", all_text)
    year = int(year_m.group(1)) if year_m else 2025

    # Status
    tail_text = "\n".join((getattr(m, "message", None) or "") for m in raw_messages[-3:]).lower()
    if any(k in tail_text for k in ["final", "tugallangan", "yakunlandi", "oxirgi qism", "film"]):
        status = "Tugallangan (Completed)"
    else:
        status = "Ongoing"

    # Description
    desc = f"«{title}» — o‘zbek tilidagi tarjima dorama. Barcha mavjud qismlarni HD sifatda tomosha qiling."

    # Clean aliases
    clean_t = re.sub(r"[#*_🎬🎥📽️❤️🔥😎😘💗🎞🇺🇿🌍⚔️]", "", title).strip()
    ascii_t = clean_t.replace("ʻ", "'").replace("ʼ", "'").replace("‘", "'").replace("’", "'")
    no_ap = ascii_t.replace("'", "")
    aliases = ", ".join(dict.fromkeys([clean_t, ascii_t, no_ap]))

    return {
        "title": clean_t,
        "genre": genre,
        "year": year,
        "country": country,
        "category": category,
        "status": status,
        "description": desc,
        "aliases": aliases,
    }


def extract_ep_num(caption: str) -> int | None:
    if not caption:
        return None
    # Match patterns like "1-qism", "12 qism", "03-qisim", "1 seriya", "Ep 5"
    m = re.search(r"\b(\d{1,3})\s*[-–.]?\s*(?:chi\s*)?(?:qism|qisim|qsim|seriya)\b", caption, re.I)
    if m:
        val = int(m.group(1))
        if 1 <= val <= 500:
            return val
    m2 = re.search(r"\b(?:ep|episode|qism)\s*[:.#-]?\s*(\d{1,3})\b", caption, re.I)
    if m2:
        val = int(m2.group(1))
        if 1 <= val <= 500:
            return val
    return None


def get_video_info(msg) -> tuple[int, str, float]:
    fsize = 0
    w = h = 0
    dur = 0.0
    doc = getattr(msg, "document", None)
    if doc:
        fsize = int(getattr(doc, "size", 0) or 0)
        for attr in getattr(doc, "attributes", []) or []:
            if attr.__class__.__name__ == "DocumentAttributeVideo":
                w = int(getattr(attr, "w", 0) or 0)
                h = int(getattr(attr, "h", 0) or 0)
                dur = float(getattr(attr, "duration", 0.0) or 0.0)
    qual = "1080p" if (w >= 1900 or h >= 1000) else "720p"
    return fsize, qual, dur


async def download_topic_poster(client, raw_messages: list, code: int) -> str:
    posters_dir = DRAMA_BOT_ROOT / "posters"
    posters_dir.mkdir(exist_ok=True)
    rel_path = f"posters/code_{code}.jpg"
    abs_path = DRAMA_BOT_ROOT / rel_path

    # 1. Prefer an explicit photo message in the topic
    for m in raw_messages[:8]:
        if getattr(m, "photo", None):
            try:
                res = await client.download_media(m, file=str(abs_path))
                if res and abs_path.exists() and abs_path.stat().st_size > 5000:
                    return rel_path
            except Exception:
                pass

    # 2. Fallback: largest video thumbnail from first video
    for m in raw_messages:
        doc = getattr(m, "document", None)
        if doc and getattr(doc, "thumbs", None):
            try:
                res = await client.download_media(m, file=str(abs_path), thumb=-1)
                if res and abs_path.exists() and abs_path.stat().st_size > 1000:
                    return rel_path
            except Exception:
                pass

    return ""


def lookup_forwarded_map(ledger_db: Path, src_group_id: int, topic_id: int, dest_id: int) -> dict[int, int]:
    with sqlite3.connect(ledger_db) as conn:
        rows = conn.execute(
            """
            SELECT source_message_id, new_message_id
            FROM forwarded_items
            WHERE source_group_id = ? AND source_topic_id = ? AND dest_id = ? AND dest_topic_id = 0
            ORDER BY source_message_id ASC
            """,
            (int(src_group_id), int(topic_id), int(dest_id)),
        ).fetchall()
    return {int(src): int(dst) for src, dst in rows if dst is not None}


def insert_dorama_and_episodes(meta: dict, poster_rel: str, ep_records: list[tuple[int, int, int, str]]) -> tuple[int, int]:
    """Atomically insert new dorama + episodes into doramas.db with strict zero-collision check."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        # Check zero collision across ALL existing episodes
        msg_ids = [r[1] for r in ep_records]
        placeholders = ",".join("?" for _ in msg_ids)
        existing_col = cur.execute(
            f"SELECT e.channel_message_id, d.code, d.title FROM episodes e JOIN doramas d ON d.id = e.dorama_id WHERE e.channel_message_id IN ({placeholders})",
            msg_ids,
        ).fetchall()
        if existing_col:
            raise ValueError(f"Cross-dorama collision detected: {existing_col}")

        # Next ID and Code
        max_id = cur.execute("SELECT COALESCE(MAX(id), 0) FROM doramas").fetchone()[0]
        new_id = int(max_id) + 1
        new_code = 100 + new_id

        # Unique slug
        base_slug = slugify(meta["title"])
        slug = base_slug
        n = 2
        while cur.execute("SELECT 1 FROM doramas WHERE slug = ?", (slug,)).fetchone():
            slug = f"{base_slug}-{n}"
            n += 1

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            """
            INSERT INTO doramas (
                id, code, title, slug, genre, year, description, poster_url,
                total_episodes, views, created_at, status, country, actors, category, aliases, series_group
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, '', ?, ?, '')
            """,
            (
                new_id,
                new_code,
                meta["title"],
                slug,
                meta["genre"],
                meta["year"],
                meta["description"],
                poster_rel,
                len(ep_records),
                now_str,
                meta["status"],
                meta["country"],
                meta["category"],
                meta["aliases"],
            ),
        )

        for ep_num, ch_msg_id, fsize, qual in ep_records:
            cur.execute(
                """
                INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_id, file_size, quality)
                VALUES (?, ?, ?, '', ?, ?)
                """,
                (new_id, ep_num, ch_msg_id, fsize, qual),
            )

        conn.commit()
    return new_id, new_code


async def run_migration(limit: int, send_update: bool):
    os.chdir(TG_AGENT_ROOT)
    settings = load_settings()
    guard = SafetyGuard(settings)
    ledger_path = _default_ledger_path(settings)
    ledger = ForwardLedger(ledger_path)

    all_missing = parse_missing_topics_from_report()
    state = load_state()

    queue = [
        (tid, title)
        for tid, title in all_missing
        if str(tid) not in state["migrated"] and str(tid) not in state["skipped"]
    ]
    print(f"Total missing candidates: {len(all_missing)} | Remaining in queue: {len(queue)} | Batch limit: {limit}", flush=True)

    batch_items = queue[:limit]
    if not batch_items:
        print("Nothing left to migrate!", flush=True)
        return

    client = build_telegram_client(settings)
    await client.connect()
    assert await client.is_user_authorized(), "TG AI PERSON user_account.session is not authorized!"

    migrated_now = []
    try:
        for idx, (tid, topic_title) in enumerate(batch_items, 1):
            print(f"\n[{idx}/{len(batch_items)}] Processing Topic #{tid}: {topic_title}", flush=True)
            try:
                # 1. Inspect full topic content (all media/text, ascending chronological)
                fetched_all = await fetch_topic_messages_paginated(
                    client,
                    target=SOURCE_GROUP,
                    topic_id=tid,
                    filter_kind="all",
                    max_messages=500,
                    ascending=True,
                    max_wait_seconds=settings.max_flood_wait_seconds,
                )
                src_group_id = int(fetched_all["_entity"].id)
                raw_all = fetched_all["_raw_messages"]

                # Filter video messages
                raw_videos = [
                    m for m in raw_all
                    if getattr(m, "video", None)
                    or (
                        getattr(m, "document", None)
                        and str(getattr(m.document, "mime_type", "")).startswith("video/")
                    )
                ]
                if not raw_videos:
                    print(f"  SKIP Topic #{tid}: 0 video messages found", flush=True)
                    state["skipped"][str(tid)] = {"title": topic_title, "reason": "no_videos"}
                    save_state(state)
                    continue

                # 2. Forward all videos to STORAGE_DEST using TG AI PERSON's ForwardLedger engine!
                fwd_res = await forward_topic_batch_safe(
                    client,
                    guard,
                    settings,
                    source_group=SOURCE_GROUP,
                    source_topic=str(tid),
                    destination=STORAGE_DEST,
                    filter_kind="videos",
                    drop_author=True,
                    batch_size=15,
                    max_messages=500,
                    delay_seconds=3.5,
                    dry_run=False,
                    explicit_confirm=True,
                    skip_duplicates=True,
                    ledger=ledger,
                )
                status = fwd_res.get("status")
                print(
                    f"  Forward status={status} | forwarded={fwd_res.get('forwarded_count')} | skipped_dup={fwd_res.get('skipped_duplicates')}",
                    flush=True,
                )
                if status not in ("completed", "already_forwarded"):
                    err_msg = fwd_res.get("error") or f"Unexpected status {status}"
                    print(f"  STOP/PAUSE on Topic #{tid}: {err_msg}", flush=True)
                    state["errors"][str(tid)] = {"title": topic_title, "error": err_msg, "job_id": fwd_res.get("job_id")}
                    save_state(state)
                    if "flood" in err_msg.lower() or "wait" in err_msg.lower():
                        print("  FloodWait triggered — stopping wave cleanly to protect account!", flush=True)
                        break
                    continue

                # 3. Map source_message_id -> new_message_id from ForwardLedger
                dest_id_num = 4336427887
                fwd_map = lookup_forwarded_map(ledger_path, src_group_id, tid, dest_id_num)

                # Build episode list in chronological order
                matched_videos = [m for m in raw_videos if int(m.id) in fwd_map]
                if not matched_videos:
                    print(f"  ERR Topic #{tid}: forwarded but new_message_id map is empty!", flush=True)
                    state["errors"][str(tid)] = {"title": topic_title, "error": "empty_new_msg_map"}
                    save_state(state)
                    continue

                # Check if explicit episode numbers are unique across all matched videos
                parsed_nums = [extract_ep_num(getattr(m, "message", None) or "") for m in matched_videos]
                use_parsed = (
                    all(n is not None for n in parsed_nums)
                    and len(set(parsed_nums)) == len(parsed_nums)
                )

                ep_records: list[tuple[int, int, int, str]] = []
                for seq_idx, m in enumerate(matched_videos, 1):
                    ep_num = parsed_nums[seq_idx - 1] if use_parsed else seq_idx
                    new_mid = fwd_map[int(m.id)]
                    fsize, qual, _dur = get_video_info(m)
                    ep_records.append((int(ep_num), int(new_mid), int(fsize), qual))
                ep_records.sort(key=lambda x: x[0])

                # 4. Guess metadata + compute next code for poster filename
                meta = guess_metadata(topic_title, raw_all)
                with sqlite3.connect(DB_PATH) as conn:
                    next_code = 100 + int(conn.execute("SELECT COALESCE(MAX(id), 0) FROM doramas").fetchone()[0]) + 1
                poster_rel = await download_topic_poster(client, raw_all, next_code)

                # 5. Insert dorama + episodes into doramas.db
                new_id, new_code = insert_dorama_and_episodes(meta, poster_rel, ep_records)
                print(
                    f"  DB INSERTED: Code {new_code} (id={new_id}) '{meta['title']}' | {len(ep_records)} eps | msgs {ep_records[0][1]}..{ep_records[-1][1]} | poster={poster_rel or 'NONE'}",
                    flush=True,
                )

                rec = {
                    "code": new_code,
                    "id": new_id,
                    "title": meta["title"],
                    "episodes": len(ep_records),
                    "msg_range": f"{ep_records[0][1]}..{ep_records[-1][1]}",
                    "poster": poster_rel,
                    "status": meta["status"],
                }
                state["migrated"][str(tid)] = rec
                save_state(state)
                migrated_now.append(rec)

                # Anti-ban random jitter pause between dramas
                if idx < len(batch_items):
                    pause = round(random.uniform(4.5, 7.5), 2)
                    print(f"  Anti-ban pause: {pause}s...", flush=True)
                    await asyncio.sleep(pause)

            except Exception as exc:
                print(f"  EXCEPTION on Topic #{tid} ({topic_title}): {type(exc).__name__}: {exc}", flush=True)
                state["errors"][str(tid)] = {"title": topic_title, "error": f"{type(exc).__name__}: {exc}"}
                save_state(state)
                if "flood" in str(exc).lower():
                    print("  Flood exception — stopping wave cleanly!", flush=True)
                    break

        print(f"\n=== WAVE COMPLETE: {len(migrated_now)} dramas migrated ===", flush=True)
        for r in migrated_now:
            print(f"  Code {r['code']}: {r['title']} ({r['episodes']} eps, msgs {r['msg_range']}, {r['status']})")

        if send_update and migrated_now:
            # Optional: only send /update AFTER git push (caller handles git push first!)
            pass
    finally:
        await client.disconnect()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--send-update", action="store_true")
    args = ap.parse_args()
    asyncio.run(run_migration(args.limit, args.send_update))
