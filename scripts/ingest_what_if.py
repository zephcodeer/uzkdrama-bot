import sqlite3
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = r"E:\Agent\Drama Bot"
DB_PATH = os.path.join(BASE_DIR, "doramas.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. series_group ustunini tekshirish / qo'shish
    c.execute("PRAGMA table_info(doramas)")
    cols = [r[1] for r in c.fetchall()]
    if "series_group" not in cols:
        print("doramas jadvaliga 'series_group' ustuni qo'shilmoqda...")
        c.execute("ALTER TABLE doramas ADD COLUMN series_group TEXT DEFAULT ''")
    else:
        print("'series_group' ustuni mavjud.")

    # 2. Mavjud franchizalarni biriktirish
    # Squid Game (311, 312, 315)
    c.execute("UPDATE doramas SET series_group = 'squid-game' WHERE code IN (311, 312, 315)")
    # Wednesday (319, 320)
    c.execute("UPDATE doramas SET series_group = 'wednesday' WHERE code IN (319, 320)")

    # 3. What If Season 1 va 2 ni kiritish
    seasons_data = [
        {
            "code": 343,
            "title": "Agarda... (What If...?) 1-fasl",
            "slug": "agarda-what-if-1-fasl",
            "genre": "Multfilm, Fantastika, Jangari, Marvel",
            "year": 2021,
            "total_episodes": 9,
            "status": "Tugallangan",
            "country": "AQSH",
            "category": "marvel",
            "actors": "Jeffrey Wright, Hayley Atwell, Chadwick Boseman, Benedict Cumberbatch, Chris Hemsworth",
            "description": "Kuzatuvchi (The Watcher) Marvel olamidagi muhim burilish nuqtalarini kuzatadi: Agar asosiy voqealar boshqacha rivojlanganida, koinot qanday tus olgan bo'lardi?",
            "poster_url": "posters/what-if-s1.jpg",
            "aliases": "What If, Agarda Marvel, What If 1, Agarda 1, Vot If, Nima bolardi agar",
            "series_group": "what-if",
            "episodes": [
                (1, 3342), (2, 3343), (3, 3344), (4, 3345), (5, 3346),
                (6, 3347), (7, 3348), (8, 3349), (9, 3350)
            ]
        },
        {
            "code": 344,
            "title": "Agarda... (What If...?) 2-fasl",
            "slug": "agarda-what-if-2-fasl",
            "genre": "Multfilm, Fantastika, Jangari, Marvel",
            "year": 2023,
            "total_episodes": 9,
            "status": "Tugallangan",
            "country": "AQSH",
            "category": "marvel",
            "actors": "Jeffrey Wright, Hayley Atwell, Cate Blanchett, Laurence Fishburne, Karen Gillan",
            "description": "Kuzatuvchi cheksiz multikoinot bo'ylab yangi qahramonlar va kutilmagan sarguzashtlarni kashf etishda davom etadi. Yangi ittifoqlar va taqdir sinovlari.",
            "poster_url": "posters/what-if-s2.jpg",
            "aliases": "What If 2, Agarda Marvel 2, What If Season 2, Agarda 2, Vot If 2",
            "series_group": "what-if",
            "episodes": [
                (1, 3351), (2, 3352), (3, 3353), (4, 3354), (5, 3355),
                (6, 3356), (7, 3357), (8, 3358), (9, 3359)
            ]
        }
    ]

    for s_info in seasons_data:
        c.execute("SELECT id FROM doramas WHERE code = ? OR slug = ?", (s_info["code"], s_info["slug"]))
        existing = c.fetchone()
        if existing:
            dorama_id = existing[0]
            c.execute("""
                UPDATE doramas SET
                    title = ?, genre = ?, year = ?, description = ?,
                    poster_url = ?, total_episodes = ?, status = ?, country = ?,
                    actors = ?, category = ?, aliases = ?, series_group = ?
                WHERE id = ?
            """, (
                s_info["title"], s_info["genre"], s_info["year"], s_info["description"],
                s_info["poster_url"], s_info["total_episodes"], s_info["status"], s_info["country"],
                s_info["actors"], s_info["category"], s_info["aliases"], s_info["series_group"],
                dorama_id
            ))
            print(f"Yangilandi: id={dorama_id}, code={s_info['code']}")
        else:
            c.execute("""
                INSERT INTO doramas (
                    code, title, slug, genre, year, description,
                    poster_url, total_episodes, views, status, country,
                    actors, category, aliases, series_group
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 15, ?, ?, ?, ?, ?, ?)
            """, (
                s_info["code"], s_info["title"], s_info["slug"], s_info["genre"],
                s_info["year"], s_info["description"], s_info["poster_url"], s_info["total_episodes"],
                s_info["status"], s_info["country"], s_info["actors"], s_info["category"],
                s_info["aliases"], s_info["series_group"]
            ))
            dorama_id = c.lastrowid
            print(f"Yangi qo'shildi: id={dorama_id}, code={s_info['code']}, title='{s_info['title']}'")

        # Qismlarni saqlash
        c.execute("DELETE FROM episodes WHERE dorama_id = ?", (dorama_id,))
        for ep_num, msg_id in s_info["episodes"]:
            c.execute("""
                INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality, file_id)
                VALUES (?, ?, ?, ?, ?)
            """, (dorama_id, ep_num, msg_id, "1080p", None))

    conn.commit()
    
    c.execute("SELECT COUNT(*) FROM doramas")
    tot_d = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM episodes")
    tot_e = c.fetchone()[0]
    print(f"\nBazada jami: {tot_d} ta dorama, {tot_e} ta qism mavjud.")
    conn.close()

if __name__ == "__main__":
    main()
