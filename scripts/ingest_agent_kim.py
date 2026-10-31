import sqlite3

conn = sqlite3.connect("doramas.db")
c = conn.cursor()

# Check if code 346 already exists
c.execute("SELECT id, code, title FROM doramas WHERE code = 346")
existing = c.fetchone()
if existing:
    print("Code 346 already exists:", existing)
else:
    c.execute("""
        INSERT INTO doramas (
            code, title, slug, genre, year, status, total_episodes,
            country, actors, category, description, aliases, poster_url, views
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        346,
        "Agent Kimning qaytishi (Manager Kim 2025)",
        "agent-kimning-qaytishi",
        "Jangari, Triller, Kriminal, Drama",
        2025,
        "Tugallangan",
        10,
        "Janubiy Koreya",
        "So Ji-sub (So Ji Sub), Kim Hee-won",
        "korea",
        "Sobiq elita maxsus agenti bo'lgan Kim hozirda oddiy menejer sifatida tinch hayot kechiradi. Ammo uning yagona qizi kutilmaganda shafqatsiz jinoiy to'da tomonidan o'g'irlab ketilgach, Kim yana qurolini qo'lga oladi va qizini qutqarish uchun butun yer osti mafiyasiga qarshi yakka o'zi urush ochadi.",
        "Manager Kim, Menejer Kim, Agent Kim, Kim bujang, Agent Kimning qaytishi 2025, Menejer Kim 2025, Manager Kim Reactivated",
        "posters/agent-kim.jpg",
        0
    ))
    dorama_id = c.lastrowid
    print(f"Created dorama record id={dorama_id}, code=346")

    # Insert 10 episodes (message IDs 3413 to 3422)
    for ep_num in range(1, 11):
        msg_id = 3412 + ep_num
        c.execute("""
            INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_id, quality)
            VALUES (?, ?, ?, ?, ?)
        """, (dorama_id, ep_num, msg_id, "", "1080p"))
    print("Inserted all 10 episodes (3413 to 3422) successfully!")

conn.commit()

# Verify
c.execute("SELECT d.code, d.title, COUNT(e.id) FROM doramas d JOIN episodes e ON d.id = e.dorama_id WHERE d.code = 346 GROUP BY d.id")
print("Verification:", c.fetchone())
conn.close()
