import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.append(r"E:\Agent\Drama Bot")
import bot
import database as db
from aiogram.types import User, Chat, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey

print("=" * 60)
print("SIMULATING FULL USER FLOW IN BOT.PY")
print("=" * 60)

storage = MemoryStorage()

async def simulate():
    await db.init_db()

    mock_bot = MagicMock()
    mock_bot.get_me = AsyncMock(return_value=MagicMock(username="uzkdrama_app"))
    mock_bot.send_message = AsyncMock(return_value=MagicMock(message_id=999))
    mock_bot.send_photo = AsyncMock(return_value=MagicMock(message_id=998))
    mock_bot.copy_message = AsyncMock(return_value=MagicMock(message_id=997))

    user = User(id=7141955036, is_bot=False, first_name="MuhammadSodiq", username="corecod")
    chat = Chat(id=7141955036, type="private")
    key = StorageKey(bot_id=123, chat_id=chat.id, user_id=user.id)
    fsm = FSMContext(storage=storage, key=key)

    import datetime
    now = datetime.datetime.now()
    # 1. Test /start
    print("\n[TEST 1] /start command")
    msg = MagicMock(spec=Message)
    msg.from_user = user
    msg.chat = chat
    msg.text = "/start"
    msg.answer = AsyncMock()
    await bot.cmd_start(msg, MagicMock(args=None), mock_bot, fsm)
    print("  ✅ /start executed successfully")

    # 2. Test /start 118 (Kino kodi)
    print("\n[TEST 2] /start 118 (Kino kodi)")
    await bot.cmd_start(msg, MagicMock(args="118"), mock_bot, fsm)
    print("  ✅ /start 118 executed successfully")

    # 3. Test /start d_18
    print("\n[TEST 3] /start d_18 (Dorama ID)")
    await bot.cmd_start(msg, MagicMock(args="d_18"), mock_bot, fsm)
    print("  ✅ /start d_18 executed successfully")

    # 4. Test menu_home callback
    print("\n[TEST 4] menu_home callback")
    call_msg = MagicMock(spec=Message)
    call_msg.photo = None
    call_msg.video = None
    call_msg.document = None
    call_msg.edit_text = AsyncMock()
    call_msg.answer = AsyncMock()
    call = MagicMock(spec=CallbackQuery)
    call.id = "1"
    call.from_user = user
    call.chat_instance = "1"
    call.message = call_msg
    call.data = "menu_home"
    call.answer = AsyncMock()
    await bot.cb_menu_home(call, fsm)
    print("  ✅ menu_home executed successfully")

    # 5. Test menu_latest:0
    print("\n[TEST 5] menu_latest:0 callback")
    call.data = "menu_latest:0"
    await bot.cb_menu_latest(call)
    print("  ✅ menu_latest:0 executed successfully")

    # 6. Test menu_top
    print("\n[TEST 6] menu_top callback")
    call.data = "menu_top"
    await bot.cb_menu_top(call)
    print("  ✅ menu_top executed successfully")

    # 7. Test menu_bookmarks
    print("\n[TEST 7] menu_bookmarks callback")
    call.data = "menu_bookmarks"
    await bot.cb_menu_bookmarks(call)
    print("  ✅ menu_bookmarks executed successfully")

    # 8. Test menu_stats
    print("\n[TEST 8] menu_stats callback")
    call.data = "menu_stats"
    await bot.cb_menu_stats(call)
    print("  ✅ menu_stats executed successfully")

    # 9. Test menu_vip
    print("\n[TEST 9] menu_vip callback")
    call.data = "menu_vip"
    await bot.cb_menu_vip(call, fsm)
    print("  ✅ menu_vip executed successfully")

    # 10. Test buy_vip:1m
    print("\n[TEST 10] buy_vip:1m callback")
    call.data = "buy_vip:1m"
    await bot.cb_buy_vip(call, fsm)
    print("  ✅ buy_vip:1m executed successfully")

    # 11. Test submit_receipt:1m
    print("\n[TEST 11] submit_receipt:1m callback")
    call.data = "submit_receipt:1m"
    await bot.cb_submit_receipt(call, fsm)
    print("  ✅ submit_receipt:1m executed successfully")

    # 12. Test view_dorama:18 (Ovchi itlar)
    print("\n[TEST 12] view_dorama:18 callback")
    call.data = "view_dorama:18"
    await bot.cb_view_dorama(call, mock_bot)
    print("  ✅ view_dorama:18 executed successfully")

    # 13. Test get_ep:18:1 (Free episode)
    print("\n[TEST 13] get_ep:18:1 (Free episode)")
    call.data = "get_ep:18:1"
    await bot.cb_get_ep(call, mock_bot)
    print("  ✅ get_ep:18:1 executed successfully")

    # 14. Test toggle_bm:18 and toggle_sub:18
    print("\n[TEST 14] toggle_bm:18 & toggle_sub:18")
    call.data = "toggle_bm:18"
    await bot.cb_toggle_bm(call, mock_bot)
    call.data = "toggle_sub:18"
    await bot.cb_toggle_sub(call, mock_bot)
    print("  ✅ toggle_bm & toggle_sub executed successfully")

    # 15. Test photo message transition
    print("\n[TEST 15] Photo message edit transition (render_text_screen on photo)")
    photo_msg = MagicMock(spec=Message)
    photo_msg.photo = [MagicMock()]
    photo_msg.delete = AsyncMock()
    photo_msg.answer = AsyncMock()
    photo_call = MagicMock(spec=CallbackQuery)
    photo_call.id = "2"
    photo_call.from_user = user
    photo_call.chat_instance = "1"
    photo_call.message = photo_msg
    photo_call.data = "menu_search"
    photo_call.answer = AsyncMock()
    await bot.cb_menu_search(photo_call, fsm)
    print("  ✅ render_text_screen on photo executed without crashing!")

    print("\n" + "=" * 60)
    print("ALL 15 BOT FLOW SIMULATION TESTS PASSED WITH ZERO CRASHES!")
    print("=" * 60)

asyncio.run(simulate())
