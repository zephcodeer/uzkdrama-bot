import asyncio
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

import database as db  # noqa: E402


async def main():
    # 1. Code 486: Imperatritsaning ikkinchi nikohi — Episode 5 -> 5323
    d486 = await db.get_dorama_by_code(486)
    assert d486, "Code 486 not found"
    await db.add_episode(
        dorama_id=d486["id"],
        episode_number=5,
        channel_message_id=5323,
        file_size=488827604,
        quality="1080p",
    )
    print(f"Added Code 486 ({d486['title']}) Ep 5 -> msg 5323 (1080p)")

    # 2. Code 481: Bechoralar — Episode 51 -> 5324
    d481 = await db.get_dorama_by_code(481)
    assert d481, "Code 481 not found"
    await db.add_episode(
        dorama_id=d481["id"],
        episode_number=51,
        channel_message_id=5324,
        file_size=207906724,
        quality="720p",
    )
    print(f"Added Code 481 ({d481['title']}) Ep 51 -> msg 5324 (720p)")

    # 3. Code 502: Nanyang jumbog'i — Episode 11 -> 5325
    d502 = await db.get_dorama_by_code(502)
    assert d502, "Code 502 not found"
    await db.add_episode(
        dorama_id=d502["id"],
        episode_number=11,
        channel_message_id=5325,
        file_size=725984667,
        quality="1080p",
    )
    print(f"Added Code 502 ({d502['title']}) Ep 11 -> msg 5325 (1080p)")

    # Restore planned total_episodes=33 and Ongoing status for Code 502
    # (db.add_episode recalculates total_episodes to COUNT(*) of uploaded rows)
    conn = sqlite3.connect("doramas.db")
    conn.execute(
        "UPDATE doramas SET total_episodes = 33, status = 'Ongoing' WHERE id = ?",
        (d502["id"],),
    )
    conn.commit()
    rows = conn.execute(
        "SELECT code, title, total_episodes, status FROM doramas WHERE code IN (486, 481, 502) ORDER BY code"
    ).fetchall()
    conn.close()
    print("Updated doramas:", rows)


if __name__ == "__main__":
    asyncio.run(main())
