import asyncio
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

import database as db  # noqa: E402


async def main():
    conn = sqlite3.connect("doramas.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT id, code, title, total_episodes, status FROM doramas WHERE title LIKE '%daha%' OR aliases LIKE '%daha%'"
    ).fetchall()
    print("Matching Daha 17:", [dict(r) for r in rows])
    assert len(rows) == 1, f"Expected 1 match for Daha 17, got {len(rows)}"
    d = dict(rows[0])

    existing_eps = cur.execute(
        "SELECT MAX(episode_number), COUNT(*) FROM episodes WHERE dorama_id = ?",
        (d["id"],),
    ).fetchone()
    print(f"Current episodes: max={existing_eps[0]}, count={existing_eps[1]}")
    conn.close()

    for ep_num, msg_id in [(47, 5383), (48, 5384), (49, 5385), (50, 5386)]:
        await db.add_episode(
            dorama_id=d["id"],
            episode_number=ep_num,
            channel_message_id=msg_id,
            file_size=0,
            quality="720p",
        )
        print(f"Added Code {d['code']} ({d['title']}) Ep {ep_num} -> msg {msg_id}")

    conn = sqlite3.connect("doramas.db")
    new_total = max(d["total_episodes"] or 0, 50)
    conn.execute(
        "UPDATE doramas SET total_episodes = ?, status = ? WHERE id = ?",
        (new_total, d["status"], d["id"]),
    )
    conn.commit()
    row = conn.execute(
        "SELECT code, title, total_episodes, status FROM doramas WHERE id = ?",
        (d["id"],),
    ).fetchone()
    conn.close()
    print("Verified row:", row)


if __name__ == "__main__":
    asyncio.run(main())
