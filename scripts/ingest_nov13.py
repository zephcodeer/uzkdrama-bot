import asyncio
from datetime import datetime
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

import database as db  # noqa: E402


async def main():
    conn = sqlite3.connect("doramas.db")
    cur = conn.cursor()

    existing = cur.execute(
        "SELECT id, code, title FROM doramas WHERE code = 503"
    ).fetchone()
    if not existing:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            """
            INSERT INTO doramas (
                id, code, title, slug, genre, year, description, poster_url,
                total_episodes, views, created_at, status, country, actors, category, aliases, series_group
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                403,
                503,
                "Ertaga ishda ko‘rishguncha (See You at Work Tomorrow!)",
                "ertaga-ishda-korishguncha",
                "Melodrama, Romantika, Komediya",
                2026,
                "Kundalik ofis muhiti, ish tashvishlari hamda xodimlar o‘rtasidagi murakkab, ammo samimiy munosabatlar haqidagi romantik komediya. Qahramonlar har kuni ishxonadagi qiyinchiliklar va charchoqlarga qaramay, bir-birlariga tayanch bo‘lib, kutilmagan sof muhabbat tuyg‘usini topadilar.",
                "posters/code_503.jpg",
                12,
                0,
                now_str,
                "Ongoing",
                "Janubiy Koreya",
                "Seo In-guk (So In Guk), Park Ji-hyun (Pak Ji Xyon)",
                "korea",
                "Ertaga ishda korishguncha, Ertaga ishda ko'rishguncha, Ertaga ishda ko‘rishguncha, Eraga ishda ko'rishguncha, Eraga ishda korishguncha, See You at Work Tomorrow, See You at Work Tomorrow!, 내일도 출근!, Seo In-guk, Park Ji-hyun, So In Guk",
                "",
            ),
        )
        conn.commit()
        print("Created new dorama row for Code 503 (id=403)")
    else:
        print("Dorama Code 503 already exists:", existing)
    conn.close()

    episodes_data = [
        (1, 5329, 967707789, "1080p"),
        (2, 5330, 870124449, "1080p"),
        (3, 5331, 1026455584, "1080p"),
        (4, 5332, 377434855, "720p"),
        (5, 5333, 386385222, "720p"),
        (6, 5334, 310544484, "720p"),
    ]

    for ep_num, msg_id, fsize, qual in episodes_data:
        await db.add_episode(
            dorama_id=403,
            episode_number=ep_num,
            channel_message_id=msg_id,
            file_size=fsize,
            quality=qual,
        )
        print(f"Added Ep {ep_num} -> msg {msg_id} ({qual})")

    # Restore planned total_episodes=12 and Ongoing
    conn = sqlite3.connect("doramas.db")
    conn.execute(
        "UPDATE doramas SET total_episodes = 12, status = 'Ongoing' WHERE id = 403"
    )
    conn.commit()
    row = conn.execute(
        "SELECT code, title, total_episodes, status FROM doramas WHERE code = 503"
    ).fetchone()
    ep_count = conn.execute(
        "SELECT COUNT(*) FROM episodes WHERE dorama_id = 403"
    ).fetchone()[0]
    conn.close()
    print(f"Verified Code 503: {row}, total inserted episodes: {ep_count}")


if __name__ == "__main__":
    asyncio.run(main())
