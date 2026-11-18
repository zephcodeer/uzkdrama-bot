import asyncio
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

import database as db  # noqa: E402


async def main():
    d168 = await db.get_dorama_by_code(168)
    assert d168, "Code 168 not found"
    await db.add_episode(
        dorama_id=d168["id"],
        episode_number=10,
        channel_message_id=5382,
        file_size=0,
        quality="720p",
    )
    conn = sqlite3.connect("doramas.db")
    conn.execute(
        "UPDATE doramas SET total_episodes = 16, status = 'Ongoing' WHERE code = 168"
    )
    conn.commit()
    rows = conn.execute(
        """
        SELECT d.code, d.title, d.poster_url, d.total_episodes, d.status, COUNT(e.id) as eps
        FROM doramas d
        LEFT JOIN episodes e ON e.dorama_id = d.id
        WHERE d.code IN (101, 168, 355, 483, 501)
        GROUP BY d.id
        ORDER BY d.code
    """
    ).fetchall()
    conn.close()
    for r in rows:
        print(r)


if __name__ == "__main__":
    asyncio.run(main())
