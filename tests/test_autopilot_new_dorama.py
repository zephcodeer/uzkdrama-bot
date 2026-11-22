"""Regression coverage for first episodes entering the live ingest pipeline."""

import asyncio
import sqlite3
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from telethon.tl.types import Message, PeerChannel

from scripts import autopilot_donor_listener as autopilot


def test_first_episode_is_forwarded_and_saved(tmp_path):
    db_path = tmp_path / "doramas.db"
    with sqlite3.connect(db_path) as db:
        db.executescript(
            """
            CREATE TABLE doramas (
                id INTEGER PRIMARY KEY, code INTEGER UNIQUE, title TEXT,
                slug TEXT UNIQUE, status TEXT, country TEXT,
                total_episodes INTEGER, views INTEGER, category TEXT,
                genre TEXT, description TEXT, aliases TEXT
            );
            CREATE TABLE episodes (
                dorama_id INTEGER, episode_number INTEGER,
                channel_message_id INTEGER, quality TEXT, file_size INTEGER,
                UNIQUE(dorama_id, episode_number)
            );
            """
        )

    msg = SimpleNamespace(
        id=42,
        chat_id=-1001234567890,
        text="Sirli dunyo 1-qism o'zbek tilida",
        get_chat=AsyncMock(return_value=SimpleNamespace(title="Donor", username="donor")),
    )
    client = SimpleNamespace(
        forward_messages=AsyncMock(return_value=Message(id=777, peer_id=PeerChannel(123)))
    )

    async def run():
        with (
            patch.object(autopilot, "DB_PATH", db_path),
            patch.object(autopilot, "get_video_attributes", return_value=(True, 1800, 1920, 1080, 1234)),
            patch.object(autopilot, "update_channel_state") as state,
            patch.object(autopilot, "notify_subscribers_async", new_callable=AsyncMock),
            patch.object(autopilot, "send_admin_notification", new_callable=AsyncMock) as admin,
            patch.object(autopilot, "schedule_catalog_sync") as sync,
        ):
            assert await autopilot.process_donor_message(client, msg)
            await asyncio.gather(*autopilot._BACKGROUND_TASKS)
            client.forward_messages.assert_awaited_once_with(autopilot.STORAGE_CHANNEL_ID, msg)
            admin.assert_awaited_once()
            sync.assert_called_once_with(client)
            state.assert_called_with(msg.chat_id, msg.id)

    asyncio.run(run())

    with sqlite3.connect(db_path) as db:
        assert db.execute("SELECT title, total_episodes FROM doramas").fetchone() == ("Sirli Dunyo", 1)
        assert db.execute(
            "SELECT episode_number, channel_message_id FROM episodes"
        ).fetchone() == (1, 777)


def test_failed_forward_does_not_create_empty_dorama(tmp_path):
    db_path = tmp_path / "doramas.db"
    with sqlite3.connect(db_path) as db:
        db.executescript(
            """
            CREATE TABLE doramas (
                id INTEGER PRIMARY KEY, code INTEGER UNIQUE, title TEXT,
                slug TEXT UNIQUE, status TEXT, country TEXT,
                total_episodes INTEGER, views INTEGER, category TEXT,
                genre TEXT, description TEXT, aliases TEXT
            );
            CREATE TABLE episodes (
                dorama_id INTEGER, episode_number INTEGER,
                channel_message_id INTEGER, quality TEXT, file_size INTEGER,
                UNIQUE(dorama_id, episode_number)
            );
            """
        )

    msg = SimpleNamespace(
        id=42,
        chat_id=-1001234567890,
        text="Sirli dunyo 1-qism o'zbek tilida",
        get_chat=AsyncMock(return_value=SimpleNamespace(title="Donor", username="donor")),
    )
    client = SimpleNamespace(forward_messages=AsyncMock(side_effect=RuntimeError("temporary outage")))

    async def run():
        with (
            patch.object(autopilot, "DB_PATH", db_path),
            patch.object(autopilot, "get_video_attributes", return_value=(True, 1800, 1920, 1080, 1234)),
            patch.object(autopilot, "update_channel_state") as state,
        ):
            assert not await autopilot.process_donor_message(client, msg)
            state.assert_not_called()

    asyncio.run(run())
    with sqlite3.connect(db_path) as db:
        assert db.execute("SELECT count(*) FROM doramas").fetchone()[0] == 0
