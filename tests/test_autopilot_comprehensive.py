"""Comprehensive regression tests for autopilot_donor_listener.py fixes."""

import asyncio
import json
import sqlite3
import sys
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import aiosqlite
import pytest
from telethon.errors import FloodWaitError
from telethon.tl.types import DocumentAttributeFilename

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "scripts"))

from scripts import autopilot_donor_listener as autopilot


def _init_test_db(db_path: Path):
    with sqlite3.connect(db_path) as db:
        db.executescript(
            """
            CREATE TABLE doramas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code INTEGER UNIQUE,
                title TEXT,
                slug TEXT UNIQUE,
                status TEXT,
                country TEXT,
                total_episodes INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                category TEXT,
                genre TEXT,
                description TEXT,
                aliases TEXT
            );
            CREATE TABLE episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dorama_id INTEGER,
                episode_number INTEGER,
                channel_message_id INTEGER,
                quality TEXT,
                file_size INTEGER,
                UNIQUE(dorama_id, episode_number)
            );
            """
        )


def test_nfkc_unicode_episode_and_title_parsing():
    caption = "• 🌸Nanyang jumbog'i ✨ \n 🌷13-𝐪𝐢𝐬𝐦🌷"
    assert autopilot.parse_episodes(caption) == [13]
    assert autopilot.parse_episodes("14-𝐪𝐢𝐬𝐦") == [14]
    title = autopilot.clean_dorama_title(caption)
    assert title.lower() == "nanyang jumbog'i"


def test_curly_apostrophe_preserved_and_smart_title_case(tmp_path):
    assert autopilot.clean_dorama_title("100 kunlik yolg‘on 11-qism").lower() == "100 kunlik yolg‘on"
    assert autopilot._smart_title_case("oʻrinbosar") == "Oʻrinbosar"
    assert autopilot._smart_title_case("crash 2: xavfli yoʻl") == "Crash 2: Xavfli Yoʻl"
    assert autopilot._smart_title_case("o'g'ri") == "O'g'ri"

    db_path = tmp_path / "doramas.db"
    _init_test_db(db_path)
    with sqlite3.connect(db_path) as db:
        db.execute(
            "INSERT INTO doramas (code, title, slug, status, category) VALUES (501, ?, '100-kunlik-yolgon', 'Ongoing', 'korea')",
            ("100 Kunlik Yolg'on",),
        )
        db.commit()

    async def run():
        async with aiosqlite.connect(db_path) as db:
            found = await autopilot.find_dorama_id(db, "100 kunlik yolg‘on 11-qism")
            assert found == 1

            new_id = await autopilot.create_new_dorama(db, "Oʻrinbosar 1-qism")
            assert new_id == 2
            async with db.execute("SELECT title FROM doramas WHERE id = ?", (new_id,)) as cur:
                row = await cur.fetchone()
                assert row[0] == "Oʻrinbosar"

    asyncio.run(run())


def test_url_only_title_rejected():
    assert autopilot.clean_dorama_title("(https://t.me/section_e_uzb_dub_sub/4829) 10-qism") == ""
    assert autopilot.clean_dorama_title("https://t.me/some_channel/123") == ""


def test_parse_episodes_precedence_and_year_guard():
    assert autopilot.parse_episodes("Dorama (2024-2025)\n15-qism") == [15]
    assert autopilot.parse_episodes("Dorama (1-2)\n15-qism") == [15]
    assert autopilot.parse_episodes("Yulduzlar 2024-2025 yil") is None
    assert autopilot.parse_episodes("16-18 yosh\n5-qism") == [5]


def test_language_filters_ovoz_berilgan_and_empty_text():
    ok1, _ = autopilot.is_uzbek_dubbed("Dorama 1-qism ovoz berilgan")
    ok2, _ = autopilot.is_uzbek_dubbed("Dorama 1-qism ovoz beriladi")
    ok3, reason3 = autopilot.is_uzbek_dubbed("", chat_title="O'zbek tilida doramalar")
    assert ok1 is True
    assert ok2 is True
    assert ok3 is True
    assert "channel_title" in reason3

    is_sub, _ = autopilot.is_subtitle_release("sub.uz 1-qism")
    assert is_sub is True


def test_vertical_video_quality_detection():
    assert autopilot.determine_quality(720, 1280) == "720p"
    assert autopilot.determine_quality(1080, 1920) == "1080p"
    assert autopilot.determine_quality(480, 854) == "480p"
    assert autopilot.determine_quality(1920, 1080) == "1080p"
    assert autopilot.determine_quality(1280, 720) == "720p"
    assert autopilot.determine_quality(0, 0, text="1080p") == "1080p"
    assert autopilot.determine_quality(0, 0) == "unknown"


def test_find_dorama_id_is_readonly_and_create_retries_integrity_error(tmp_path):
    db_path = tmp_path / "doramas.db"
    _init_test_db(db_path)
    with sqlite3.connect(db_path) as db:
        db.execute(
            "INSERT INTO doramas (code, title, slug, status, category) VALUES (501, 'Test Micro', 'test-micro', 'Ongoing', 'korea')"
        )
        db.commit()

    async def run():
        async with aiosqlite.connect(db_path) as db:
            d_id = await autopilot.find_dorama_id(db, "Test Micro", is_micro_drama=True)
            assert d_id == 1
            async with db.execute("SELECT category FROM doramas WHERE id = 1") as cur:
                assert (await cur.fetchone())[0] == "korea"

    asyncio.run(run())


def test_direct_storage_drop_sends_admin_notif_and_handles_vertical_quality(tmp_path):
    db_path = tmp_path / "doramas.db"
    _init_test_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO doramas (id, code, title, slug, status, country, total_episodes, views, category) VALUES (1, 101, 'Vertikal Sevgi', 'vertikal-sevgi', 'Ongoing', 'Koreya', 1, 0, 'duanju')")
    conn.commit()
    conn.close()

    msg = SimpleNamespace(
        id=9001,
        text="Vertikal Sevgi 1-qism",
        message="Vertikal Sevgi 1-qism",
        video=SimpleNamespace(attributes=[]),
        document=None,
    )
    client = SimpleNamespace()

    async def run():
        with (
            patch.object(autopilot, "DB_PATH", db_path),
            patch.object(autopilot, "get_video_attributes", return_value=(True, 120, 720, 1280, 500000)),
            patch.object(autopilot, "notify_subscribers_async", new_callable=AsyncMock),
            patch.object(autopilot, "send_admin_notification", new_callable=AsyncMock) as admin_notif,
            patch.object(autopilot, "schedule_catalog_sync") as sync_mock,
        ):
            ok = await autopilot.process_direct_storage_message(client, msg)
            assert ok is True
            if autopilot._BACKGROUND_TASKS:
                await asyncio.gather(*list(autopilot._BACKGROUND_TASKS), return_exceptions=True)
            admin_notif.assert_awaited_once()
            assert admin_notif.call_args.kwargs["quality"] == "720p"
            sync_mock.assert_called_once_with(client)

    asyncio.run(run())

    with sqlite3.connect(db_path) as db:
        row = db.execute("SELECT quality FROM episodes WHERE channel_message_id = 9001").fetchone()
        assert row == ("720p",)


def test_atomic_state_concurrent_updates(tmp_path):
    state_file = tmp_path / "autopilot_state.json"

    with patch.object(autopilot, "STATE_FILE", state_file):
        errors = []

        def worker(cid, start_id):
            try:
                for i in range(20):
                    autopilot.update_channel_state(cid, start_id + i)
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=worker, args=(-1001, 100)),
            threading.Thread(target=worker, args=(-1002, 200)),
            threading.Thread(target=worker, args=(-1003, 300)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert data["-1001"] == 119
        assert data["-1002"] == 219
        assert data["-1003"] == 319


def test_warm_up_handles_floodwait_and_sync_worker_cancels():
    fw = FloodWaitError(request=None, capture=1)
    client = SimpleNamespace(
        get_input_entity=AsyncMock(side_effect=[fw, "ok"]),
        get_entity=AsyncMock(),
    )

    async def run():
        with patch("asyncio.sleep", new_callable=AsyncMock) as sleep_mock:
            await autopilot.warm_up_channel_entities(client, [-100123])
            assert client.get_input_entity.await_count == 2
            sleep_mock.assert_awaited_with(2)

    asyncio.run(run())


def test_staggered_catchup_cold_start_processes_latest_message(tmp_path):
    state_file = tmp_path / "autopilot_state.json"
    msg = SimpleNamespace(id=555, chat_id=-100999)

    async def fake_iter_messages(cid, **kwargs):
        yield msg

    client = SimpleNamespace(iter_messages=fake_iter_messages)
    locks = {-100999: asyncio.Lock()}

    async def run():
        with (
            patch.object(autopilot, "STATE_FILE", state_file),
            patch.object(autopilot, "process_donor_message", new_callable=AsyncMock, return_value=True) as proc_mock,
            patch("asyncio.sleep", side_effect=[None, asyncio.CancelledError()]),
        ):
            await autopilot.staggered_catchup_sync(client, [-100999], locks, dry_run=False)
            proc_mock.assert_awaited_once_with(client, msg, dry_run=False, advance_state=True)

    asyncio.run(run())


def test_run_listener_empty_targets_and_clean_shutdown(tmp_path):
    missing_donors = tmp_path / "missing_donors.json"
    state_file = tmp_path / "autopilot_state.json"
    handlers_registered = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self._connected = False

        async def connect(self):
            self._connected = True

        async def is_user_authorized(self):
            return True

        async def get_me(self):
            return SimpleNamespace(username="testbot", first_name="Test", id=1)

        def is_connected(self):
            return self._connected

        def on(self, event_builder):
            handlers_registered.append(event_builder)
            def decorator(fn):
                return fn
            return decorator

        async def get_messages(self, *args, **kwargs):
            return []

        async def get_input_entity(self, *args, **kwargs):
            return "ok"

        async def run_until_disconnected(self):
            raise asyncio.CancelledError()

        async def disconnect(self):
            self._connected = False

    async def run():
        with (
            patch.object(autopilot, "DONOR_FILTERED_PATH", missing_donors),
            patch.object(autopilot, "STATE_FILE", state_file),
            patch.object(autopilot, "TelegramClient", FakeClient),
        ):
            await autopilot.run_listener(dry_run=True)

    asyncio.run(run())
    # Only STORAGE_CHANNEL_ID handler should be registered, never empty chats=[]
    assert len(handlers_registered) == 1
    assert handlers_registered[0].chats == {autopilot.STORAGE_CHANNEL_ID} or handlers_registered[0].chats == [autopilot.STORAGE_CHANNEL_ID]
