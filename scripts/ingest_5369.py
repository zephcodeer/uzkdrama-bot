import asyncio
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

import database as db  # noqa: E402


async def main():
    d241 = await db.get_dorama_by_code(241)
    assert d241, "Code 241 not found"

    await db.add_episode(
        dorama_id=d241["id"],
        episode_number=9,
        channel_message_id=5369,
        file_size=2843034257,
        quality="1080p",
    )
    print("Updated Code 241 Ep 9 -> msg 5369 (1080p)")

    conn = sqlite3.connect("doramas.db")
    cur = conn.cursor()

    row = cur.execute(
        "SELECT aliases FROM doramas WHERE id = ?", (d241["id"],)
    ).fetchone()
    current_aliases = row[0] or ""
    new_aliases = current_aliases
    for extra in [
        "Sendan o'zga bir sevgi",
        "Sendan ozga bir sevgi",
        "Sendan özga bir sevgi",
        "Sendan o‘zga bir sevgi",
    ]:
        if extra.lower() not in current_aliases.lower():
            new_aliases += f", {extra}"

    cur.execute(
        "UPDATE doramas SET total_episodes = 14, status = 'Ongoing', aliases = ? WHERE id = ?",
        (new_aliases, d241["id"]),
    )
    conn.commit()

    updated = cur.execute(
        "SELECT code, title, total_episodes, status, aliases FROM doramas WHERE code = 241"
    ).fetchone()
    conn.close()
    print("Updated Code 241 row:", updated)


if __name__ == "__main__":
    asyncio.run(main())
