import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch, MagicMock

import bot
import database as db
import keyboards as kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def extract_button_by_text(markup: InlineKeyboardMarkup, text_substr: str) -> InlineKeyboardButton | None:
    """Helper to locate an inline keyboard button by partial or exact label."""
    if not markup or not getattr(markup, "inline_keyboard", None):
        return None
    for row in markup.inline_keyboard:
        for btn in row:
            if text_substr in (btn.text or ""):
                return btn
    return None


def extract_button_by_callback(markup: InlineKeyboardMarkup, callback_data: str) -> InlineKeyboardButton | None:
    """Helper to locate an inline keyboard button by exact callback_data."""
    if not markup or not getattr(markup, "inline_keyboard", None):
        return None
    for row in markup.inline_keyboard:
        for btn in row:
            if btn.callback_data == callback_data:
                return btn
    return None


class TestRandomNavigationFlow(unittest.IsolatedAsyncioTestCase):
    """1. menu_random card contains '🎲 Boshqa tavsiya' and 'Orqaga' routes to menu_home."""

    def test_random_detail_kb_has_reroll_and_routes_to_home(self):
        markup = kb.dorama_detail_kb(
            dorama_id=1,
            episodes=[],
            back_cb="menu_home",
            is_random=True
        )

        reroll_btn = extract_button_by_text(markup, "Boshqa tavsiya")
        self.assertIsNotNone(reroll_btn, "Random detail view must include '🎲 Boshqa tavsiya' button")
        self.assertEqual(reroll_btn.callback_data, "menu_random", "Re-roll button must have callback_data='menu_random'")

        back_btn = extract_button_by_text(markup, "Orqaga")
        self.assertIsNotNone(back_btn, "Random detail view must include 'Orqaga' button")
        self.assertEqual(back_btn.callback_data, "menu_home", "Random view 'Orqaga' must route to 'menu_home'")

    def test_standard_detail_kb_does_not_contain_reroll(self):
        markup = kb.dorama_detail_kb(
            dorama_id=1,
            episodes=[],
            back_cb="menu_home",
            is_random=False
        )
        reroll_btn = extract_button_by_text(markup, "Boshqa tavsiya")
        self.assertIsNone(reroll_btn, "Standard (non-random) detail view must not include re-roll button")

    async def test_cb_menu_random_calls_show_dorama_detail_with_random_context(self):
        mock_dorama = {
            "id": 99,
            "title": "Random Test Drama",
            "code": 999,
            "total_episodes": 16,
            "poster_url": None,
            "status": "Completed"
        }
        mock_call = SimpleNamespace(
            from_user=SimpleNamespace(id=12345, is_premium=False, first_name="Tester"),
            message=SimpleNamespace(
                photo=None,
                answer=AsyncMock(),
                edit_text=AsyncMock(),
                delete=AsyncMock()
            ),
            answer=AsyncMock()
        )
        mock_bot = SimpleNamespace(
            get_me=AsyncMock(return_value=SimpleNamespace(username="test_bot")),
            send_photo=AsyncMock()
        )

        with patch.object(db, "get_random_dorama", AsyncMock(return_value=mock_dorama)), \
             patch.object(bot, "show_dorama_detail", AsyncMock()) as mock_show_detail, \
             patch.object(bot, "safe_answer", AsyncMock()):
            await bot.cb_menu_random(mock_call, mock_bot)
            mock_show_detail.assert_awaited_once_with(
                mock_call,
                mock_dorama["id"],
                mock_bot,
                user_id=mock_call.from_user.id,
                back_cb="menu_home",
                is_random=True
            )

    async def test_cb_view_dorama_random_source_maps_to_random_context(self):
        mock_call = SimpleNamespace(
            data="view_dorama:99:random",
            from_user=SimpleNamespace(id=12345),
            answer=AsyncMock()
        )
        mock_bot = SimpleNamespace()

        with patch.object(bot, "show_dorama_detail", AsyncMock()) as mock_show_detail, \
             patch.object(bot, "safe_answer", AsyncMock()):
            await bot.cb_view_dorama(mock_call, mock_bot)
            mock_show_detail.assert_awaited_once_with(
                mock_call,
                99,
                mock_bot,
                user_id=12345,
                back_cb="menu_home",
                is_random=True
            )


class TestCategoryNavigationFlow(unittest.IsolatedAsyncioTestCase):
    """2. From categories (cat:mini:1), clicking detail then 'Orqaga' returns to cat:mini:1."""

    def test_category_list_kb_preserves_category_and_page(self):
        items = [{"id": 101, "title": "Mini Drama 1", "code": 501, "total_episodes": 6}]
        markup = kb.doramas_list_kb(items, prefix="cat:mini", page=1)

        item_btn = extract_button_by_callback(markup, "view_dorama:101:cat:mini:1")
        self.assertIsNotNone(item_btn, "List item callback must include full category and page context 'cat:mini:1'")

    def test_category_detail_kb_routes_back_to_exact_category_page(self):
        markup = kb.dorama_detail_kb(
            dorama_id=101,
            episodes=[],
            back_cb="cat:mini:1",
            is_random=False
        )

        back_btn = extract_button_by_text(markup, "Orqaga")
        self.assertIsNotNone(back_btn, "Detail view must have an 'Orqaga' button")
        self.assertEqual(back_btn.callback_data, "cat:mini:1", "Orqaga must route back to 'cat:mini:1'")

        reroll_btn = extract_button_by_text(markup, "Boshqa tavsiya")
        self.assertIsNone(reroll_btn, "Category navigation flow must not contain random re-roll button")

    async def test_cb_view_dorama_from_category_passes_exact_back_cb(self):
        mock_call = SimpleNamespace(
            data="view_dorama:101:cat:mini:1",
            from_user=SimpleNamespace(id=12345),
            answer=AsyncMock()
        )
        mock_bot = SimpleNamespace()

        with patch.object(bot, "show_dorama_detail", AsyncMock()) as mock_show_detail, \
             patch.object(bot, "safe_answer", AsyncMock()):
            await bot.cb_view_dorama(mock_call, mock_bot)
            mock_show_detail.assert_awaited_once_with(
                mock_call,
                101,
                mock_bot,
                user_id=12345,
                back_cb="cat:mini:1",
                is_random=False
            )

    async def test_clicking_back_to_category_triggers_category_view(self):
        mock_call = SimpleNamespace(
            data="cat:mini:1",
            from_user=SimpleNamespace(id=12345),
            message=SimpleNamespace(photo=None, edit_text=AsyncMock()),
            answer=AsyncMock()
        )
        items = [{"id": 101, "title": "Mini Drama 1", "code": 501, "total_episodes": 6}]

        with patch.object(db, "get_doramas_by_category", AsyncMock(return_value=("Mini Dramalar", items))) as mock_cat, \
             patch.object(bot, "render_text_screen", AsyncMock()) as mock_render, \
             patch.object(bot, "safe_answer", AsyncMock()):
            await bot.cb_category_view(mock_call)
            mock_cat.assert_awaited_once_with("mini", limit=9, offset=8)
            mock_render.assert_awaited_once()


class TestBookmarksNavigationFlow(unittest.IsolatedAsyncioTestCase):
    """3. From bookmarks, clicking detail then 'Orqaga' returns to menu_bookmarks."""

    def test_bookmarks_list_kb_preserves_bookmarks_context(self):
        items = [{"id": 202, "title": "Favorite Drama", "code": 602}]
        markup = kb.doramas_list_kb(items, prefix="bookmarks", page=0)

        item_btn = extract_button_by_callback(markup, "view_dorama:202:menu_bookmarks")
        self.assertIsNotNone(item_btn, "List item callback for page 0 bookmarks must be 'view_dorama:202:menu_bookmarks'")

    def test_bookmarks_detail_kb_routes_back_to_bookmarks(self):
        markup = kb.dorama_detail_kb(
            dorama_id=202,
            episodes=[],
            back_cb="menu_bookmarks",
            is_random=False
        )

        back_btn = extract_button_by_text(markup, "Orqaga")
        self.assertIsNotNone(back_btn, "Detail view must have an 'Orqaga' button")
        self.assertEqual(back_btn.callback_data, "menu_bookmarks", "Orqaga must route back to 'menu_bookmarks'")

    async def test_cb_view_dorama_from_bookmarks_passes_bookmarks_back_cb(self):
        mock_call = SimpleNamespace(
            data="view_dorama:202:menu_bookmarks",
            from_user=SimpleNamespace(id=12345),
            answer=AsyncMock()
        )
        mock_bot = SimpleNamespace()

        with patch.object(bot, "show_dorama_detail", AsyncMock()) as mock_show_detail, \
             patch.object(bot, "safe_answer", AsyncMock()):
            await bot.cb_view_dorama(mock_call, mock_bot)
            mock_show_detail.assert_awaited_once_with(
                mock_call,
                202,
                mock_bot,
                user_id=12345,
                back_cb="menu_bookmarks",
                is_random=False
            )

    async def test_clicking_back_to_bookmarks_triggers_bookmarks_view(self):
        mock_call = SimpleNamespace(
            data="menu_bookmarks",
            from_user=SimpleNamespace(id=12345),
            message=SimpleNamespace(photo=None, edit_text=AsyncMock()),
            answer=AsyncMock()
        )
        items = [{"id": 202, "title": "Favorite Drama", "code": 602}]

        with patch.object(db, "get_user_bookmarks", AsyncMock(return_value=items)) as mock_bm, \
             patch.object(bot, "render_text_screen", AsyncMock()) as mock_render, \
             patch.object(bot, "safe_answer", AsyncMock()):
            await bot.cb_menu_bookmarks(mock_call)
            mock_bm.assert_awaited_once_with(12345)
            mock_render.assert_awaited_once()


class TestTopNavigationFlow(unittest.IsolatedAsyncioTestCase):
    """4. From top, clicking detail then 'Orqaga' returns to menu_top."""

    def test_top_list_kb_preserves_top_context(self):
        items = [{"id": 303, "title": "Top Hit Drama", "code": 703}]
        markup = kb.doramas_list_kb(items, prefix="menu_top", page=0)

        item_btn = extract_button_by_callback(markup, "view_dorama:303:menu_top")
        self.assertIsNotNone(item_btn, "List item callback for page 0 top must be 'view_dorama:303:menu_top'")

    def test_top_detail_kb_routes_back_to_top(self):
        markup = kb.dorama_detail_kb(
            dorama_id=303,
            episodes=[],
            back_cb="menu_top",
            is_random=False
        )

        back_btn = extract_button_by_text(markup, "Orqaga")
        self.assertIsNotNone(back_btn, "Detail view must have an 'Orqaga' button")
        self.assertEqual(back_btn.callback_data, "menu_top", "Orqaga must route back to 'menu_top'")

    async def test_cb_view_dorama_from_top_passes_top_back_cb(self):
        mock_call = SimpleNamespace(
            data="view_dorama:303:menu_top",
            from_user=SimpleNamespace(id=12345),
            answer=AsyncMock()
        )
        mock_bot = SimpleNamespace()

        with patch.object(bot, "show_dorama_detail", AsyncMock()) as mock_show_detail, \
             patch.object(bot, "safe_answer", AsyncMock()):
            await bot.cb_view_dorama(mock_call, mock_bot)
            mock_show_detail.assert_awaited_once_with(
                mock_call,
                303,
                mock_bot,
                user_id=12345,
                back_cb="menu_top",
                is_random=False
            )

    async def test_clicking_back_to_top_triggers_top_view(self):
        mock_call = SimpleNamespace(
            data="menu_top",
            from_user=SimpleNamespace(id=12345),
            message=SimpleNamespace(photo=None, edit_text=AsyncMock()),
            answer=AsyncMock()
        )
        items = [{"id": 303, "title": "Top Hit Drama", "code": 703}]

        with patch.object(db, "get_top_doramas", AsyncMock(return_value=items)) as mock_top, \
             patch.object(bot, "render_text_screen", AsyncMock()) as mock_render, \
             patch.object(bot, "safe_answer", AsyncMock()):
            await bot.cb_menu_top(mock_call)
            mock_top.assert_awaited_once_with(limit=9, offset=0)
            mock_render.assert_awaited_once()


class TestNavigationContextPreservation(unittest.IsolatedAsyncioTestCase):
    """5. Preserving navigation context across pagination and toggles."""

    def test_extract_dorama_nav_context_from_message(self):
        # 1. Random markup
        rand_markup = kb.dorama_detail_kb(1, [], is_random=True, back_cb="menu_home")
        msg_rand = SimpleNamespace(reply_markup=rand_markup)
        back_cb, is_random = bot.extract_dorama_nav_context(msg_rand)
        self.assertTrue(is_random)
        self.assertEqual(back_cb, "menu_home")

        # 2. Category markup
        cat_markup = kb.dorama_detail_kb(1, [], is_random=False, back_cb="cat:mini:1")
        msg_cat = SimpleNamespace(reply_markup=cat_markup)
        back_cb, is_random = bot.extract_dorama_nav_context(msg_cat)
        self.assertFalse(is_random)
        self.assertEqual(back_cb, "cat:mini:1")

        # 3. Bookmarks markup
        bm_markup = kb.dorama_detail_kb(1, [], is_random=False, back_cb="menu_bookmarks")
        msg_bm = SimpleNamespace(reply_markup=bm_markup)
        back_cb, is_random = bot.extract_dorama_nav_context(msg_bm)
        self.assertFalse(is_random)
        self.assertEqual(back_cb, "menu_bookmarks")

    async def test_cb_ep_page_preserves_navigation_context(self):
        existing_markup = kb.dorama_detail_kb(10, [], back_cb="cat:mini:1", is_random=False)
        mock_call = SimpleNamespace(
            data="ep_page:10:1",
            from_user=SimpleNamespace(id=12345),
            message=SimpleNamespace(reply_markup=existing_markup),
            answer=AsyncMock()
        )
        mock_bot = SimpleNamespace()

        with patch.object(bot, "show_dorama_detail", AsyncMock()) as mock_show_detail, \
             patch.object(bot, "safe_answer", AsyncMock()):
            await bot.cb_ep_page(mock_call, mock_bot)
            mock_show_detail.assert_awaited_once_with(
                mock_call,
                10,
                mock_bot,
                user_id=12345,
                page=1,
                back_cb="cat:mini:1",
                is_random=False
            )


if __name__ == "__main__":
    unittest.main()
