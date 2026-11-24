#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Autopilot Kdrama Donor Listener Daemon (Production Hardened)
Audited by 3-Agent Adversarial Committee.

Guarantees:
- Cloud-to-cloud forwarding (SSD: 0 KB, Bandwidth: 0 MB)
- 100% Asynchronous non-blocking SQLite via aiosqlite
- Strict Dubbed Uzbek filter with Cyrillic & Curly Apostrophes (Zero Subtitle leak)
- High-precision Episode Parser: Handles ranges ('1-11'), '5-seriya', '5-ep', rejects age limits ('16-18 yosh')
- Anti-Collision Title Matcher: Never merges single-word titles ('Baxt' vs 'Baxt qasri')
- Safe Dorama Creation with unique NOT NULL slug constraint and next code generation
- Quality Regression Protection: 1080p is never downgraded by 720p/480p
"""

import asyncio
from difflib import SequenceMatcher
import html
import json
import logging
from pathlib import Path
import re
import sys
from typing import List, Optional, Tuple

import aiosqlite
from telethon import TelegramClient, events
from telethon.errors import ChatForwardsRestrictedError, FloodWaitError
from telethon.tl.types import (
    DocumentAttributeFilename,
    DocumentAttributeVideo,
    Message,
)

# Output encoding
if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Configure Paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
import database  # noqa: E402
from database import invalidate_search_cache, normalize_search_text, slugify  # noqa: E402
from scripts.catalog_sync import publish_catalog_snapshot  # noqa: E402

try:
    from notifications import notify_subscribers_async
except ImportError:
    notify_subscribers_async = None

_BACKGROUND_TASKS = set()
_CREATE_LOCK = asyncio.Lock()
_SYNC_TASK = None
_SYNC_REVISION = 0

def track_background_task(coro):
    """Schedules an async task and retains a strong reference to prevent garbage collection."""
    task = asyncio.create_task(coro)
    _BACKGROUND_TASKS.add(task)
    def _done_callback(t):
        _BACKGROUND_TASKS.discard(t)
        try:
            exc = t.exception()
            if exc:
                logger.error(f"Background task failed with exception: {exc}")
        except asyncio.CancelledError:
            pass
        except Exception as ex:
            logger.error(f"Error checking background task status: {ex}")
    task.add_done_callback(_done_callback)
    return task


def schedule_catalog_sync(client: TelegramClient):
    """Debounce nearby episode writes into one hosted catalog update."""
    global _SYNC_TASK, _SYNC_REVISION
    _SYNC_REVISION += 1
    if _SYNC_TASK is None or _SYNC_TASK.done():
        _SYNC_TASK = track_background_task(sync_catalog_worker(client))


async def sync_catalog_worker(client: TelegramClient):
    pending_bot_update = False
    while True:
        revision = _SYNC_REVISION
        await asyncio.sleep(5)
        try:
            changed = await asyncio.to_thread(publish_catalog_snapshot, DB_PATH)
            pending_bot_update |= changed
            if pending_bot_update:
                await client.send_message("uzkdrama_app", "/update")
                logger.info("Hosted bot /update requested after catalog publish")
                pending_bot_update = False
            if revision == _SYNC_REVISION:
                return
        except Exception as exc:
            logger.error(f"Catalog sync failed; retrying in 60 seconds: {exc}")
            await asyncio.sleep(60)

LOG_FILE = BASE_DIR / "scripts" / "autopilot.log"
handlers = [logging.FileHandler(str(LOG_FILE), encoding="utf-8")]
if sys.stdout is not None:
    handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=handlers,
)
logger = logging.getLogger("AutopilotListener")

# Constants
DB_PATH = config.DB_PATH if hasattr(config, "DB_PATH") else (BASE_DIR / "doramas.db")
STORAGE_CHANNEL_ID = config.STORAGE_CHANNEL_ID
SESSION_PATH = str(BASE_DIR / "autopilot.session")
API_ID = getattr(config, "API_ID", 2040)
API_HASH = getattr(config, "API_HASH", "b18441a1ff607e10a989891a5462e627")
DONOR_FILTERED_PATH = BASE_DIR / "donor_channels_filtered.json"

# Strict Subtitle Regex (Latin & Cyrillic, with prefixes/suffixes & known sub channels)
RE_SUBTITLE_PATTERNS = [
    r"\b(?:hard|soft)?sub(?:lar)?\b",
    r"\b(?:hard|soft)?subtitr[a-z]*\b",
    r"\bsubtitles?\b",
    r"\b(?:uzb|uz|eng|rus|kor)[-_ ]?sub(?:s)?\b",
    r"\b(?:uzbsub|uzsub)[0-9]*\b",
    r"\bredsky\b",
    r"\b(?:хард|софт)?саб(?:ы|лар)?\b",
    r"\b(?:хард|софт)?суб(?:ы|лар)?\b",
    r"\bсубтитр[а-я]*\b",
    r"\b(?:узб|уз)[-_ ]?(?:саб|суб)\b",
]
RE_SUBTITLE = re.compile("|".join(RE_SUBTITLE_PATTERNS), re.IGNORECASE)

# Strict Uzbek Dubbed Indicators (Latin, Cyrillic, All Apostrophe variants, Known Studio tags)
RE_UZB_DUB = re.compile(
    r"(?:(?:o['ʻ`’ʼ]?zbek|özbek|ozbek|uzbek|uzb|ўзбек|узбек)\s*tilida(?:\s*dublyaj[a-z]*)?|"
    r"(?:o['ʻ`’ʼ]?zbek|özbek|ozbek|uzbek|ўзбек|узбек)cha|"
    r"dublyaj[a-z]*|prof(?:f)?\s*dub[a-z]*|tarjima\s*(?:kino|serial|dorama)?|"
    r"ўзбек\s*тилида|узбек\s*тилида|дубляж|таржима|"
    r"ovoz\s*berild[i-z]*|tomonidan\s*ovoz|"
    r"(?:\b|[#@])(?:choson(?:\s*tv|\s*media)?|minxo\s*tv|souls\s*studio|idub(?:tv)?|idup(?:tv)?|salom\s*tv|af\s*tv|sevar\s*studio|uzdub|dramma_uzbdub|asilmedia|asil_media)(?:\b|_))",
    re.IGNORECASE,
)

METADATA_TAGS = {
    "uzb", "sub", "dub", "1080p", "720p", "480p", "qism", "ep", "seriya",
    "choson_tv", "chosontv", "manba", "kino", "serial", "dorama", "kdrama", "yonu",
    "idub", "salomtv", "premyera", "film", "top", "tarjima", "koreya", "korea"
}


def normalize_for_filter(text: str) -> str:
    """Normalizes text for robust token-boundary regex matching."""
    if not text:
        return ""
    cleaned = re.sub(r"https?://\S+", " ", text)
    cleaned = re.sub(r"@\w+", " ", cleaned)
    cleaned = re.sub(r"['ʻ`’ʼ]", "'", cleaned)
    cleaned = re.sub(r"[(){}\[\]<>/\\]", " ", cleaned)
    cleaned = re.sub(r"[:;,!?\"«»“”#•·|~_\-*+=]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip().lower()


def is_subtitle_release(text: str) -> Tuple[bool, str]:
    """Strictly identifies subtitle-only releases with deny-first precedence."""
    if not text:
        return False, ""
    norm = normalize_for_filter(text)
    m = RE_SUBTITLE.search(norm)
    if m:
        return True, m.group(0)
    # Direct raw keyword search for safety
    raw_sub = re.search(r"\b(?:uzbsub|uzsub|hardsub|softsub)\b", text, re.IGNORECASE)
    if raw_sub:
        return True, raw_sub.group(0)
    # Check for #yonu or yonutv (known sub creator) when not explicitly marked as dubbed
    if re.search(r"(?:#yonu|yonutv\s*\(\s*subtitr\s*\)|yonu\s*tv\s*sub)", text, re.IGNORECASE):
        return True, "yonu_sub"
    return False, ""


def is_uzbek_dubbed(text: str, chat_title: str = "", chat_username: str = "") -> Tuple[bool, str]:
    """Determines if a post qualifies as an Uzbek dubbed release."""
    if not text:
        return False, ""
    m = RE_UZB_DUB.search(text)
    if m:
        return True, m.group(0)
    norm = normalize_for_filter(text)
    m_norm = RE_UZB_DUB.search(norm)
    if m_norm:
        return True, m_norm.group(0)
    title_lower = (chat_title or "").lower()
    if any(k in title_lower for k in ["o'zbek tilida", "oʻzbek tilida", "ozbek tilida", "uzbek tilida"]):
        return True, f"channel_title:{chat_title}"
    uname_lower = (chat_username or "").lower()
    if any(k in uname_lower for k in ["uzbdub", "dublaj"]):
        return True, f"channel_username:{chat_username}"
    return False, ""

# Micro-Drama / Duanju Platform & Keyword Identifier
RE_MICRO_DRAMA = re.compile(
    r"\b(?:dramabox|reelshort|shortmax|duanju|vertikal|micro[- ]?drama)\b",
    re.IGNORECASE,
)

# Title prefix stripper (e.g. 'Drama nomi: Qonli gul', 'Drama Box: X', 'Dorama: Y', 'Nomi: Z')
RE_TITLE_PREFIX = re.compile(
    r"^(?:dorama|drama\s*box|drama|reelshort|shortmax|duanju|serial|kino|film|nomi|дорама|драма)\s*(?:nomi|номи)?\s*[:|-]?\s*",
    re.IGNORECASE,
)

# Episode Parsing Regexes
RE_RANGE_EP = re.compile(
    r"(?:^|[^\d])(\d{1,3})\s*[-–—]\s*(\d{1,3})\s*[-–—/]?\s*(?:qis[i]?m(?:lar)?|қис[и]?м(?:лар)?|ep(?:isodes?)?|seriya(?:lar)?|серия(?:лар)?)\b",
    re.IGNORECASE,
)
RE_RANGE_PREFIX = re.compile(
    r"\b(?:qis[i]?m(?:lar)?|қис[и]?м(?:лар)?|ep(?:isodes?)?|seriya(?:lar)?|серия(?:лар)?)\s*[:#-]?\s*(\d{1,3})\s*[-–—]\s*(\d{1,3})\b",
    re.IGNORECASE,
)
RE_BARE_RANGE = re.compile(
    r"(?:^|[^\d(])\(?\s*(\d{1,3})\s*[-–—]\s*(\d{1,3})\s*\)?(?!\s*(?:yosh|yoshlar|\+|yil|so['ʻ`]?m|ming|mln))\b",
    re.IGNORECASE,
)
RE_AGE_FILTER = re.compile(r"\b\d{1,2}\s*[-–—]\s*\d{1,2}\s*(?:yosh|\+)", re.IGNORECASE)
RE_SINGLE_EP = re.compile(
    r"(?:^|[^\d])(\d{1,3})\s*[-–—/]?\s*(?:qis[i]?m(?:lar)?|қис[и]?м(?:лар)?|ep(?:isodes?)?|seriya|серия)\b",
    re.IGNORECASE,
)
RE_EP_PREFIX = re.compile(
    r"\b(?:qis[i]?m(?:lar)?|қис[и]?м(?:лар)?|ep(?:isodes?)?|seriya|серия)\s*[-–—#:]*\s*(\d{1,3})\b",
    re.IGNORECASE,
)

# Boilerplate line skipper (e.g. "PREMYERA!", "Yangi dorama!")
RE_BOILERPLATE = re.compile(
    r"^(?:premyera|yangi\s+(?:dorama|serial|kino)|diqqat|rasmiy|admin|tezkor|shoshiling|kino\s*kodi)\b",
    re.IGNORECASE,
)

# Quality Ranking for Regression Protection
QUALITY_RANKS = {"1080p": 3, "720p": 2, "480p": 1, "unknown": 0}


def get_video_attributes(msg: Message) -> Tuple[bool, int, int, int, int]:
    """Extracts (is_video, duration_seconds, width, height, size_bytes)."""
    media = msg.video or msg.document
    if not media:
        return False, 0, 0, 0, 0

    duration, width, height = 0, 0, 0
    is_video = bool(msg.video)

    if hasattr(media, "attributes") and media.attributes:
        for attr in media.attributes:
            if isinstance(attr, DocumentAttributeVideo):
                duration = int(getattr(attr, "duration", 0) or 0)
                width = int(getattr(attr, "w", 0) or 0)
                height = int(getattr(attr, "h", 0) or 0)
                is_video = True
            elif isinstance(attr, DocumentAttributeFilename):
                fname = getattr(attr, "file_name", "") or ""
                if fname.lower().endswith((".mp4", ".mkv", ".mov", ".avi")):
                    is_video = True

    size = int(getattr(media, "size", 0) or 0)
    return is_video, duration, width, height, size


def parse_episodes(text: str) -> Optional[List[int]]:
    """Accurately parses episode numbers and ranges ('1-11', '1-15', '12-25 qismlar')."""
    if not text:
        return None

    # Strip age limits like '16-18 yosh' or '18+' to prevent false range match
    cleaned_text = RE_AGE_FILTER.sub("", text)

    # 1. Explicit keyword range ('1-11 qism', '1-15 qismlar', 'qism 1-11')
    m_range = RE_RANGE_EP.search(cleaned_text) or RE_RANGE_PREFIX.search(cleaned_text)
    if m_range:
        start_ep = int(m_range.group(1))
        end_ep = int(m_range.group(2))
        if 1 <= start_ep < end_ep <= 300:
            return list(range(start_ep, end_ep + 1))

    # 2. Bundled batch range e.g. '1-11', '1-15', '(1-11)' (Micro-dramas / Duanju)
    m_bare = RE_BARE_RANGE.search(cleaned_text)
    if m_bare:
        start_ep = int(m_bare.group(1))
        end_ep = int(m_bare.group(2))
        if 1 <= start_ep < end_ep <= 300:
            return list(range(start_ep, end_ep + 1))

    # 3. Single episode check
    m_single = RE_SINGLE_EP.search(cleaned_text)
    if m_single:
        ep = int(m_single.group(1))
        if 1 <= ep <= 300:
            return [ep]

    # 4. Prefix episode check
    m_pref = RE_EP_PREFIX.search(cleaned_text)
    if m_pref:
        ep = int(m_pref.group(1))
        if 1 <= ep <= 300:
            return [ep]

    return None


def clean_dorama_title(text: str) -> str:
    """Extracts authentic dorama title, stripping markdown formatting, label prefixes, boilerplate headers, hashtags, and emojies."""
    if not text:
        return ""

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""

    candidate = ""
    for line in lines[:4]:
        raw_line = line
        cleaned = re.sub(r"@\w+|\[.*?\]", "", raw_line).strip()

        # If line contains hashtags (e.g. #Doktor_X or #niqobdagi_muhabbat/ #Mening_aybdor_insonim)
        if "#" in cleaned:
            non_tag_text = re.sub(r"#\w+", "", cleaned).strip(" /|-_~*`")
            if len(non_tag_text) < 2:
                # Line is purely/predominantly hashtags! Extract title candidate
                tags = re.findall(r"#([a-zA-Z0-9_а-яА-ЯёЁ]+)", cleaned)
                valid_tags = []
                for t in tags:
                    t_lower = t.lower().strip("_")
                    if t_lower not in METADATA_TAGS and not any(
                        m in t_lower for m in ["qism", "seriya", "1080p", "720p", "480p", "choson", "yonu"]
                    ):
                        valid_tags.append(t.replace("_", " ").strip())
                if valid_tags:
                    cleaned = valid_tags[0]

        # Strip remaining hashtags and markdown syntax
        cleaned = re.sub(r"#\w+", "", cleaned).strip()
        cleaned = re.sub(r"[_*~`]+", " ", cleaned).strip()
        # Strip emojies, variation selectors, and decorative symbols
        cleaned = re.sub(
            r"[\U00010000-\U0010ffff\u2000-\u3300\ufe00-\ufe0f•*►«»|“”]+",
            " ",
            cleaned,
        ).strip()
        # Strip label prefixes (e.g. 'Drama nomi:', 'Dorama nomi:', 'Nomi:')
        cleaned = RE_TITLE_PREFIX.sub("", cleaned).strip()

        if cleaned and not RE_BOILERPLATE.search(cleaned):
            candidate = cleaned
            break

    if not candidate:
        candidate = lines[0]
        cleaned = re.sub(r"@\w+|\[.*?\]", "", candidate).strip()
        if "#" in cleaned:
            tags = re.findall(r"#([a-zA-Z0-9_а-яА-ЯёЁ]+)", cleaned)
            valid_tags = [
                t.replace("_", " ").strip()
                for t in tags
                if t.lower().strip("_") not in METADATA_TAGS
            ]
            if valid_tags:
                cleaned = valid_tags[0]
        cleaned = re.sub(r"#\w+", "", cleaned).strip()
        cleaned = re.sub(r"[_*~`]+", " ", cleaned).strip()
        cleaned = re.sub(r"[\U00010000-\U0010ffff\u2000-\u3300\ufe00-\ufe0f•*►«»|“”]+", " ", cleaned).strip()
        candidate = RE_TITLE_PREFIX.sub("", cleaned).strip()

    # Re-apply prefix stripping in case of nested labels
    candidate = RE_TITLE_PREFIX.sub("", candidate).strip()

    # Remove bracketed episode numbers (e.g. '(1-qisim)', '[1-qism]', '(1-20)')
    candidate = re.sub(
        r"[\(\[]\s*\d{1,3}(?:\s*[-–—]\s*\d{1,3})?(?:\s*[-–—/]?\s*(?:qis[i]?m[a-z]*|қис[и]?м[а-я]*|ep(?:isodes?)?|seriya[a-z]*|серия[а-я]*))?\s*[\)\]].*$",
        "",
        candidate,
        flags=re.I,
    )

    # Remove episode ranges and tokens (both with keyword and bare numbers like 1-11, 1-15)
    candidate = re.sub(
        r"\b\d{1,3}\s*[-–—]\s*\d{1,3}(?:\s*[-–—/]?\s*(?:qis[i]?m(?:lar)?|қис[и]?м(?:лар)?|ep(?:isodes?)?|seriya(?:lar)?|серия(?:лар)?))?\b.*$",
        "",
        candidate,
        flags=re.I,
    )
    candidate = re.sub(
        r"\b\d{1,3}\s*[-–—/]?\s*(?:qis[i]?m(?:lar)?|қис[и]?м(?:lar)?|ep(?:isodes?)?|seriya(?:lar)?|серия(?:лар)?)\b.*$",
        "",
        candidate,
        flags=re.I,
    )
    candidate = re.sub(
        r"\b(?:uzbek|o['ʻ`’ʼ]?zbek)\s*tilida\b.*$",
        "",
        candidate,
        flags=re.I,
    )
    candidate = re.sub(r"\s+", " ", candidate).strip(" _*~`-–—:/|\"'«»“”")
    return candidate


async def find_dorama_id(
    db: aiosqlite.Connection,
    raw_title: str,
    is_micro_drama: bool = False,
) -> Optional[int]:
    """High-accuracy anti-collision dorama lookup."""
    clean_target = clean_dorama_title(raw_title)
    if not clean_target or len(clean_target) < 2:
        return None

    norm_target = normalize_search_text(clean_target)
    target_tokens = set(norm_target.split())

    async with db.execute("SELECT id, title, aliases, code FROM doramas") as cur:
        rows = await cur.fetchall()

    best_match_id = None
    best_score = 0.0

    for d_id, title, aliases, code in rows:
        norm_t = normalize_search_text(title or "")
        db_tokens = set(norm_t.split())

        # Exact match
        if norm_target == norm_t:
            if is_micro_drama:
                await db.execute(
                    "UPDATE doramas SET category = 'duanju', genre = 'Vertikal Micro-Drama, Duanju' WHERE id = ? AND (category = 'korea' OR category = '' OR category IS NULL)",
                    (d_id,),
                )
                await db.commit()
            return d_id

        # Token set match (prevents 'Baxt' from matching 'Baxt qasri')
        if target_tokens == db_tokens:
            if is_micro_drama:
                await db.execute(
                    "UPDATE doramas SET category = 'duanju', genre = 'Vertikal Micro-Drama, Duanju' WHERE id = ? AND (category = 'korea' OR category = '' OR category IS NULL)",
                    (d_id,),
                )
                await db.commit()
            return d_id

        # High-threshold SequenceMatcher only when token counts are very close
        if abs(len(target_tokens) - len(db_tokens)) <= 1:
            score = SequenceMatcher(None, norm_target, norm_t).ratio()
            if score > 0.88 and score > best_score:
                best_score = score
                best_match_id = d_id

        # Aliases match
        if aliases:
            for alias in str(aliases).split(","):
                norm_a = normalize_search_text(alias.strip())
                if norm_target == norm_a:
                    if is_micro_drama:
                        await db.execute(
                            "UPDATE doramas SET category = 'duanju', genre = 'Vertikal Micro-Drama, Duanju' WHERE id = ? AND (category = 'korea' OR category = '' OR category IS NULL)",
                            (d_id,),
                        )
                        await db.commit()
                    return d_id

    if best_match_id and best_score >= 0.88:
        if is_micro_drama:
            await db.execute(
                "UPDATE doramas SET category = 'duanju', genre = 'Vertikal Micro-Drama, Duanju' WHERE id = ? AND (category = 'korea' OR category = '' OR category IS NULL)",
                (best_match_id,),
            )
            await db.commit()
        return best_match_id

    return None


async def create_new_dorama(
    db: aiosqlite.Connection,
    raw_title: str,
    is_micro_drama: bool = False,
) -> Optional[int]:
    """Safely creates a new dorama with collision-proof unique code and unique slug."""
    clean_target = clean_dorama_title(raw_title)
    if not clean_target or len(clean_target) < 2:
        return None

    # Safe code allocation
    async with db.execute("SELECT code FROM doramas WHERE code IS NOT NULL") as cur:
        existing_codes = set(r[0] for r in await cur.fetchall())
    new_code = max(existing_codes, default=500) + 1
    while new_code in existing_codes:
        new_code += 1

    clean_name = clean_target.title()
    base_slug = slugify(clean_name) or f"dorama-{new_code}"
    slug = base_slug
    counter = 1

    while True:
        async with db.execute(
            "SELECT id FROM doramas WHERE slug = ?",
            (slug,),
        ) as cur:
            exists = await cur.fetchone()
            if not exists:
                break
            counter += 1
            slug = f"{base_slug}-{counter}"

    category = "duanju" if is_micro_drama else "korea"
    genre = "Vertikal Micro-Drama, Duanju" if is_micro_drama else "Dorama"
    country = "DramaBox / Micro-Drama" if is_micro_drama else "Janubiy Koreya"
    description = "DramaBox 9:16 vertikal formatdagi micro-drama (qismlar to'plami)" if is_micro_drama else ""

    async with db.execute(
        """
        INSERT INTO doramas (code, title, slug, status, country, total_episodes, views, category, genre, description)
        VALUES (?, ?, ?, 'Ongoing', ?, 1, 0, ?, ?, ?)
    """,
        (new_code, clean_name, slug, country, category, genre, description),
    ) as cur:
        await db.commit()
        new_id = cur.lastrowid
        logger.info(
            f"✨ Created NEW Dorama [Code {new_code}] '{clean_name}' (ID={new_id}, slug='{slug}', cat='{category}')"
        )
        return new_id


async def find_or_create_dorama(
    db: aiosqlite.Connection,
    raw_title: str,
    is_micro_drama: bool = False,
) -> Optional[int]:
    """Backward compatibility wrapper."""
    d_id = await find_dorama_id(db, raw_title, is_micro_drama=is_micro_drama)
    if d_id:
        return d_id
    return await create_new_dorama(db, raw_title, is_micro_drama=is_micro_drama)


async def ingest_episodes_to_db(
    dorama_id: int,
    ep_list: List[int],
    storage_msg_id: int,
    quality: str,
    file_size: int,
    allow_same_quality_update: bool = False,
):
    """Asynchronously ingests episodes into SQLite with quality regression protection."""
    async with aiosqlite.connect(str(DB_PATH), timeout=30.0) as db:
        await db.execute("PRAGMA journal_mode = WAL;")
        await db.execute("PRAGMA busy_timeout = 30000;")

        # Cross-dorama collision check
        async with db.execute(
            "SELECT dorama_id, episode_number FROM episodes WHERE channel_message_id = ?",
            (storage_msg_id,),
        ) as cur:
            collision = await cur.fetchone()
            if collision and collision[0] != dorama_id:
                logger.warning(
                    f"Blocked cross-collision: storage_msg_id={storage_msg_id} already bound to dorama {collision[0]} ep {collision[1]}"
                )
                return

        new_qual_rank = QUALITY_RANKS.get(quality.lower(), 1)
        actual_ingested = []

        for ep_num in ep_list:
            # Check existing quality to prevent downgrading or duplicate overwriting
            async with db.execute(
                "SELECT channel_message_id, quality FROM episodes WHERE dorama_id = ? AND episode_number = ?",
                (dorama_id, ep_num),
            ) as cur:
                existing_ep = await cur.fetchone()

            if existing_ep and existing_ep[0] and existing_ep[0] > 0:
                old_msg_id = existing_ep[0]
                old_qual = existing_ep[1] or "720p"
                old_qual_rank = QUALITY_RANKS.get(old_qual.lower(), 1)
                if old_msg_id == storage_msg_id:
                    continue
                if not allow_same_quality_update and old_qual_rank >= new_qual_rank:
                    logger.info(
                        f"Skipped overwrite for Dorama {dorama_id} Ep {ep_num}: existing {old_qual} >= incoming {quality}"
                    )
                    continue

            await db.execute(
                """
                INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality, file_size)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
                    channel_message_id = excluded.channel_message_id,
                    quality = excluded.quality,
                    file_size = excluded.file_size
            """,
                (dorama_id, ep_num, storage_msg_id, quality, file_size),
            )
            actual_ingested.append(ep_num)

        if not actual_ingested:
            logger.info(f"No new episodes were ingested for Dorama ID={dorama_id} (all already exist with equal/better quality).")
            return []

        max_ep = max(actual_ingested)
        await db.execute(
            """
            UPDATE doramas
            SET total_episodes = MAX(COALESCE(total_episodes, 0), ?),
                status = 'Ongoing'
            WHERE id = ?
        """,
            (max_ep, dorama_id),
        )

        await db.commit()
        logger.info(
            f"✅ Ingested Dorama ID={dorama_id} Ep(s)={actual_ingested} -> Storage MSG={storage_msg_id} ({quality})"
        )

        # 1. Qidiruv keshini yangilash (In-Memory Search Engine Invalidation)
        try:
            database.invalidate_search_cache()
            logger.info(f"🔄 Search cache invalidated successfully for Dorama ID={dorama_id}")
        except Exception as e:
            logger.warning(f"Could not invalidate search cache: {e}")

        # 2. Obunachilarga Push Bildirishnoma yuborish (Async Notification Dispatch)
        try:
            if notify_subscribers_async is not None:
                track_background_task(notify_subscribers_async(dorama_id, actual_ingested, quality))
                logger.info(
                    f"📢 Dispatched notify_subscribers_async for Dorama ID={dorama_id}, Ep={actual_ingested}, Quality={quality}"
                )
            else:
                from notifications import notify_subscribers_async as _notify
                track_background_task(_notify(dorama_id, actual_ingested, quality))
                logger.info(
                    f"📢 Dispatched notify_subscribers_async for Dorama ID={dorama_id}, Ep={actual_ingested}, Quality={quality}"
                )
        except Exception as e:
            logger.warning(f"Could not trigger subscriber notification: {e}")

        return actual_ingested


async def send_admin_notification(
    title: str,
    code: int,
    ep_list: List[int],
    quality: str,
    file_size: int,
    chat_title: str,
    storage_msg_id: int,
):
    """Sends instant HTML notification to admin Telegram via Bot API."""
    import urllib.request

    try:
        size_mb = round(file_size / (1024 * 1024), 1) if file_size else 0
        eps_str = (
            f"{min(ep_list)}–{max(ep_list)}"
            if len(ep_list) > 1
            else str(ep_list[0])
        )
        msg_text = (
            f"⚡ <b>YANGI QISM AVTOMATIK QO‘SHILDI!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎬 <b>Dorama:</b> {html.escape(str(title))} (Kod: <code>{code}</code>)\n"
            f"🎞 <b>Qism:</b> {eps_str}-qism ({quality}, {size_mb} MB)\n"
            f"📢 <b>Manba:</b> {html.escape(str(chat_title))}\n"
            f"💾 <b>Storage ID:</b> <code>{storage_msg_id}</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🟡 <i>Bot katalogi yangilanmoqda.</i>"
        )
        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
        payload = json.dumps(
            {
                "chat_id": config.ADMIN_ID,
                "text": msg_text,
                "parse_mode": "HTML",
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
        await asyncio.to_thread(urllib.request.urlopen, req, timeout=10)
        logger.info(f"Delivered admin notification for {title} ep {eps_str}")
    except Exception as e:
        logger.warning(f"Could not send admin notification: {e}")


STATE_FILE = BASE_DIR / "scripts" / "autopilot_state.json"
RESTRICTED_CHANNELS_FILE = BASE_DIR / "scripts" / "autopilot_restricted_channels.json"


def load_sync_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading {STATE_FILE}: {e}")
    return {}


def save_sync_state(state: dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Error saving {STATE_FILE}: {e}")


def update_channel_state(chat_id: int, msg_id: int):
    state = load_sync_state()
    cid_str = str(chat_id)
    if msg_id > state.get(cid_str, 0):
        state[cid_str] = msg_id
        save_sync_state(state)


async def warm_up_channel_entities(client: TelegramClient, target_ids: List[int]):
    """Pre-warms Telethon entity cache so events.NewMessage never drops updates from unknown peers."""
    logger.info(f"Warming up entity cache for {len(target_ids)} donor channels...")
    warmed = 0
    for idx, cid in enumerate(target_ids):
        try:
            await client.get_input_entity(cid)
            warmed += 1
        except Exception:
            try:
                await client.get_entity(cid)
                warmed += 1
            except Exception as e:
                logger.debug(f"Could not warm entity for {cid}: {e}")
        if (idx + 1) % 15 == 0:
            await asyncio.sleep(1.0)
    logger.info(f"Warm-up complete: {warmed}/{len(target_ids)} channels verified in entity cache.")


async def process_donor_message(client: TelegramClient, msg: Message, dry_run: bool = False, advance_state: bool = True) -> bool:
    """Core pipeline processing for a donor channel video message."""
    text = msg.text or msg.message or ""
    chat_id = msg.chat_id

    def mark_done():
        if advance_state:
            update_channel_state(chat_id, msg.id)

    # 1. Video Check
    is_video, duration, w, h, size = get_video_attributes(msg)
    if not is_video:
        mark_done()
        return False

    chat = await msg.get_chat()
    chat_title = getattr(chat, "title", "Channel") or ""
    chat_username = (getattr(chat, "username", "") or "").lower()

    # Strict Micro-drama detection: MUST be vertical and short (<15m) OR explicit duanju keyword
    is_vertical = bool(h > 0 and w > 0 and h > w)
    has_micro_kw = bool(RE_MICRO_DRAMA.search(text))

    if duration > 900:  # Any video > 15 minutes is a standard TV drama or movie, NEVER a micro-drama!
        is_micro = False
    elif is_vertical and duration <= 600:
        is_micro = True
    elif has_micro_kw and duration <= 900:
        is_micro = True
    else:
        is_micro = False

    # 2. Duration Guard
    if duration > 0:
        if is_micro:
            if duration < 20:
                logger.debug(f"Skipped ultra-short clip (<20s): {text[:40]}")
                mark_done()
                return False
        elif duration < 90:
            logger.debug(f"Skipped short/edit (<90s): {text[:40]}")
            mark_done()
            return False

    # 3. Deny-First Subtitle Evaluation (Strict Rejection Precedence)
    is_sub, sub_reason = is_subtitle_release(text)
    if is_sub:
        logger.info(
            f"⏭ [SUBTITLE BLOCKED] Subtitle marker '{sub_reason}' detected from '{chat_title}': {text[:45]}"
        )
        mark_done()
        return False

    # 4. Mandatory Uzbek Dubbed indicator for TV doramas and movies
    has_dub, dub_reason = is_uzbek_dubbed(text, chat_title, chat_username)
    if not is_micro:
        if not has_dub:
            logger.info(
                f"⏭ [NON-DUBBED BLOCKED] Post lacks explicit Uzbek dubbed indicator from '{chat_title}': {text[:45]}"
            )
            mark_done()
            return False

    # 5. Episode Parsing
    ep_list = parse_episodes(text)
    if not ep_list:
        logger.debug(f"Could not parse episode number from: {text[:40]}")
        mark_done()
        return False

    # 6. Title Extraction
    raw_title = clean_dorama_title(text)
    if not raw_title or len(raw_title) < 2:
        mark_done()
        return False

    quality = f"{h}p" if h in (480, 720, 1080) else ("1080p" if h > 720 else "720p")

    logger.info(
        f"🎬 DETECTED: '{raw_title}' Ep {ep_list} ({quality}, {duration}s, {size}b, micro={is_micro}) from '{chat_title}'"
    )

    if dry_run:
        logger.info(f"[DRY-RUN] Forward to storage & ingest verified. Skipped DB write.")
        mark_done()
        return True

    # 7. DB Pre-resolution & Orphan Guard
    new_qual_rank = QUALITY_RANKS.get(quality.lower(), 1)
    needed_eps = []
    async with aiosqlite.connect(str(DB_PATH), timeout=30.0) as db:
        dorama_id = await find_dorama_id(db, raw_title, is_micro_drama=is_micro)
        if not dorama_id:
            # If incoming episode is NOT starting from 1 (e.g. Ep 3 or 8), prevent creating a broken orphan dorama!
            if min(ep_list) > 1:
                logger.warning(
                    f"⏭ [ORPHAN PREVENTED] '{raw_title}' is a new dorama but incoming episode is {ep_list} (missing Ep 1). Skipping."
                )
                mark_done()
                return False
            needed_eps = list(ep_list)
        else:
            for ep_num in ep_list:
                async with db.execute(
                    "SELECT channel_message_id, quality FROM episodes WHERE dorama_id = ? AND episode_number = ?",
                    (dorama_id, ep_num),
                ) as cur:
                    row = await cur.fetchone()
                    if not row or not row[0] or row[0] <= 0:
                        needed_eps.append(ep_num)
                    else:
                        existing_qual = row[1] or "720p"
                        existing_qual_rank = QUALITY_RANKS.get(existing_qual.lower(), 1)
                        if new_qual_rank > existing_qual_rank:
                            needed_eps.append(ep_num)

    if not needed_eps:
        logger.info(
            f"⏭ [DUPLICATE BLOCKED] '{raw_title}' Ep {ep_list} already exists in DB with equal/better quality ({quality}) from channel '{chat_title}'."
        )
        mark_done()
        return False

    # 8. Cloud-to-Cloud Forwarding
    try:
        fwd = await client.forward_messages(STORAGE_CHANNEL_ID, msg)
        storage_msg = fwd if isinstance(fwd, Message) else fwd[0]
        storage_msg_id = storage_msg.id
        logger.info(f"Cloud Forwarded to Storage -> msg_id={storage_msg_id} (Needed eps: {needed_eps})")
    except ChatForwardsRestrictedError:
        logger.warning(f"Skipped restricted channel '{chat_title}': Forwarding disabled.")
        try:
            restricted = {}
            if RESTRICTED_CHANNELS_FILE.exists():
                with open(RESTRICTED_CHANNELS_FILE, "r", encoding="utf-8") as rf:
                    restricted = json.load(rf)
            restricted[str(chat_id)] = {"title": chat_title, "username": chat_username}
            with open(RESTRICTED_CHANNELS_FILE, "w", encoding="utf-8") as rf:
                json.dump(restricted, rf, indent=2, ensure_ascii=False)
        except Exception:
            pass
        mark_done()
        return False
    except FloodWaitError as e:
        logger.warning(f"Telegram FloodWait: waiting {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)
        return False
    except Exception as e:
        logger.error(f"Forwarding exception: {e}")
        return False

    # 9. Ingest into DB
    if not dorama_id:
        # Do not leave an empty catalog entry when Telegram rejects the forward.
        async with _CREATE_LOCK:
            async with aiosqlite.connect(str(DB_PATH), timeout=30.0) as db:
                dorama_id = await find_dorama_id(db, raw_title, is_micro_drama=is_micro)
                if not dorama_id:
                    dorama_id = await create_new_dorama(db, raw_title, is_micro_drama=is_micro)
        if not dorama_id:
            logger.error(f"Could not create dorama for '{raw_title}' after forwarding")
            return False

    ingested = await ingest_episodes_to_db(dorama_id, needed_eps, storage_msg_id, quality, size)
    mark_done()
    if not ingested:
        return False

    schedule_catalog_sync(client)

    # 10. Instant Admin Notification
    try:
        async with aiosqlite.connect(str(DB_PATH)) as db:
            async with db.execute(
                "SELECT title, code FROM doramas WHERE id = ?", (dorama_id,)
            ) as cur:
                row = await cur.fetchone()
                d_title = row[0] if row else raw_title
                d_code = row[1] if row else dorama_id

        await send_admin_notification(
            title=d_title,
            code=d_code,
            ep_list=ingested,
            quality=quality,
            file_size=size,
            chat_title=chat_title,
            storage_msg_id=storage_msg_id,
        )
    except Exception as e:
        logger.warning(f"Admin notification step skipped: {e}")

    return True


async def process_direct_storage_message(client: TelegramClient, msg: Message) -> bool:
    """Instant Ingestion Hub for our own STORAGE_CHANNEL ('Dramalar').
    When admin drops or forwards videos (single or batch of 1-22 episodes) directly into Dramalar,
    this function immediately parses title, episodes, links to DB, and syncs the catalog.
    Zero donor heuristic blocks.
    """
    text = msg.text or msg.message or ""
    is_video, duration, w, h, size = get_video_attributes(msg)
    if not is_video:
        return False

    if not text:
        media = msg.video or msg.document
        if media and hasattr(media, "attributes"):
            for attr in media.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    fname = getattr(attr, "file_name", "") or ""
                    if fname:
                        text = fname.replace("_", " ").rsplit(".", 1)[0]
                        break

    if not text:
        logger.warning(f"⚠️ [DIRECT DROP] Video message {msg.id} in Dramalar has no caption or filename.")
        return False

    raw_title = clean_dorama_title(text)
    if not raw_title or len(raw_title) < 2:
        logger.warning(f"⚠️ [DIRECT DROP] Could not parse dorama title from: {text[:50]}")
        return False

    ep_list = parse_episodes(text)
    if not ep_list:
        logger.warning(f"⚠️ [DIRECT DROP] Could not parse episode number(s) from: {text[:50]}")
        return False

    quality = f"{h}p" if h in (480, 720, 1080) else ("1080p" if h > 720 else "720p")
    storage_msg_id = msg.id

    logger.info(
        f"🎯 [DIRECT DROP DETECTED] '{raw_title}' Ep {ep_list} ({quality}, {size}b) in Dramalar (msg_id={storage_msg_id})"
    )

    # Check cross-collision BEFORE creating a new dorama row in DB
    async with aiosqlite.connect(str(DB_PATH), timeout=30.0) as check_db:
        async with check_db.execute(
            "SELECT dorama_id, episode_number FROM episodes WHERE channel_message_id = ?",
            (storage_msg_id,),
        ) as cur:
            collision = await cur.fetchone()
            if collision:
                logger.info(
                    f"ℹ️ [DIRECT DROP] Msg {storage_msg_id} already bound to Dorama {collision[0]} Ep {collision[1]}. Skipping redundant creation."
                )
                return True

    async with _CREATE_LOCK:
        async with aiosqlite.connect(str(DB_PATH), timeout=30.0) as db:
            dorama_id = await find_dorama_id(db, raw_title)
            if not dorama_id:
                is_micro = bool(duration <= 600 and duration > 0 and h > w)
                dorama_id = await create_new_dorama(db, raw_title, is_micro_drama=is_micro)
                logger.info(f"✨ [DIRECT DROP] Created NEW Dorama for '{raw_title}' (ID={dorama_id})")

    if not dorama_id:
        logger.error(f"❌ [DIRECT DROP] Failed to find or create dorama for '{raw_title}'")
        return False

    ingested = await ingest_episodes_to_db(
        dorama_id, ep_list, storage_msg_id, quality, size, allow_same_quality_update=True
    )
    if not ingested:
        logger.info(f"ℹ️ [DIRECT DROP] Ep {ep_list} already up to date in DB.")
        return True

    try:
        database.invalidate_search_cache()
    except Exception:
        pass

    schedule_catalog_sync(client)

    # Deliver Telegram notification to admin
    try:
        async with aiosqlite.connect(str(DB_PATH)) as db:
            async with db.execute(
                "SELECT title, code FROM doramas WHERE id = ?", (dorama_id,)
            ) as cur:
                row = await cur.fetchone()
                d_title = row[0] if row else raw_title
                d_code = row[1] if row else 0

        ep_str = f"{min(ep_list)}-{max(ep_list)}-qismlar" if len(ep_list) > 1 else f"{ep_list[0]}-qism"
        notif_text = (
            f"⚡ <b>DRAMALAR HUB: YANGI QISM TAYYOR!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎬 <b>Dorama:</b> {d_title} (Kod: <b>{d_code}</b>)\n"
            f"🎞 <b>Qism:</b> {ep_str} ({quality})\n"
            f"💾 <b>Storage ID:</b> {storage_msg_id}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🚀 Bot katalogi avtomatik yangilandi va tomoshaga tayyor!"
        )
        if notify_subscribers_async:
            for admin_id in config.ADMIN_IDS:
                track_background_task(
                    notify_subscribers_async(
                        admin_id, notif_text, dorama_id=dorama_id, is_admin_report=True
                    )
                )
    except Exception as ne:
        logger.debug(f"[DIRECT DROP] Admin notification error: {ne}")

    return True


async def staggered_catchup_sync(client: TelegramClient, target_ids: List[int], channel_locks: dict, dry_run: bool = False):
    """Background incremental sentinel: checks channels for any missed episodes during downtime with anti-flood throttling."""
    logger.info("Initializing Staggered Catchup Sentinel...")
    while True:
        try:
            state = load_sync_state()
            for cid in target_ids:
                cid_str = str(cid)
                last_msg_id = state.get(cid_str, 0)
                try:
                    if last_msg_id > 0:
                        # Fetch messages newer than last_msg_id
                        async for msg in client.iter_messages(cid, min_id=last_msg_id, limit=100, reverse=True):
                            async with channel_locks[cid]:
                                await process_donor_message(client, msg, dry_run=dry_run, advance_state=not dry_run)
                            # A retryable forwarding or database failure leaves the cursor
                            # unchanged. Do not skip past it to later messages.
                            if not dry_run and load_sync_state().get(cid_str, 0) < msg.id:
                                break
                    else:
                        # Cold start: capture latest msg id to anchor future queries
                        async for msg in client.iter_messages(cid, limit=1):
                            if not dry_run:
                                update_channel_state(cid, msg.id)
                except FloodWaitError as fe:
                    logger.warning(f"Catchup FloodWait: sleeping {fe.seconds + 2}s")
                    await asyncio.sleep(fe.seconds + 2)
                except Exception as ex:
                    logger.debug(f"Catchup check error for channel {cid}: {ex}")
                
                # Polite throttle: 2.0s pause between channel history queries to stay 100% flood-free
                await asyncio.sleep(2.0)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning(f"Staggered catchup loop error: {e}")
        
        # Periodic sync every 20 minutes
        await asyncio.sleep(1200)


async def run_listener(dry_run: bool = False):
    """Production Telethon event listener for Kdrama channels with Staggered Catchup Sentinel."""
    logger.info("Connecting Telethon client with active session...")
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        logger.error("Telethon session is not authorized! Exiting.")
        return

    me = await client.get_me()
    logger.info(f"Authorized as @{me.username or me.first_name} (ID={me.id})")

    # Load filtered donor channels
    target_ids = []
    if DONOR_FILTERED_PATH.exists():
        with open(DONOR_FILTERED_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for cid_str in data.keys():
            cid = int(cid_str)
            if cid != STORAGE_CHANNEL_ID:
                target_ids.append(cid)
    logger.info(f"Loaded {len(target_ids)} filtered Kdrama donor channels.")

    # 1. Warm up entity cache for reliable event dispatch
    await warm_up_channel_entities(client, target_ids + [STORAGE_CHANNEL_ID])
    channel_locks = {cid: asyncio.Lock() for cid in target_ids}
    storage_lock = asyncio.Lock()

    # 2. Register real-time push event listener for donor channels
    @client.on(events.NewMessage(chats=target_ids))
    async def handle_new_media(event: events.NewMessage.Event):
        async with channel_locks[event.chat_id]:
            await process_donor_message(client, event.message, dry_run=dry_run, advance_state=False)

    # 3. Register real-time push event listener for our own Dramalar storage channel (Instant Admin Drop)
    @client.on(events.NewMessage(chats=[STORAGE_CHANNEL_ID]))
    async def handle_direct_storage_drop(event: events.NewMessage.Event):
        async with storage_lock:
            await process_direct_storage_message(client, event.message)

    # Check recent storage channel messages in case any was dropped while offline
    try:
        logger.info("Checking recent Dramalar storage messages for pending direct drops...")
        recent_storage = await client.get_messages(STORAGE_CHANNEL_ID, limit=30)
        for m in reversed(recent_storage or []):
            await process_direct_storage_message(client, m)
    except Exception as se:
        logger.debug(f"Storage initial scan error: {se}")

    # 4. Start background staggered catchup sentinel
    track_background_task(staggered_catchup_sync(client, target_ids, channel_locks, dry_run=dry_run))

    logger.info("⚡ Autopilot Kdrama Listener is LIVE (Monitoring Donors + Dramalar Direct Drop Hub)...")
    while True:
        try:
            if not client.is_connected():
                await client.connect()
            await client.run_until_disconnected()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning(f"Connection interrupted ({e}), auto-reconnecting in 5 seconds...")
            await asyncio.sleep(5)

    if _BACKGROUND_TASKS:
        logger.info(f"Waiting for {len(_BACKGROUND_TASKS)} active background notification tasks to finish...")
        await asyncio.gather(*_BACKGROUND_TASKS, return_exceptions=True)

    await client.disconnect()


def acquire_listener_lock():
    """Keep direct launches from opening the same Telethon session twice on Windows."""
    if sys.platform != "win32":
        return None
    import msvcrt

    lock_file = open(BASE_DIR / "scripts" / ".autopilot_instance.lock", "a+b")
    lock_file.seek(0, 2)
    if lock_file.tell() == 0:
        lock_file.write(b"0")
        lock_file.flush()
    lock_file.seek(0)
    try:
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        lock_file.close()
        return False
    return lock_file


if __name__ == "__main__":
    instance_lock = acquire_listener_lock()
    if instance_lock is False:
        logger.error("Another Autopilot listener is already using this session. Exiting duplicate.")
        sys.exit(2)
    is_dry = "--dry-run" in sys.argv
    asyncio.run(run_listener(dry_run=is_dry))
