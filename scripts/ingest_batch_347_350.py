import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH = "doramas.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

new_doramas = [
    {
        "code": 347,
        "title": "Xalk / Xalk 1 (Hulk 2003)",
        "slug": "xalk-1",
        "genre": "Fantastika, Jangari, Sarguzasht",
        "year": 2003,
        "status": "Tugallangan",
        "total_episodes": 1,
        "country": "AQSH",
        "actors": "Erik Bana (Eric Bana), Jennifer Connelly, Sam Elliott",
        "category": "marvel",
        "description": "Olim Bryus Benner o'z laboratoriyasidagi kutilmagan gamma nurlanishi halokatidan so'ng omon qoladi. Biroq bu radiatsiya uning genetik tuzilishini o'zgartiradi: har gal kuchli g'azab yoki hayajon paydo bo'lganda, u ulkan, yengilmas yashil maxluq — Xalkka aylanadi. Harbiy kuchlar uni xavfli qurol deb hisoblab, yo'q qilishga kirishadi.",
        "aliases": "Xalk 1, Xalk, Hulk, Hulk 2003, Erik Bana, Bryus Benner, Bruce Banner, Marvel Hulk 1",
        "poster_url": "posters/hulk-2003.jpg",
        "episodes": [
            (1, 4590, "1080p")
        ]
    },
    {
        "code": 348,
        "title": "Xalk 2: Aqlbovar qilmas Xalk (The Incredible Hulk 2008)",
        "slug": "xalk-2",
        "genre": "Fantastika, Jangari, Sarguzasht, Triller",
        "year": 2008,
        "status": "Tugallangan",
        "total_episodes": 1,
        "country": "AQSH",
        "actors": "Edvard Norton (Edward Norton), Liv Tayler, Tim Rot",
        "category": "marvel",
        "description": "Bryus Benner o'zidagi yirtqichni jilovlash va davo topish maqsadida dunyoning eng chekka burchaklarida yashirinib yuradi. Ammo general Ross boshchiligidagi armiya uni tinch qo'ymaydi. Shu bilan birga, yana bir xavfli askar Emili Blonski undan ham dahshatli maxluq — Abominationga aylanib, Nyu-Yorkni vayron qila boshlaydi. Uni faqat Xalk to'xtata oladi.",
        "aliases": "Xalk 2, Xalk 2 2008, The Incredible Hulk, The Incredible Hulk 2008, Aqlbovar qilmas Xalk, Edvard Norton, Marvel Hulk 2, Abomination",
        "poster_url": "posters/the-incredible-hulk-2008.jpg",
        "episodes": [
            (1, 4591, "1080p")
        ]
    },
    {
        "code": 349,
        "title": "Ayol Xalk: Advokat (She-Hulk: Attorney at Law 2022)",
        "slug": "ayol-xalk",
        "genre": "Fantastika, Komediya, Jangari, Huquqiy",
        "year": 2022,
        "status": "Tugallangan",
        "total_episodes": 9,
        "country": "AQSH",
        "actors": "Tatyana Maslani (Tatiana Maslany), Mark Ruffalo, Tim Rot, Jameela Jamil",
        "category": "marvel",
        "description": "Oddiy 30 yoshli advokat Jennifer Uolters o'z amakivachchasi Bryus Benner (Xalk) bilan avtohalokatga uchragach, tasodifan uning qoni bilan zararlanadi va Ayol Xalkka aylanish qobiliyatini qo'lga kiritadi. Endi u nafaqat superqahramonlar huquqlarini himoya qiluvchi yuridik bo'limni boshqarishi, balki o'zining 2 metrlik yashil qiyofasi va shaxsiy hayoti o'rtasida muvozanat topishi kerak.",
        "aliases": "Ayol Xalk, Ayol Halk, She-Hulk, She Hulk, She-Hulk Attorney at Law, Ayol Xalk Marvel, She-Hulk 2022, Jennifer Walters, Tatyana Maslani",
        "poster_url": "posters/she-hulk-2022.jpg",
        "episodes": [
            (1, 4592, "1080p"),
            (2, 4593, "1080p"),
            (3, 4594, "1080p"),
            (4, 4595, "1080p"),
            (5, 4596, "1080p"),
            (6, 4597, "1080p"),
            (7, 4598, "1080p"),
            (8, 4599, "1080p"),
            (9, 4600, "1080p")
        ]
    },
    {
        "code": 350,
        "title": "Y loyihasi (Project Y 2026)",
        "slug": "y-loyihasi",
        "genre": "Kriminal, Triller, Neo-nuar, Drama",
        "year": 2026,
        "status": "Tugallangan",
        "total_episodes": 1,
        "country": "Janubiy Koreya",
        "actors": "Han So-hee (Han So Hee), Jeon Jong-seo (Jun Jong Seo), Kim Shin-rok",
        "category": "korea",
        "description": "Seulning Gangnam tumanida yashovchi ikki tengdosh dugona (Mi-seon va Do-kyeong) bor-yo'q pullarini firibgarlarga boy bergach, umidsizlikka tushib qoladilar. Qashshoqlikdan qutulish uchun ular jinoiy to'daning yashirin 8 milliard vonlik oltin quymalarini o'g'irlash bo'yicha o'ta xavfli rejani tuzadilar. Ammo bu reja ularni butun shahar mafiyasi bilan to'qnashuvga olib keladi.",
        "aliases": "Y loyhasi, Y loyihasi, Project Y, Project Y 2026, Han So-hee, Jeon Jong-seo, Proyekt Y, Han So Xi, Jon Jon So",
        "poster_url": "posters/project-y-2026.jpg",
        "episodes": [
            (1, 4049, "1080p")
        ]
    }
]

for d in new_doramas:
    code = d["code"]
    c.execute("SELECT id, title FROM doramas WHERE code = ?", (code,))
    existing = c.fetchone()
    
    if existing:
        d_id = existing[0]
        print(f"[# {code}] Mavjud ({existing[1]}), ma'lumotlari yangilanmoqda...")
        c.execute("""
            UPDATE doramas SET
                title = ?, slug = ?, genre = ?, year = ?, status = ?,
                total_episodes = ?, country = ?, actors = ?, category = ?,
                description = ?, aliases = ?, poster_url = ?
            WHERE id = ?
        """, (
            d["title"], d["slug"], d["genre"], d["year"], d["status"],
            d["total_episodes"], d["country"], d["actors"], d["category"],
            d["description"], d["aliases"], d["poster_url"], d_id
        ))
        c.execute("DELETE FROM episodes WHERE dorama_id = ?", (d_id,))
    else:
        print(f"[# {code}] Yangi qo'shilmoqda: {d['title']}")
        c.execute("""
            INSERT INTO doramas (
                code, title, slug, genre, year, status, total_episodes,
                country, actors, category, description, aliases, poster_url, views
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            d["code"], d["title"], d["slug"], d["genre"], d["year"], d["status"],
            d["total_episodes"], d["country"], d["actors"], d["category"],
            d["description"], d["aliases"], d["poster_url"]
        ))
        d_id = c.lastrowid

    # Insert episodes
    for ep_num, msg_id, quality in d["episodes"]:
        c.execute("""
            INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_id, quality)
            VALUES (?, ?, ?, ?, ?)
        """, (d_id, ep_num, msg_id, "", quality))

    print(f"  -> {len(d['episodes'])} ta qism muvaffaqiyatli bog'landi.")

conn.commit()
conn.close()

print("\nBARCHA 4 TA FILM/SERIAL BAZAGA 100% MUVAFFAQIYATLI YUKLANDI!")
