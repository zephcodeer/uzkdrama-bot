import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import database as db
import notifications

class TestRandomDorama(unittest.IsolatedAsyncioTestCase):
    """1. get_random_dorama() test suite."""

    async def test_get_random_dorama_returns_valid_item(self):
        result = await db.get_random_dorama()
        self.assertIsNotNone(result, "get_random_dorama should return a dorama dictionary")
        self.assertIsInstance(result, dict)
        self.assertIn("id", result)
        self.assertIn("title", result)
        self.assertIn("total_episodes", result)
        self.assertGreater(result["total_episodes"], 0, "total_episodes must be > 0")
        self.assertIn("poster_url", result)
        self.assertTrue(bool(result["poster_url"]), "poster_url should not be empty")

    async def test_get_random_dorama_empty_result(self):
        class MockEmptyCursor:
            async def fetchone(self):
                return None
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc, tb):
                pass

        class MockDbConn:
            row_factory = None
            def execute(self, sql):
                return MockEmptyCursor()
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc, tb):
                pass

        with patch("aiosqlite.connect", return_value=MockDbConn()):
            res = await db.get_random_dorama()
            self.assertIsNone(res, "Should return None when query returns no rows")


class TestCategoryQueries(unittest.IsolatedAsyncioTestCase):
    """2. get_doramas_by_category('mini') and ('movies') test suite."""

    async def test_get_doramas_by_category_mini(self):
        title, items = await db.get_doramas_by_category("mini", limit=10, offset=0)
        self.assertIn("Mini", title, "Category title should contain 'Mini'")
        self.assertGreater(len(items), 0, "Should return mini-doramas")
        self.assertLessEqual(len(items), 10, "Should respect limit=10")
        for item in items:
            self.assertGreaterEqual(
                item["total_episodes"], 2, 
                f"Mini dorama '{item['title']}' must have at least 2 episodes, got {item['total_episodes']}"
            )
            if item.get("category") not in ("mini_drama", "duanju"):
                self.assertLessEqual(
                    item["total_episodes"], 12, 
                    f"Mini dorama '{item['title']}' must have at most 12 episodes, got {item['total_episodes']}"
                )

    async def test_get_doramas_by_category_movies(self):
        title, items = await db.get_doramas_by_category("movies", limit=10, offset=0)
        self.assertIn("Filmlar", title, "Category title should contain 'Filmlar'")
        self.assertGreater(len(items), 0, "Should return movies")
        self.assertLessEqual(len(items), 10, "Should respect limit=10")
        for item in items:
            self.assertEqual(
                item["total_episodes"], 1, 
                f"Movie '{item['title']}' must have total_episodes == 1, got {item['total_episodes']}"
            )

    async def test_category_pagination(self):
        _, page1 = await db.get_doramas_by_category("mini", limit=3, offset=0)
        _, page2 = await db.get_doramas_by_category("mini", limit=3, offset=3)
        self.assertEqual(len(page1), 3)
        self.assertEqual(len(page2), 3)
        p1_ids = [d["id"] for d in page1]
        p2_ids = [d["id"] for d in page2]
        self.assertEqual(len(set(p1_ids).intersection(set(p2_ids))), 0, "Paginated pages should not overlap")


class TestSubscriptions(unittest.IsolatedAsyncioTestCase):
    """3. toggle_subscription and get_dorama_subscribers test suite."""

    TEST_USER_ID = 999888111
    TEST_DORAMA_ID = 1

    async def asyncSetUp(self):
        # Ensure clean state before each test
        subs = await db.get_dorama_subscribers(self.TEST_DORAMA_ID)
        if self.TEST_USER_ID in subs:
            await db.toggle_subscription(self.TEST_USER_ID, self.TEST_DORAMA_ID)

    async def asyncTearDown(self):
        # Clean up after each test
        subs = await db.get_dorama_subscribers(self.TEST_DORAMA_ID)
        if self.TEST_USER_ID in subs:
            await db.toggle_subscription(self.TEST_USER_ID, self.TEST_DORAMA_ID)

    async def test_toggle_subscription_lifecycle(self):
        # 1. Initially not subscribed
        initial_subs = await db.get_dorama_subscribers(self.TEST_DORAMA_ID)
        self.assertNotIn(self.TEST_USER_ID, initial_subs)

        # 2. Toggle subscription on -> returns True
        is_sub = await db.toggle_subscription(self.TEST_USER_ID, self.TEST_DORAMA_ID)
        self.assertTrue(is_sub, "First toggle should subscribe (return True)")

        after_sub = await db.get_dorama_subscribers(self.TEST_DORAMA_ID)
        self.assertIn(self.TEST_USER_ID, after_sub, "User ID should now be in subscribers list")

        # 3. Toggle subscription off -> returns False
        is_sub_again = await db.toggle_subscription(self.TEST_USER_ID, self.TEST_DORAMA_ID)
        self.assertFalse(is_sub_again, "Second toggle should unsubscribe (return False)")

        after_unsub = await db.get_dorama_subscribers(self.TEST_DORAMA_ID)
        self.assertNotIn(self.TEST_USER_ID, after_unsub, "User ID should be removed from subscribers list")


class TestBookmarks(unittest.IsolatedAsyncioTestCase):
    """4. toggle_bookmark and get_user_bookmarks test suite."""

    TEST_USER_ID = 999888222
    TEST_DORAMA_ID = 1

    async def asyncSetUp(self):
        # Clean state before test
        bms = await db.get_user_bookmarks(self.TEST_USER_ID)
        if any(d["id"] == self.TEST_DORAMA_ID for d in bms):
            await db.toggle_bookmark(self.TEST_USER_ID, self.TEST_DORAMA_ID)

    async def asyncTearDown(self):
        # Clean state after test
        bms = await db.get_user_bookmarks(self.TEST_USER_ID)
        if any(d["id"] == self.TEST_DORAMA_ID for d in bms):
            await db.toggle_bookmark(self.TEST_USER_ID, self.TEST_DORAMA_ID)

    async def test_toggle_bookmark_lifecycle(self):
        # 1. Initially no bookmarks
        initial_bms = await db.get_user_bookmarks(self.TEST_USER_ID)
        self.assertFalse(any(d["id"] == self.TEST_DORAMA_ID for d in initial_bms))

        # 2. Toggle bookmark on -> returns True
        added = await db.toggle_bookmark(self.TEST_USER_ID, self.TEST_DORAMA_ID)
        self.assertTrue(added, "First toggle should add to bookmarks (return True)")

        after_bms = await db.get_user_bookmarks(self.TEST_USER_ID)
        matched = [d for d in after_bms if d["id"] == self.TEST_DORAMA_ID]
        self.assertEqual(len(matched), 1, "Bookmark should be present in user bookmarks")
        self.assertEqual(matched[0]["id"], self.TEST_DORAMA_ID)

        # 3. Toggle bookmark off -> returns False
        removed = await db.toggle_bookmark(self.TEST_USER_ID, self.TEST_DORAMA_ID)
        self.assertFalse(removed, "Second toggle should remove from bookmarks (return False)")

        final_bms = await db.get_user_bookmarks(self.TEST_USER_ID)
        self.assertFalse(any(d["id"] == self.TEST_DORAMA_ID for d in final_bms))


from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError

class TestNotificationFloodLimit(unittest.IsolatedAsyncioTestCase):
    """5. Notification engine flood-limit simulation (mock rate limiter)."""

    async def test_notify_subscribers_rate_limiting_and_stats(self):
        """Simulates 5 subscribers: verifies 0.04s safe delay (25 msgs/s) and delivery."""
        test_dorama_id = 100
        test_subscribers = [101, 102, 103, 104, 105]
        mock_dorama = {
            "id": test_dorama_id,
            "title": "Qahramon",
            "code": 100,
            "poster_url": "https://example.com/poster.jpg",
            "total_episodes": 16,
        }

        slept_durations = []
        async def fake_sleep(duration):
            slept_durations.append(duration)

        mock_bot = MagicMock()
        mock_bot.send_photo = AsyncMock()
        mock_bot.send_message = AsyncMock()

        with patch.object(db, "get_dorama_subscribers", AsyncMock(return_value=test_subscribers)), \
             patch.object(db, "get_dorama_by_id", AsyncMock(return_value=mock_dorama)), \
             patch("asyncio.sleep", side_effect=fake_sleep):

            sent = await notifications.notify_subscribers_async(test_dorama_id, [5], bot=mock_bot)
            self.assertEqual(sent, 5, "All 5 subscribers should have received the notification")
            self.assertEqual(mock_bot.send_photo.await_count, 5, "send_photo must be called 5 times")
            # Verify 0.04s delay was called for each subscriber to enforce 25 msgs/s rate limit
            rate_limit_sleeps = [s for s in slept_durations if abs(s - 0.04) < 1e-4]
            self.assertEqual(
                len(rate_limit_sleeps), 5,
                f"Rate limiter must sleep 0.04s for each recipient (called {len(rate_limit_sleeps)} times)"
            )

    async def test_notify_subscribers_flood_wait_429_handling(self):
        """Simulates Telegram Flood-Wait (TelegramRetryAfter) and verifies retry_after + 1 sleep."""
        test_dorama_id = 100
        test_subscribers = [201, 202]
        mock_dorama = {
            "id": test_dorama_id,
            "title": "Qahramon",
            "code": 100,
            "poster_url": "https://example.com/poster.jpg",
            "total_episodes": 16,
        }

        slept_durations = []
        async def fake_sleep(duration):
            slept_durations.append(duration)

        mock_bot = MagicMock()
        
        # User 201: 1st attempt triggers TelegramRetryAfter(retry_after=3), 2nd attempt succeeds
        # User 202: triggers TelegramForbiddenError (blocked)
        retry_err = TelegramRetryAfter(method=None, message="Too Many Requests", retry_after=3)
        blocked_err = TelegramForbiddenError(method=None, message="Bot was blocked by user")
        
        mock_bot.send_photo = AsyncMock(side_effect=[retry_err, None, blocked_err])
        mock_bot.send_message = AsyncMock()

        with patch.object(db, "get_dorama_subscribers", AsyncMock(return_value=test_subscribers)), \
             patch.object(db, "get_dorama_by_id", AsyncMock(return_value=mock_dorama)), \
             patch("asyncio.sleep", side_effect=fake_sleep):

            sent = await notifications.notify_subscribers_async(test_dorama_id, [5], bot=mock_bot)
            self.assertEqual(sent, 1, "Only 1 message should be counted as successfully sent (1 retry succeeded, 1 blocked)")
            # Verify retry_after + 1 = 4 seconds was slept
            flood_sleeps = [s for s in slept_durations if s == 4]
            self.assertEqual(len(flood_sleeps), 1, "Must sleep retry_after + 1 upon TelegramRetryAfter")

    async def test_notify_subscribers_empty_or_missing(self):
        """Verifies 0 messages sent when no subscribers or missing dorama."""
        with patch.object(db, "get_dorama_subscribers", AsyncMock(return_value=[])):
            sent = await notifications.notify_subscribers_async(9999, [1])
            self.assertEqual(sent, 0)

        with patch.object(db, "get_dorama_subscribers", AsyncMock(return_value=[123])), \
             patch.object(db, "get_dorama_by_id", AsyncMock(return_value=None)):
            sent = await notifications.notify_subscribers_async(9999, [1])
            self.assertEqual(sent, 0)


if __name__ == "__main__":
    unittest.main()
