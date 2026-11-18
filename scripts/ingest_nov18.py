import asyncio
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

import database as db  # noqa: E402


async def main():
    items = [
        # (code, ep_num, msg_id, quality)
        (501, 4, 5372, "720p"),   # Mening qo'shnim Franchesko Ep 4
        (101, 9, 5374, "720p"),   # Doktor X Ep 9 (updated msg_id)
        (101, 10, 5375, "720p"),  # Doktor X Ep 10
        (168, 9, 5376, "720p"),   # 100 kunlik yolg'on Ep 9
        (355, 11, 5377, "720p"),  # Choson nikoh agentligi Ep 11
        (355, 12, 5378, "720p"),  # Choson nikoh agentligi Ep 12
        (483, 8, 5379, "720p"),   # Mening aybdor insonim Ep 8
        (483, 9, 5380, "720p"),   # Mening aybdor insonim Ep 9
        (483, 10, 5381, "720p"),  # Mening aybdor insonim Ep 10
    ]

    cache = {}
    for code, ep_num, msg_id, qual in items:
        if code not in cache:
            d = await db.get_dorama_by_code(code)
            assert d, f"Code {code} not found"
            cache[code] = d
        d = cache[code]
        await db.add_episode(
            dorama_id=d["id"],
            episode_number=ep_num,
            channel_message_id=msg_id,
            file_size=0,
            quality=qual,
        )
        print(f"Ingested Code {code} ({d['title']}) Ep {ep_num} -> msg {msg_id}")

    # Restore planned total_episodes / status and update Code 498 (33 eps, Xitoy)
    conn = sqlite3.connect("doramas.db")
    cur = conn.cursor()
    cur.execute(
        "UPDATE doramas SET total_episodes = 4, status = 'Ongoing' WHERE code = 501"
    )
    cur.execute(
        "UPDATE doramas SET total_episodes = 10, status = 'Ongoing' WHERE code = 101"
    )
    cur.execute(
        "UPDATE doramas SET total_episodes = 16, status = 'Ongoing' WHERE code = 168"
    )
    cur.execute(
        "UPDATE doramas SET total_episodes = 16, status = 'Ongoing' WHERE code = 355"
    )
    cur.execute(
        "UPDATE doramas SET total_episodes = 12, status = 'Ongoing' WHERE code = 483"
    )
    cur.execute(
        "UPDATE doramas SET total_episodes = 33, country = 'Xitoy', category = 'china', status = 'Ongoing' WHERE code = 498"
    )
    conn.commit()

    rows = cur.execute(
        """
        SELECT code, title, total_episodes, status, country, category
        FROM doramas
        WHERE code IN (101, 168, 355, 483, 498, 501)
        ORDER BY code
    """
    ).fetchall()
    conn.close()

    print("\n=== VERIFIED DORAMAS ===")
    for r in rows:
        print(r)


if __name__ == "__main__":
    asyncio.run(main())
