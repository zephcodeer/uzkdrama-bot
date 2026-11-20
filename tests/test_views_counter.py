import asyncio
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch, MagicMock

# Ensure project root is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import aiosqlite
import bot
import database as db
import keyboards as kb


class ViewsCounterTests(unittest.IsolatedAsyncioTestCase):
    """
    Test suite for Dorama Views Counter, Debouncing, and Git-Reset Persistence.
    Verifies:
      1. Views increment properly when a user opens dorama detail.
      2. Debouncing works: tapping dorama detail 5 times within 1 hour increments view count exactly ONCE.
      3. Paginating episodes or switching seasons does NOT inflate view count.
      4. Views are persistent across git resets or stored safely in userdata.db.
    """

    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.old_db_path = db.DB_PATH
        self.old_user_db_path = db.USER_DB_PATH

        db.DB_PATH = Path(self.tmp.name) / "doramas.db"
        db.USER_DB_PATH = Path(self.tmp.name) / "userdata.db"

        # Initialize fresh schema
        await db.init_db()
        db.reset_views_debounce()

        # Seed sample doramas in catalog
        async with aiosqlite.connect(db.DB_PATH) as conn:
            await conn.execute("""
                INSERT INTO doramas (id, code, title, slug, genre, year, total_episodes, views, status, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (1, 101, 'Vincenzo', 'vincenzo', 'Kriminal, Drama', 2021, 20, 0, 'Tugallangan', 'Vincenzo Cassano advokat hikoyasi'))
            await conn.execute("""
                INSERT INTO doramas (id, code, title, slug, genre, year, total_episodes, views, status, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (2, 102, 'Squid Game', 'squid-game', 'Thriller, Omon qolish', 2021, 9, 0, 'Tugallangan', "Halokatli omon qolish o'yini"))
            # Seed 25 episodes for dorama 1 to test pagination
            for ep in range(1, 26):
                await conn.execute("""
                    INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
                    VALUES (1, ?, ?, '720p')
                """, (ep, 1000 + ep))
            await conn.commit()

    async def asyncTearDown(self):
        db.reset_views_debounce()
        db.DB_PATH = self.old_db_path
        db.USER_DB_PATH = self.old_user_db_path
        self.tmp.cleanup()

    # -------------------------------------------------------------------------
    # 1. Unit Tests: Increment & Debouncing
    # -------------------------------------------------------------------------

    async def test_increment_views_basic(self):
        """Views should increment by 1 on first view and sync across both databases."""
        self.assertEqual(await db.get_dorama_views(1), 0)

        # First increment
        result = await db.increment_views(1, user_id=1001)
        self.assertTrue(result, "First view by user must return True")

        # Check view count via helper
        views = await db.get_dorama_views(1)
        self.assertEqual(views, 1, "Views count must be 1")

        # Verify userdata.db storage directly
        async with aiosqlite.connect(db.USER_DB_PATH) as udb:
            async with udb.execute("SELECT views FROM dorama_views WHERE dorama_id = 1") as cur:
                row = await cur.fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], 1)

        # Verify doramas.db sync directly
        async with aiosqlite.connect(db.DB_PATH) as cdb:
            async with cdb.execute("SELECT views FROM doramas WHERE id = 1") as cur:
                row = await cur.fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], 1)

    async def test_debouncing_five_taps_within_one_hour(self):
        """Tapping dorama detail 5 times within 1 hour increments view count exactly ONCE."""
        user_id = 2002
        dorama_id = 1

        # Tap 1: Fresh view -> increments
        first_call = await db.increment_views(dorama_id, user_id=user_id)
        self.assertTrue(first_call, "First tap must count as a valid view")

        # Taps 2 to 5: Immediate subsequent taps within 1 hour -> debounced
        for tap in range(2, 6):
            subsequent_call = await db.increment_views(dorama_id, user_id=user_id)
            self.assertFalse(subsequent_call, f"Tap #{tap} within 1 hour must be debounced (return False)")

        # Verify views count remains strictly 1
        views = await db.get_dorama_views(dorama_id)
        self.assertEqual(views, 1, "5 taps within 1 hour must increment view count exactly ONCE!")

    async def test_debounce_different_users_are_independent(self):
        """Different users viewing the same dorama should each increment views independently."""
        dorama_id = 1

        res1 = await db.increment_views(dorama_id, user_id=3001)
        self.assertTrue(res1)
        self.assertEqual(await db.get_dorama_views(dorama_id), 1)

        res2 = await db.increment_views(dorama_id, user_id=3002)
        self.assertTrue(res2)
        self.assertEqual(await db.get_dorama_views(dorama_id), 2)

        # User 3001 taps again -> debounced
        res1_again = await db.increment_views(dorama_id, user_id=3001)
        self.assertFalse(res1_again)
        self.assertEqual(await db.get_dorama_views(dorama_id), 2)

    async def test_debounce_different_doramas_for_same_user(self):
        """The same user viewing different doramas should increment each dorama once."""
        user_id = 4001

        res_d1 = await db.increment_views(1, user_id=user_id)
        res_d2 = await db.increment_views(2, user_id=user_id)

        self.assertTrue(res_d1)
        self.assertTrue(res_d2)
        self.assertEqual(await db.get_dorama_views(1), 1)
        self.assertEqual(await db.get_dorama_views(2), 1)

    async def test_debounce_expires_after_one_hour(self):
        """After 1 hour has elapsed, a new view from the same user should be counted."""
        user_id = 5001
        dorama_id = 1
        base_time = 1700000000.0

        with patch("time.time", return_value=base_time):
            res1 = await db.increment_views(dorama_id, user_id=user_id)
            self.assertTrue(res1)
            self.assertEqual(await db.get_dorama_views(dorama_id), 1)

        # 30 minutes later: still debounced
        with patch("time.time", return_value=base_time + 1800):
            res2 = await db.increment_views(dorama_id, user_id=user_id)
            self.assertFalse(res2)
            self.assertEqual(await db.get_dorama_views(dorama_id), 1)

        # 1 hour and 1 second later: debounce window expired -> increments!
        with patch("time.time", return_value=base_time + 3601):
            res3 = await db.increment_views(dorama_id, user_id=user_id)
            self.assertTrue(res3, "View after 1 hour must be accepted")
            self.assertEqual(await db.get_dorama_views(dorama_id), 2)

    async def test_debounce_survives_bot_restart_via_userdata_db(self):
        """Even if in-memory debounce cache is wiped (bot restart), userdata.db enforces debounce."""
        user_id = 6001
        dorama_id = 1

        # 1st view
        res = await db.increment_views(dorama_id, user_id=user_id)
        self.assertTrue(res)
        self.assertEqual(await db.get_dorama_views(dorama_id), 1)

        # Simulate bot crash/restart by clearing memory cache
        db.reset_views_debounce()

        # 2nd view right away: memory cache empty, but userdata.db catches it
        res_after_restart = await db.increment_views(dorama_id, user_id=user_id)
        self.assertFalse(res_after_restart, "Debounce must be enforced from persistent userdata.db even after restart")
        self.assertEqual(await db.get_dorama_views(dorama_id), 1)

    # -------------------------------------------------------------------------
    # 2. Integration Tests: show_dorama_detail, Pagination, Seasons
    # -------------------------------------------------------------------------

    async def test_show_dorama_detail_increments_views_on_open(self):
        """Opening dorama detail card via show_dorama_detail increments views properly."""
        user_id = 7001
        dorama_id = 1

        mock_bot = SimpleNamespace(
            get_me=AsyncMock(return_value=SimpleNamespace(username="test_dorama_bot")),
            send_message=AsyncMock(),
            send_photo=AsyncMock()
        )
        mock_msg = SimpleNamespace(
            photo=None,
            caption=None,
            edit_caption=AsyncMock(),
            edit_media=AsyncMock(),
            answer=AsyncMock(),
            delete=AsyncMock()
        )
        mock_target = SimpleNamespace(
            message=mock_msg,
            from_user=SimpleNamespace(id=user_id),
            answer=AsyncMock(),
            answer_photo=AsyncMock()
        )

        with patch.object(bot, "is_user_channel_member", AsyncMock(return_value=True)):
            # User opens dorama detail (page=0)
            await bot.show_dorama_detail(
                target=mock_target,
                dorama_id=dorama_id,
                bot=mock_bot,
                user_id=user_id,
                page=0
            )
            # Yield to let background create_task complete
            await asyncio.sleep(0.05)

            self.assertEqual(await db.get_dorama_views(dorama_id), 1)

    async def test_show_dorama_detail_five_taps_increments_once(self):
        """User tapping dorama detail 5 times rapidly triggers exactly 1 view increment."""
        user_id = 8001
        dorama_id = 1

        mock_bot = SimpleNamespace(
            get_me=AsyncMock(return_value=SimpleNamespace(username="test_dorama_bot")),
            send_message=AsyncMock(),
            send_photo=AsyncMock()
        )
        mock_msg = SimpleNamespace(
            photo=None,
            caption=None,
            edit_caption=AsyncMock(),
            edit_media=AsyncMock(),
            answer=AsyncMock(),
            delete=AsyncMock()
        )
        mock_target = SimpleNamespace(
            message=mock_msg,
            from_user=SimpleNamespace(id=user_id),
            answer=AsyncMock(),
            answer_photo=AsyncMock()
        )

        with patch.object(bot, "is_user_channel_member", AsyncMock(return_value=True)):
            for _ in range(5):
                await bot.show_dorama_detail(
                    target=mock_target,
                    dorama_id=dorama_id,
                    bot=mock_bot,
                    user_id=user_id,
                    page=0
                )
            await asyncio.sleep(0.05)

            self.assertEqual(
                await db.get_dorama_views(dorama_id),
                1,
                "5 rapid detail card opens must only increment views once"
            )

    async def test_pagination_and_seasons_do_not_inflate_views(self):
        """Paginating episodes (page > 0) or switching seasons does NOT inflate view count."""
        user_id = 9001
        dorama_id = 1

        mock_bot = SimpleNamespace(
            get_me=AsyncMock(return_value=SimpleNamespace(username="test_dorama_bot")),
            send_message=AsyncMock(),
            send_photo=AsyncMock()
        )
        mock_msg = SimpleNamespace(
            photo=None,
            caption=None,
            edit_caption=AsyncMock(),
            edit_media=AsyncMock(),
            answer=AsyncMock(),
            delete=AsyncMock()
        )
        mock_target = SimpleNamespace(
            message=mock_msg,
            from_user=SimpleNamespace(id=user_id),
            answer=AsyncMock(),
            answer_photo=AsyncMock()
        )

        with patch.object(bot, "is_user_channel_member", AsyncMock(return_value=True)):
            # 1. User opens main detail page (page 0) -> views becomes 1
            await bot.show_dorama_detail(
                target=mock_target,
                dorama_id=dorama_id,
                bot=mock_bot,
                user_id=user_id,
                page=0
            )
            await asyncio.sleep(0.05)
            self.assertEqual(await db.get_dorama_views(dorama_id), 1)

            # 2. User paginates to page 1 (episodes 11-20)
            await bot.show_dorama_detail(
                target=mock_target,
                dorama_id=dorama_id,
                bot=mock_bot,
                user_id=user_id,
                page=1
            )
            await asyncio.sleep(0.05)
            self.assertEqual(
                await db.get_dorama_views(dorama_id),
                1,
                "Paginating to page 1 must NOT increment views!"
            )

            # 3. User paginates to page 2 (episodes 21-25)
            await bot.show_dorama_detail(
                target=mock_target,
                dorama_id=dorama_id,
                bot=mock_bot,
                user_id=user_id,
                page=2
            )
            await asyncio.sleep(0.05)
            self.assertEqual(
                await db.get_dorama_views(dorama_id),
                1,
                "Paginating to page 2 must NOT increment views!"
            )

            # 4. User navigates back to page 0 within debounce window
            await bot.show_dorama_detail(
                target=mock_target,
                dorama_id=dorama_id,
                bot=mock_bot,
                user_id=user_id,
                page=0
            )
            await asyncio.sleep(0.05)
            self.assertEqual(
                await db.get_dorama_views(dorama_id),
                1,
                "Returning to page 0 within 1 hour must NOT inflate view count!"
            )

    # -------------------------------------------------------------------------
    # 3. Persistence Across Git Resets & Database Sync
    # -------------------------------------------------------------------------

    async def test_views_persistent_across_git_resets_via_userdata_db(self):
        """
        Views are persistent across git resets:
        When doramas.db is wiped/overwritten by a git reset, sync_views_to_doramas_db
        restores the live view counts from indestructible userdata.db.
        """
        # Accumulate views in the system
        for u in range(101, 116):  # 15 views for dorama 1
            await db.increment_views(1, user_id=u)
        for u in range(201, 243):  # 42 views for dorama 2
            await db.increment_views(2, user_id=u)

        self.assertEqual(await db.get_dorama_views(1), 15)
        self.assertEqual(await db.get_dorama_views(2), 42)

        # SIMULATE GIT RESET --HARD:
        # doramas.db is overwritten by repository version where views = 0
        async with aiosqlite.connect(db.DB_PATH) as cdb:
            await cdb.execute("UPDATE doramas SET views = 0")
            await cdb.commit()

        # Confirm doramas.db was wiped
        async with aiosqlite.connect(db.DB_PATH) as cdb:
            async with cdb.execute("SELECT views FROM doramas WHERE id = 1") as cur:
                self.assertEqual((await cur.fetchone())[0], 0)
            async with cdb.execute("SELECT views FROM doramas WHERE id = 2") as cur:
                self.assertEqual((await cur.fetchone())[0], 0)

        # userdata.db is untouched (.gitignored) and holds 15 and 42
        async with aiosqlite.connect(db.USER_DB_PATH) as udb:
            async with udb.execute("SELECT views FROM dorama_views WHERE dorama_id = 1") as cur:
                self.assertEqual((await cur.fetchone())[0], 15)
            async with udb.execute("SELECT views FROM dorama_views WHERE dorama_id = 2") as cur:
                self.assertEqual((await cur.fetchone())[0], 42)

        # Run async sync
        await db.sync_views_to_doramas_db()

        # Verify doramas.db is completely restored
        async with aiosqlite.connect(db.DB_PATH) as cdb:
            async with cdb.execute("SELECT views FROM doramas WHERE id = 1") as cur:
                self.assertEqual((await cur.fetchone())[0], 15)
            async with cdb.execute("SELECT views FROM doramas WHERE id = 2") as cur:
                self.assertEqual((await cur.fetchone())[0], 42)

        # Now test synchronous recovery used in execute_git_update()
        async with aiosqlite.connect(db.DB_PATH) as cdb:
            await cdb.execute("UPDATE doramas SET views = 0")
            await cdb.commit()

        db.sync_views_to_doramas_db_sync()

        async with aiosqlite.connect(db.DB_PATH) as cdb:
            async with cdb.execute("SELECT views FROM doramas WHERE id = 1") as cur:
                self.assertEqual((await cur.fetchone())[0], 15, "Sync restoration failed for dorama 1")
            async with cdb.execute("SELECT views FROM doramas WHERE id = 2") as cur:
                self.assertEqual((await cur.fetchone())[0], 42, "Sync restoration failed for dorama 2")

    async def test_get_stats_reflects_durable_userdata_views(self):
        """get_stats and get_admin_detailed_stats reflect views from userdata.db even if doramas.db is delayed."""
        await db.increment_views(1, user_id=9901)
        await db.increment_views(2, user_id=9902)

        stats = await db.get_stats()
        self.assertIn("total_views", stats)
        self.assertEqual(stats["total_views"], 2)

        admin_stats = await db.get_admin_detailed_stats()
        self.assertIn("total_views", admin_stats)
        self.assertEqual(admin_stats["total_views"], 2)


if __name__ == "__main__":
    unittest.main()
