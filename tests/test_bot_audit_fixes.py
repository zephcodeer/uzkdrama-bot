"""Regression tests for bot.py, keyboards.py, database.py, and notifications.py audit fixes."""

import asyncio
import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import bot as bot_mod
import config
import database as db_mod
import keyboards as kb_mod
import notifications as notif_mod


ADMIN_UID = next(iter(config.ADMIN_IDS))


def _init_user_db(user_db_path: Path):
    with sqlite3.connect(user_db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                is_premium INTEGER DEFAULT 0,
                is_vip INTEGER DEFAULT 0,
                vip_until TIMESTAMP,
                invited_by INTEGER,
                referrals_count INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE promo_qualified_referrals (
                referee_id INTEGER PRIMARY KEY,
                inviter_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE system_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )


def test_admin_view_back_button_uses_menu_admin():
    markup = kb_mod.build_admin_users_view_kb([], filter_type="active", page=0, total_users=0)
    callbacks = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]
    assert "menu_admin" in callbacks
    assert "admin_panel" not in callbacks


def test_callback_malformed_data_and_sub_notice_safe_answer():
    async def run():
        call = SimpleNamespace(
            data="get_ep:bad:1",
            from_user=SimpleNamespace(id=12345, first_name="Test"),
            message=SimpleNamespace(reply_markup=None),
            answer=AsyncMock(),
        )
        bot = SimpleNamespace()
        await bot_mod.cb_get_ep(call, bot)
        call.answer.assert_awaited()

        call2 = SimpleNamespace(
            data="get_ep:10:2",
            from_user=SimpleNamespace(id=12345, first_name="Test"),
            message=SimpleNamespace(reply_markup=None),
            answer=AsyncMock(),
        )
        with (
            patch.object(bot_mod, "is_user_channel_member", AsyncMock(return_value=False)),
            patch.object(bot_mod, "send_sub_required_notice", AsyncMock()) as notice,
        ):
            await bot_mod.cb_get_ep(call2, bot)
            notice.assert_awaited_once()
            call2.answer.assert_awaited()

        call3 = SimpleNamespace(
            data="aview_f:active:notanint",
            from_user=SimpleNamespace(id=ADMIN_UID),
            answer=AsyncMock(),
        )
        await bot_mod.cb_aview_filter(call3)
        call3.answer.assert_awaited()

    asyncio.run(run())


def test_vip_approve_reject_works_without_photo_caption():
    async def run():
        text_msg = SimpleNamespace(
            photo=None,
            document=None,
            caption=None,
            text="Order #7",
            edit_caption=AsyncMock(side_effect=AssertionError("should not call edit_caption")),
            edit_text=AsyncMock(),
        )
        call = SimpleNamespace(
            data="admin_approve:7:111:30",
            from_user=SimpleNamespace(id=ADMIN_UID),
            message=text_msg,
            answer=AsyncMock(),
        )
        bot = SimpleNamespace(send_message=AsyncMock())
        with patch.object(db_mod, "resolve_vip_order", AsyncMock(return_value=(111, 30))):
            await bot_mod.cb_admin_approve(call, bot)
        text_msg.edit_text.assert_awaited_once()
        call.answer.assert_awaited()

        text_msg2 = SimpleNamespace(
            photo=None,
            document=None,
            caption=None,
            text="Order #8",
            edit_caption=AsyncMock(side_effect=AssertionError("should not call edit_caption")),
            edit_text=AsyncMock(),
        )
        call2 = SimpleNamespace(
            data="admin_reject:8:111",
            from_user=SimpleNamespace(id=ADMIN_UID),
            message=text_msg2,
            answer=AsyncMock(),
        )
        with patch.object(db_mod, "resolve_vip_order", AsyncMock(return_value=(111, 30))):
            await bot_mod.cb_admin_reject(call2, bot)
        text_msg2.edit_text.assert_awaited_once()
        call2.answer.assert_awaited()

    asyncio.run(run())


def test_ongoing_list_escapes_html_titles():
    async def run():
        event = SimpleNamespace(
            from_user=SimpleNamespace(id=ADMIN_UID),
            answer=AsyncMock(),
        )
        fake_doramas = [{"id": 1, "code": 500, "title": "A <B> & C", "uploaded_episodes": 3}]
        with (
            patch.object(db_mod, "get_ongoing_doramas", AsyncMock(return_value=fake_doramas)),
            patch.object(bot_mod, "render_text_screen", AsyncMock()) as render_mock,
        ):
            await bot_mod.handle_admin_ongoing_list(event)
            rendered_text = render_mock.call_args.args[1]
            assert "A &lt;B&gt; &amp; C" in rendered_text

    asyncio.run(run())


def test_vip_expiration_iso_and_invalid_dates(tmp_path):
    user_db = tmp_path / "userdata.db"
    _init_user_db(user_db)
    with sqlite3.connect(user_db) as conn:
        conn.execute(
            "INSERT INTO users (tg_id, is_vip, vip_until) VALUES (1, 1, '2099-01-01T12:00:00.123456')"
        )
        conn.execute(
            "INSERT INTO users (tg_id, is_vip, vip_until) VALUES (2, 1, '2020-01-01T12:00:00.123456')"
        )
        conn.execute(
            "INSERT INTO users (tg_id, is_vip, vip_until) VALUES (3, 1, 'not-a-timestamp')"
        )
        conn.commit()

    async def run():
        with patch.object(db_mod, "USER_DB_PATH", str(user_db)):
            assert await db_mod.is_vip(1) is True
            assert await db_mod.is_vip(2) is False
            assert await db_mod.is_vip(3) is False

            with patch.object(db_mod, "is_promo_free_mode", AsyncMock(return_value=False)):
                unlocked_bad, _, _, _ = await db_mod.is_user_unlocked(3, 5)
                assert unlocked_bad is False

    asyncio.run(run())


def test_register_user_atomic_no_double_referral(tmp_path):
    user_db = tmp_path / "userdata.db"
    _init_user_db(user_db)
    with sqlite3.connect(user_db) as conn:
        conn.execute("INSERT INTO users (tg_id, referrals_count) VALUES (10, 0)")
        conn.commit()

    async def run():
        with patch.object(db_mod, "USER_DB_PATH", str(user_db)):
            res1, res2 = await asyncio.gather(
                db_mod.register_user(20, "u20", "U20", False, referrer_id=10),
                db_mod.register_user(20, "u20", "U20", False, referrer_id=10),
            )
            assert sum(1 for r in (res1, res2) if r[0] is True) == 1

    asyncio.run(run())
    with sqlite3.connect(user_db) as conn:
        refs = conn.execute("SELECT referrals_count FROM users WHERE tg_id = 10").fetchone()[0]
        assert refs == 1


def test_notifications_send_photo_bad_request_falls_back_to_send_message():
    async def run():
        fake_bot = SimpleNamespace(
            send_photo=AsyncMock(side_effect=TelegramBadRequest(method=MagicMock(), message="wrong file identifier")),
            send_message=AsyncMock(),
            session=SimpleNamespace(close=AsyncMock()),
        )
        with (
            patch.object(db_mod, "get_dorama_subscribers", AsyncMock(return_value=[777])),
            patch.object(db_mod, "get_dorama_by_id", AsyncMock(return_value={"id": 1, "title": "Test", "code": 101, "poster_url": "https://example.com/a.jpg", "total_episodes": 10})),
            patch("asyncio.sleep", AsyncMock()),
        ):
            sent = await notif_mod.notify_subscribers_async(1, [2], quality="1080p", bot=fake_bot)
            assert sent == 1
            fake_bot.send_photo.assert_awaited_once()
            fake_bot.send_message.assert_awaited_once()

    asyncio.run(run())


def test_dd_attach_preserves_state_when_code_not_found(tmp_path):
    pending_path = tmp_path / "pending_drops.json"
    pending_path.write_text(
        json.dumps({"555": {"raw_title": "Test", "ep_list": [1], "storage_msg_id": 555, "quality": "720p", "size": 100}}),
        encoding="utf-8",
    )

    async def run():
        state = SimpleNamespace(
            get_data=AsyncMock(return_value={"dd_msg_id": "555"}),
            clear=AsyncMock(),
        )
        msg = SimpleNamespace(
            from_user=SimpleNamespace(id=ADMIN_UID),
            text="99999",
            answer=AsyncMock(),
        )
        with (
            patch.object(bot_mod, "PENDING_DROPS_PATH", str(pending_path)),
            patch.object(db_mod, "get_dorama_by_code", AsyncMock(return_value=None)),
        ):
            await bot_mod.msg_dd_attach_code(msg, state)
            state.clear.assert_not_awaited()
            assert "555" in json.loads(pending_path.read_text(encoding="utf-8"))

    asyncio.run(run())
