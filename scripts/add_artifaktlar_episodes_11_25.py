import sqlite3

conn = sqlite3.connect('E:/Agent/Drama Bot/doramas.db')
cur = conn.cursor()

cur.execute('SELECT id, code, title FROM doramas WHERE code = 666')
d = cur.fetchone()
if not d:
    print("Dorama 666 not found!")
    exit(1)

dorama_id = d[0]

# Mapping of episode numbers to storage message IDs and file sizes
new_episodes = {
    11: (5978, 18952842),
    12: (5979, 17670733),
    13: (5980, 15868387),
    14: (5981, 11847023),
    15: (5982, 13402141),
    16: (5983, 18860662),
    17: (5984, 15669565),
    18: (5985, 15894016),
    19: (5986, 13791220),
    21: (5987, 14323534),
    22: (5988, 16977803),
    23: (5989, 17049572),
    24: (5990, 16720303),
    25: (5991, 12586170),
}

for ep_num, (msg_id, fsize) in new_episodes.items():
    cur.execute('''
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_id, file_size, quality)
        VALUES (?, ?, ?, '', ?, '720p')
        ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
            channel_message_id = excluded.channel_message_id,
            file_size = excluded.file_size,
            quality = '720p',
            file_id = ''
    ''', (dorama_id, ep_num, msg_id, fsize))

# Update total_episodes to 25 and status to 'Ongoing'
cur.execute('''
    UPDATE doramas 
    SET total_episodes = 25, status = 'Ongoing'
    WHERE id = ?
''', (dorama_id,))

conn.commit()

# Verify
cur.execute('SELECT COUNT(*) FROM episodes WHERE dorama_id = ?', (dorama_id,))
print("Total episodes in DB for 666:", cur.fetchone()[0])

cur.execute('SELECT episode_number, channel_message_id, file_size FROM episodes WHERE dorama_id = ? ORDER BY episode_number', (dorama_id,))
for row in cur.fetchall():
    print(f"  Ep {row[0]}: msg={row[1]}, size={row[2]}")

conn.close()
