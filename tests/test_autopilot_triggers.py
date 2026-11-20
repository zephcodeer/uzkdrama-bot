import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
import aiosqlite

BASE_DIR = Path("E:/Agent/Drama Bot")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "scripts"))

def test_triggers():
    async def _async_test():
        import autopilot_donor_listener as adl

        mock_invalidate = MagicMock()
        mock_notify = AsyncMock(return_value=1)

        # Use in-memory db
        async with aiosqlite.connect(":memory:") as test_db:
            await test_db.execute("""
                CREATE TABLE doramas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code INTEGER UNIQUE,
                    title TEXT,
                    slug TEXT UNIQUE,
                    status TEXT,
                    country TEXT,
                    total_episodes INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    category TEXT
                );
            """)
            await test_db.execute("""
                CREATE TABLE episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dorama_id INTEGER,
                    episode_number INTEGER,
                    channel_message_id INTEGER,
                    quality TEXT,
                    file_size INTEGER,
                    UNIQUE(dorama_id, episode_number)
                );
            """)
            await test_db.execute("INSERT INTO doramas (id, code, title, slug) VALUES (9999, 9999, 'Test Dorama', 'test-dorama');")
            await test_db.commit()

            # Patch DB_PATH to point to our test DB connection or wrap aiosqlite.connect
            class MockConnectContext:
                async def __aenter__(self):
                    return test_db
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass

            with patch("database.invalidate_search_cache", mock_invalidate), \
                 patch("notifications.notify_subscribers_async", mock_notify), \
                 patch("autopilot_donor_listener.notify_subscribers_async", mock_notify), \
                 patch("aiosqlite.connect", return_value=MockConnectContext()):

                print("Executing ingest_episodes_to_db...")
                await adl.ingest_episodes_to_db(
                    dorama_id=9999,
                    ep_list=[1, 2],
                    storage_msg_id=12345,
                    quality="1080p",
                    file_size=500000000
                )

                # Allow background tasks to run
                if adl._BACKGROUND_TASKS:
                    await asyncio.gather(*adl._BACKGROUND_TASKS)

                assert mock_invalidate.called, "database.invalidate_search_cache was NOT called!"
                print("[PASS] database.invalidate_search_cache was successfully called!")

                assert mock_notify.called, "notify_subscribers_async was NOT called!"
                call_args = mock_notify.call_args
                print(f"[PASS] notify_subscribers_async was successfully called with args: {call_args}")
                assert call_args[0] == (9999, [1, 2], "1080p"), f"Unexpected args: {call_args}"

        print("[ALL TRIGGERS VERIFIED SUCCESSFULLY]")

    asyncio.run(_async_test())

if __name__ == "__main__":
    test_triggers()
