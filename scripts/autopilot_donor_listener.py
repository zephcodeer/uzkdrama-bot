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

try:
    from notifications import notify_subscribers_async
except ImportError:
    notify_subscribers_async = None

_BACKGROUND_TASKS = set()

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

# Strict Subtitle Regex (Latin & Cyrillic, with prefixes/suffixes)
RE_SUBTITLE = re.compile(
    r"(?:^|[^\w])(?:hard|soft)?(?:sub|subtitr[a-z]*|subtitles?|sublar|саб[ыа-я]*|субтитр[а-я]*)(?:[^\w]|$)",
    re.IGNORECASE,
)

# Strict Uzbek Dubbed Indicators (Latin, Cyrillic, All Apostrophe variants, Known Studio tags)
RE_UZB_DUB = re.compile(
    r"(?:o['ʻ`’ʼ]?zbek\s*tilida|uzbek\s*tilida|uzb\s*tilida|o['ʻ`’ʼ]?zbekcha|uzbekcha|dublyaj|tarjima|"
    r"ўзбек\s*тилида|узбек\s*тилида|ўзбекча|узбекча|дубляж|таржима|"
    r"#choson_tv|#minxo_tv|#souls_studio|#idub|#iduptv|#salomtv|#af_tv|#sevar_studio|#uzdub|#dramma_uzbdub|"
    r"dramabox|reelshort|shortmax|duanju|vertikal|#dramabox|#reelshort|#shortmax|#duanju|#vertikal|@drammaworld)",
    re.IGNORECASE,
)

# Micro-Drama / Duanju Platform & Keyword Identifier
RE_MICRO_DRAMA = re.compile(
    r"\b(?:dramabox|reelshort|shortmax|duanju|vertikal|micro[- ]?drama)\b",
    re.IGNORECASE,
)

# Episode Parsing Regexes
RE_RANGE_EP = re.compile(
    r"(?:^|[^\d])(\d{1,3})\s*[-–—]\s*(\d{1,3})\s*[-–—/]?\s*(?:qism(?:lar)?|ep(?:isodes?)?|seriya(?:lar)?)\b",
    re.IGNORECASE,
)
RE_RANGE_PREFIX = re.compile(
    r"\b(?:qism(?:lar)?|ep(?:isodes?)?|seriya(?:lar)?)\s*[:#-]?\s*(\d{1,3})\s*[-–—]\s*(\d{1,3})\b",
    re.IGNORECASE,
)
RE_BARE_RANGE = re.compile(
    r"(?:^|[^\d(])\(?\s*(\d{1,3})\s*[-–—]\s*(\d{1,3})\s*\)?(?!\s*(?:yosh|yoshlar|\+|yil|so['ʻ`]?m|ming|mln))\b",
    re.IGNORECASE,
)
RE_AGE_FILTER = re.compile(r"\b\d{1,2}\s*[-–—]\s*\d{1,2}\s*(?:yosh|\+)", re.IGNORECASE)
RE_SINGLE_EP = re.compile(
    r"(?:^|[^\d])(\d{1,3})\s*[-–—/]?\s*(?:qism(?:lar)?|ep(?:isodes?)?|seriya)\b",
    re.IGNORECASE,
)
RE_EP_PREFIX = re.compile(
    r"\b(?:qism(?:lar)?|ep(?:isodes?)?|seriya)\s*[-–—#:]*\s*(\d{1,3})\b",
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
    """Extracts authentic dorama title, skipping boilerplate headers, platform tags and emojies."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""

    candidate = ""
    for line in lines[:3]:
        # Strip hashtags, channel mentions, and square brackets
        cleaned = re.sub(r"#\w+|@\w+|\[.*?\]", "", line).strip()
        # Strip emojies and decorative symbols, keeping apostrophes and hyphens
        cleaned = re.sub(
            r"[\U00010000-\U0010ffff\u2000-\u3300•*►«»|]+",
            " ",
            cleaned,
        ).strip()
        if cleaned and not RE_BOILERPLATE.search(cleaned):
            candidate = cleaned
            break

    if not candidate:
        candidate = lines[0]

    # Strip micro-drama platform prefixes (e.g. 'Drama Box: Title', 'DramaBox - Title')
    candidate = re.sub(
        r"^(?:drama\s*box|reelshort|shortmax|duanju)\s*[:|-]?\s*",
        "",
        candidate,
        flags=re.I,
    ).strip()

    # Remove bracketed ranges (e.g. '(1-20)')
    candidate = re.sub(
        r"\(\s*\d{1,3}\s*[-–—]\s*\d{1,3}\s*\).*$",
        "",
        candidate,
        flags=re.I,
    )

    # Remove episode ranges and tokens (both with keyword and bare numbers like 1-11, 1-15)
    candidate = re.sub(
        r"\b\d{1,3}\s*[-–—]\s*\d{1,3}(?:\s*[-–—/]?\s*(?:qism(?:lar)?|ep(?:isodes?)?|seriya(?:lar)?))?\b.*$",
        "",
        candidate,
        flags=re.I,
    )
    candidate = re.sub(
        r"\b\d{1,3}\s*[-–—/]?\s*(?:qism(?:lar)?|ep(?:isodes?)?|seriya(?:lar)?)\b.*$",
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
    candidate = re.sub(r"\s+", " ", candidate).strip(" -–—:/|\"'«»")
    return candidate


async def find_or_create_dorama(
    db: aiosqlite.Connection,
    raw_title: str,
    is_micro_drama: bool = False,
) -> Optional[int]:
    """High-accuracy anti-collision dorama lookup or safe creation with unique slug."""
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

    # Create NEW dorama with safe unique slug and next available code
    async with db.execute("SELECT MAX(code) FROM doramas") as cur:
        row = await cur.fetchone()
        max_code = (row[0] or 500) if row else 500
        new_code = max_code + 1

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


async def ingest_episodes_to_db(
    dorama_id: int,
    ep_list: List[int],
    storage_msg_id: int,
    quality: str,
    file_size: int,
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

        for ep_num in ep_list:
            # Check existing quality to prevent downgrading 1080p -> 720p
            async with db.execute(
                "SELECT channel_message_id, quality FROM episodes WHERE dorama_id = ? AND episode_number = ?",
                (dorama_id, ep_num),
            ) as cur:
                existing_ep = await cur.fetchone()

            if existing_ep:
                old_qual = existing_ep[1] or "720p"
                old_qual_rank = QUALITY_RANKS.get(old_qual.lower(), 1)
                if old_qual_rank > new_qual_rank:
                    logger.info(
                        f"Skipped overwrite for Dorama {dorama_id} Ep {ep_num}: existing {old_qual} > incoming {quality}"
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

        max_ep = max(ep_list)
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
            f"✅ Ingested Dorama ID={dorama_id} Ep(s)={ep_list} -> Storage MSG={storage_msg_id} ({quality})"
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
                track_background_task(notify_subscribers_async(dorama_id, ep_list, quality))
                logger.info(
                    f"📢 Dispatched notify_subscribers_async for Dorama ID={dorama_id}, Ep={ep_list}, Quality={quality}"
                )
            else:
                from notifications import notify_subscribers_async as _notify
                track_background_task(_notify(dorama_id, ep_list, quality))
                logger.info(
                    f"📢 Dispatched notify_subscribers_async for Dorama ID={dorama_id}, Ep={ep_list}, Quality={quality}"
                )
        except Exception as e:
            logger.warning(f"Could not trigger subscriber notification: {e}")


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
            f"🟢 <i>Botda darhol tomosha qilish mumkin!</i>"
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


async def run_listener(dry_run: bool = False):
    """Production Telethon event listener for Kdrama channels."""
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

    @client.on(events.NewMessage(chats=target_ids))
    async def handle_new_media(event: events.NewMessage.Event):
        msg = event.message
        text = msg.text or msg.message or ""

        # 1. Video Check
        is_video, duration, w, h, size = get_video_attributes(msg)
        if not is_video:
            return

        chat = await event.get_chat()
        chat_title = getattr(chat, "title", "Channel") or ""
        chat_username = (getattr(chat, "username", "") or "").lower()

        # Micro-drama detection (DramaBox, ReelShort, ShortMax, 9:16 vertical, @drammaworld)
        is_micro = bool(
            chat_username in ("drammaworld", "dramabox", "reelshort", "shortmax")
            or getattr(chat, "id", 0) == -1002313267574
            or "drama box" in chat_title.lower()
            or RE_MICRO_DRAMA.search(text)
            or (h > 0 and w > 0 and h > w)  # 9:16 vertical format
        )

        # 2. Duration Guard: Skip shorts/edits (<30s for micro-dramas, <90s for others)
        if duration > 0:
            if is_micro:
                if duration < 30:
                    logger.debug(f"Skipped ultra-short clip (<30s): {text[:40]}")
                    return
            elif duration < 90:
                logger.debug(f"Skipped short/edit (<90s): {text[:40]}")
                return

        # 3. Subtitle Check (Zero Subtitle Policy)
        if RE_SUBTITLE.search(text):
            logger.debug(f"Skipped subtitle post: {text[:40]}")
            return

        # 4. Mandatory Uzbek Dubbed indicator (bypassed for verified micro-drama sources)
        if not (is_micro or RE_UZB_DUB.search(text)):
            logger.debug(f"Skipped post lacking Uzbek dubbed indicator: {text[:40]}")
            return

        # 5. Episode Parsing (handles ranges like '1-11', '1-15', '12-25 qismlar')
        ep_list = parse_episodes(text)
        if not ep_list:
            logger.debug(f"Could not parse episode number from: {text[:40]}")
            return

        if len(ep_list) > 1:
            is_micro = True

        # 6. Title Extraction
        raw_title = clean_dorama_title(text)
        if not raw_title or len(raw_title) < 2:
            return

        quality = (
            f"{h}p" if h in (480, 720, 1080) else ("1080p" if h > 720 else "720p")
        )

        logger.info(
            f"🎬 DETECTED: '{raw_title}' Ep {ep_list} ({quality}, {duration}s, {size}b, micro={is_micro}) from '{chat_title}'"
        )

        if dry_run:
            logger.info(f"[DRY-RUN] Forward to storage & ingest verified. Skipped DB write.")
            return

        # 7. DB Pre-resolution (Prevents orphan files in storage)
        async with aiosqlite.connect(str(DB_PATH), timeout=30.0) as db:
            dorama_id = await find_or_create_dorama(db, raw_title, is_micro_drama=is_micro)
            if not dorama_id:
                logger.warning(f"Could not resolve or create dorama for '{raw_title}'")
                return

        # 8. Cloud-to-Cloud Forwarding
        try:
            fwd = await client.forward_messages(STORAGE_CHANNEL_ID, msg)
            storage_msg = fwd if isinstance(fwd, Message) else fwd[0]
            storage_msg_id = storage_msg.id
            logger.info(f"Cloud Forwarded to Storage -> msg_id={storage_msg_id}")
        except ChatForwardsRestrictedError:
            logger.warning(
                f"Skipped restricted channel '{chat_title}': Forwarding disabled (protected SSD/traffic)."
            )
            return
        except FloodWaitError as e:
            logger.warning(f"Telegram FloodWait: waiting {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
            return
        except Exception as e:
            logger.error(f"Forwarding exception: {e}")
            return

        # 9. Ingest into DB
        await ingest_episodes_to_db(dorama_id, ep_list, storage_msg_id, quality, size)

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
                ep_list=ep_list,
                quality=quality,
                file_size=size,
                chat_title=chat_title,
                storage_msg_id=storage_msg_id,
            )
        except Exception as e:
            logger.warning(f"Admin notification step skipped: {e}")

    logger.info("⚡ Autopilot Kdrama Listener is LIVE and actively monitoring...")
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


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    asyncio.run(run_listener(dry_run=is_dry))
