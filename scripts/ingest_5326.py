import asyncio
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

import database as db  # noqa: E402


async def main():
    d486 = await db.get_dorama_by_code(486)
    assert d486, "Code 486 not found"
    await db.add_episode(
        dorama_id=d486["id"],
        episode_number=6,
        channel_message_id=5326,
        file_size=1616091624,
        quality="1080p",
    )
    conn = sqlite3.connect("doramas.db")
    row = conn.execute(
        "SELECT code, title, total_episodes, status FROM doramas WHERE code = 486"
    ).fetchone()
    conn.close()
    print("Added Code 486 Ep 6 -> msg 5326 (1080p). Row:", row)


if __name__ == "__main__":
    asyncio.run(main())
