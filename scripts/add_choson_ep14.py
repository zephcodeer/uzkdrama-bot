import sqlite3

conn = sqlite3.connect('E:/Agent/Drama Bot/doramas.db')
cur = conn.cursor()

cur.execute('SELECT id, code, title, total_episodes, status FROM doramas WHERE code = 355')
d = cur.fetchone()
print("Dorama:", d)

d_id = d[0]
cur.execute('''
    INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_id, file_size, quality)
    VALUES (?, 14, 6063, '', 739515966, '720p')
    ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
        channel_message_id = 6063,
        file_size = 739515966,
        quality = '720p',
        file_id = ''
''', (d_id,))

cur.execute('''
    UPDATE doramas 
    SET total_episodes = 16, status = 'Ongoing'
    WHERE id = ?
''', (d_id,))

conn.commit()

cur.execute('SELECT episode_number, channel_message_id, file_size FROM episodes WHERE dorama_id = ? ORDER BY episode_number', (d_id,))
rows = cur.fetchall()
print(f"Total episodes for 355: {len(rows)}")
for r in rows:
    print(f"  Ep {r[0]}: msg={r[1]}, size={r[2]}")

conn.close()
