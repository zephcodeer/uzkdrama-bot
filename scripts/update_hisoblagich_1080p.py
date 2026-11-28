import sqlite3

conn = sqlite3.connect('E:/Agent/Drama Bot/doramas.db')
cur = conn.cursor()

cur.execute('SELECT id, code, title FROM doramas WHERE code = 175')
d = cur.fetchone()
if not d:
    print("Dorama 175 not found!")
    exit(1)
d_id = d[0]

# Episode 1..16 -> msg 6047..6062
for ep_num, mid in enumerate(range(6047, 6063), start=1):
    cur.execute('''
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_id, file_size, quality)
        VALUES (?, ?, ?, '', 0, '1080p')
        ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
            channel_message_id = excluded.channel_message_id,
            quality = '1080p',
            file_id = ''
    ''', (d_id, ep_num, mid))

cur.execute('''
    UPDATE doramas 
    SET total_episodes = 16, status = 'Tugallangan'
    WHERE id = ?
''', (d_id,))

conn.commit()

cur.execute('SELECT COUNT(*) FROM episodes WHERE dorama_id = ?', (d_id,))
print("Total episodes in DB for 175:", cur.fetchone()[0])
conn.close()
