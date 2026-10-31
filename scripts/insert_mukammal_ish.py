import sqlite3
import os

db_path = r"E:\Agent\Drama Bot\doramas.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Check if code 480 already exists
c.execute("SELECT id, code, title FROM doramas WHERE code = 480")
existing = c.fetchone()
if existing:
    print(f"Warning: Code 480 already exists: {existing}")
else:
    # Insert Dorama 480
    c.execute("""
        INSERT INTO doramas (
            title, slug, genre, year, description, poster_url, 
            total_episodes, views, code, status, country, 
            actors, category, aliases, series_group
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Mukammal ish (Dead-End Job)",
        "mukammal-ish",
        "Triller, Detektiv, Sirli",
        2026,
        "Qarz botqog'iga botgan yigit (Li Chje Vuk) juda katta haq to'lanadigan, ammo o'ta xavfli va sirli vaqtinchalik ishga kirishadi va dahshatli hodisalar girdobiga tushib qoladi...",
        "posters/code_480.jpg",
        8,
        0,
        480,
        "Ongoing",
        "Janubiy Koreya",
        "Lee Jae-wook, Go Min-si, Kim Min-ha, Lee Hee-joon",
        "korea",
        "Dead-End Job, Ggul-alba, Oxiri yo'q ish, Mukammal ish 2026, 꿀알바, Dead End Job",
        ""
    ))
    dorama_id = c.lastrowid
    print(f"Inserted dorama ID: {dorama_id}, Code: 480")

    # Insert episodes 1 to 6
    episodes_data = [
        (1, 5057),
        (2, 5052),
        (3, 5053),
        (4, 5054),
        (5, 5055),
        (6, 5056)
    ]

    for ep_num, msg_id in episodes_data:
        c.execute("""
            INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_id, file_size, quality)
            VALUES (?, ?, ?, '', 0, '720p')
        """, (dorama_id, ep_num, msg_id))
        print(f"Inserted Episode {ep_num} -> Message ID: {msg_id}")

    conn.commit()
    print("Database commit successful!")

conn.close()
