import sqlite3

conn = sqlite3.connect('E:/Agent/Drama Bot/doramas.db')
c = conn.cursor()

# Check if exists
c.execute("SELECT id FROM doramas WHERE id = 36 OR code = 136")
row = c.fetchone()
if not row:
    c.execute("""
        INSERT INTO doramas (
            id, code, title, slug, genre, year, description, poster_url, total_episodes, views, created_at, status, country, actors
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, datetime('now'), ?, ?, ?)
    """, (
        36,
        136,
        'Ojiz qahramon 2-fasl (Weak Hero Class 2)',
        'ojiz-qahramon-2-fasl',
        'Ekshn, Yoshlar, Maktab, Triller',
        2025,
        "Yeon Si-eun Eunjang o'rta maktabiga ko'chib o'tadi va yangi do'stlar orttiradi. U yerda yanada xavfli va shafqatsiz jinoiy to'dalar hamda maktab zo'ravonlariga qarshi o'z aqli va shafqatsiz kurash taktikasi bilan jangga kirishadi.",
        'E:/Agent/Drama Bot/posters/ojiz_qahramon_s2.jpg',
        8,
        'Tugallangan',
        'Janubiy Koreya',
        'Park Ji-hoon, Ryeoun, Choi Min-young, Lee Min-jae, Yoo Su-bin, Lee Jun-young'
    ))
    conn.commit()
    print("Dorama 36 (Code 136) inserted successfully!")
else:
    print("Dorama already exists with ID:", row[0])

c.execute("SELECT id, code, title, total_episodes, poster_url FROM doramas WHERE id = 36")
print("Row:", c.fetchone())
conn.close()
