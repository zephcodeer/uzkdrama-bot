import sqlite3
import os

conn = sqlite3.connect('E:/Agent/Drama Bot/doramas.db')
cur = conn.cursor()

# Check if 666 already exists
cur.execute('SELECT id, code, title FROM doramas WHERE code = 666')
existing = cur.fetchone()

if existing:
    print(f"Dorama with code 666 already exists: {existing}")
    dorama_id = existing[0]
else:
    cur.execute('''
        INSERT INTO doramas (
            title, slug, genre, year, description, poster_url, 
            total_episodes, views, code, status, country, actors, category, aliases
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Artifaktlar Hukmdori',
        'artifaktlar-hukmdori-666',
        'Vertikal Micro-Drama, Fantastika, Jangari, Sehr-jodu',
        2026,
        'Zamonaviy shahar va qadimiy afsonaviy olam chorrahasida qudratli artifaktlar kuchi uygʻonadi. Qahramon yashirin artifaktlar sirlarini ochib, beqiyos jangovar qudratga erishadi va dunyo muvozanatini saqlab qolish uchun jangga kirishadi...',
        'posters/code_666.jpg',
        10,
        0,
        666,
        'Tugallangan (Completed)',
        'Xitoy',
        'Mahalliy mini-dorama aktyorlari',
        'mini_drama',
        'Artifaktlar Hukmdor, Artifact Master, Lord of Artifacts, Artifaktlar'
    ))
    dorama_id = cur.lastrowid
    print(f"Created dorama with ID: {dorama_id}, Code: 666")

# Now insert / update episodes 1..10 (msg 5967..5976)
ep_sizes = {
    1: (5967, 26316950),
    2: (5968, 18263439),
    3: (5969, 17912614),
    4: (5970, 15127430),
    5: (5971, 21672267),
    6: (5972, 23244068),
    7: (5973, 20154812),
    8: (5974, 13128850),
    9: (5975, 13363282),
    10: (5976, 22986572)
}

for ep_num, (msg_id, fsize) in ep_sizes.items():
    cur.execute('''
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_id, file_size, quality)
        VALUES (?, ?, ?, '', ?, '720p')
        ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
            channel_message_id = excluded.channel_message_id,
            file_size = excluded.file_size,
            quality = '720p',
            file_id = ''
    ''', (dorama_id, ep_num, msg_id, fsize))

conn.commit()

# Verify
cur.execute('SELECT id, code, title, total_episodes, category FROM doramas WHERE id = ?', (dorama_id,))
print("Dorama:", cur.fetchone())

cur.execute('SELECT episode_number, channel_message_id, file_size, quality FROM episodes WHERE dorama_id = ? ORDER BY episode_number', (dorama_id,))
episodes = cur.fetchall()
print(f"Total episodes inserted: {len(episodes)}")
for ep in episodes:
    print(f"  Ep {ep[0]}: msg={ep[1]}, size={ep[2]}, quality={ep[3]}")

conn.close()
