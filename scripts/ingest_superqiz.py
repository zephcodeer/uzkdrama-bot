import sqlite3
import os

conn = sqlite3.connect("doramas.db")
c = conn.cursor()

# Check if code 345 already exists
c.execute("SELECT id, code, title FROM doramas WHERE code = 345")
existing = c.fetchone()
if existing:
    print("Code 345 already exists:", existing)
else:
    c.execute("""
        INSERT INTO doramas (
            code, title, slug, genre, year, status, total_episodes,
            country, actors, category, description, aliases, poster_url, views
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        345,
        "Superqiz (Supergirl 2026)",
        "superqiz-2026",
        "Fantastika, Jangari, Sarguzasht",
        2026,
        "Tugallangan",
        1,
        "AQSh",
        "Milli Olkok (Milly Alcock), Sasha Calle",
        "marvel",
        "Kara Zor-El o'zining sodiq do'sti Kripto bilan galaktika bo'ylab sayohat qilayotgan vaqtida xavfli kosmik qaroqchilar hujumiga duch keladi. Kema vayron bo'lib, eng yaqin do'sti jarohatlangach, Superqiz adolatni qaror toptirish va qasos olish uchun butun koinot bo'ylab ayovsiz jangga kirishadi.",
        "Supergirl, Super ayol, Superqiz 2026, Supergirl 2026, Milly Alcock Supergirl, Superqiz kino, Super ayol 2026",
        "posters/superqiz-2026.jpg",
        0
    ))
    dorama_id = c.lastrowid
    print(f"Created dorama record id={dorama_id}, code=345")

    # Insert episode 1 (message 3411)
    c.execute("""
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_id, quality)
        VALUES (?, ?, ?, ?, ?)
    """, (dorama_id, 1, 3411, "", "1080p"))
    print("Inserted episode 1 with channel_message_id=3411!")

conn.commit()

# Verify
c.execute("SELECT d.code, d.title, COUNT(e.id) FROM doramas d JOIN episodes e ON d.id = e.dorama_id WHERE d.code = 345 GROUP BY d.id")
print("Verification:", c.fetchone())
conn.close()
