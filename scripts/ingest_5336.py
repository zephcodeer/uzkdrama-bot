import asyncio
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

import database as db  # noqa: E402


async def main():
    d483 = await db.get_dorama_by_code(483)
    assert d483, "Code 483 not found"

    await db.add_episode(
        dorama_id=d483["id"],
        episode_number=7,
        channel_message_id=5336,
        file_size=1199069861,
        quality="720p",
    )
    print(f"Added Code 483 Ep 7 -> msg 5336 (720p)")

    conn = sqlite3.connect("doramas.db")
    cur = conn.cursor()

    # Update aliases if needed and restore planned total_episodes=12
    row = cur.execute(
        "SELECT aliases FROM doramas WHERE id = ?", (d483["id"],)
    ).fetchone()
    current_aliases = row[0] or ""
    new_aliases = current_aliases
    for extra in ["Niqob ostidagi sevgi", "Yashirin niqob"]:
        if extra.lower() not in current_aliases.lower():
            new_aliases += f", {extra}"

    cur.execute(
        "UPDATE doramas SET total_episodes = 12, status = 'Ongoing', aliases = ? WHERE id = ?",
        (new_aliases, d483["id"]),
    )
    conn.commit()

    updated = cur.execute(
        "SELECT code, title, total_episodes, status, aliases FROM doramas WHERE code = 483"
    ).fetchone()
    conn.close()
    print("Updated Code 483 row:", updated)


if __name__ == "__main__":
    asyncio.run(main())
