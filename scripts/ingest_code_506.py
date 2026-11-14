import asyncio
from datetime import datetime
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

import database as db  # noqa: E402


async def main():
    conn = sqlite3.connect("doramas.db")
    cur = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. Update Code 504 with series_group and 1-fasl title
    cur.execute(
        """
        UPDATE doramas
        SET title = 'Mening azizim 1-fasl (My Dearest)',
            series_group = 'my-dearest',
            aliases = aliases || ', Mening azizim 1, Mening azizim 1-fasl'
        WHERE code = 504
    """
    )

    # 2. Add Code 506 (id=406)
    ex_506 = cur.execute(
        "SELECT id, code, title FROM doramas WHERE code = 506"
    ).fetchone()
    if not ex_506:
        cur.execute(
            """
            INSERT INTO doramas (
                id, code, title, slug, genre, year, description, poster_url,
                total_episodes, views, created_at, status, country, actors, category, aliases, series_group
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                406,
                506,
                "Mening azizim 2-fasl (My Dearest Season 2)",
                "mening-azizim-2-fasl",
                "Tarixiy, Romantika, Melodrama, Jangari",
                2023,
                "Urush girdobida ayrilgan Li Jan Xyon va Yu Gil Chonning taqdiri yanada og‘ir sinovlarga duch keladi. Sin imperiyasining asirlar lageridagi shafqatsiz sharoitlar va yangi to‘siqlarga qaramay, ularning so‘nmas muhabbati va erkinlik uchun kurashi davom etadi.",
                "posters/code_506.jpg",
                11,
                0,
                now_str,
                "Tugallangan (Completed)",
                "Janubiy Koreya",
                "Namkoong Min (Namgung Min), Ahn Eun-jin (An In Jin), Lee Hak-joo, Lee Da-in",
                "korea",
                "Mening azizim 2, Mening azizim 2-fasl, Mening azizim 2 fasl, My Dearest 2, My Dearest Season 2, My Dearest Part 2, Lovers 2, 연인 2, Namkoong Min",
                "my-dearest",
            ),
        )
        print("Created Code 506 (id=406)")
    conn.commit()
    conn.close()

    # 3. Add episodes 1..11 for Code 506
    episodes_506 = [
        (1, 5358, 870035902, "1080p"),
        (2, 5359, 822174876, "1080p"),
        (3, 5360, 781336097, "1080p"),
        (4, 5361, 802068690, "1080p"),
        (5, 5362, 635844929, "1080p"),
        (6, 5363, 576488845, "1080p"),
        (7, 5364, 659429905, "1080p"),
        (8, 5365, 624604050, "1080p"),
        (9, 5366, 585427569, "1080p"),
        (10, 5367, 573434603, "1080p"),
        (11, 5368, 866350223, "1080p"),
    ]
    for ep_num, msg_id, fsize, qual in episodes_506:
        await db.add_episode(
            dorama_id=406,
            episode_number=ep_num,
            channel_message_id=msg_id,
            file_size=fsize,
            quality=qual,
        )
        print(f"Added Ep {ep_num} -> msg {msg_id} ({qual})")

    # Restore planned total_episodes and status
    conn = sqlite3.connect("doramas.db")
    conn.execute(
        "UPDATE doramas SET total_episodes = 11, status = 'Tugallangan (Completed)' WHERE id = 406"
    )
    conn.commit()
    row = conn.execute(
        "SELECT code, title, total_episodes, status, series_group FROM doramas WHERE code IN (504, 506) ORDER BY code"
    ).fetchall()
    print("Dorama states:", row)
    conn.close()


if __name__ == "__main__":
    asyncio.run(main())
