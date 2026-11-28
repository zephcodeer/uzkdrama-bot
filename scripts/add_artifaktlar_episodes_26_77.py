import sqlite3

conn = sqlite3.connect('E:/Agent/Drama Bot/doramas.db')
cur = conn.cursor()

cur.execute('SELECT id, code, title FROM doramas WHERE code = 666')
d = cur.fetchone()
if not d:
    print("Dorama 666 not found!")
    exit(1)

dorama_id = d[0]

# Episode mapping for 26..77:
# 26: 5993
# 27..33: 5994..6000
# 35..37: 6001..6003 (34 is missing in donor channel!)
# 38..47: 6004..6013
# 48..77: 6014..6043

episodes_to_add = {}
episodes_to_add[26] = (5993, 15040892)
for ep, mid in zip(range(27, 34), range(5994, 6001)):
    episodes_to_add[ep] = (mid, 0)
episodes_to_add[35] = (6001, 32720999)
episodes_to_add[36] = (6002, 48697078)
episodes_to_add[37] = (6003, 28092297)
for ep, mid in zip(range(38, 48), range(6004, 6014)):
    episodes_to_add[ep] = (mid, 0)
for ep, mid in zip(range(48, 78), range(6014, 6044)):
    episodes_to_add[ep] = (mid, 0)

for ep_num, (mid, fsize) in episodes_to_add.items():
    cur.execute('''
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_id, file_size, quality)
        VALUES (?, ?, ?, '', ?, '720p')
        ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
            channel_message_id = excluded.channel_message_id,
            file_size = excluded.file_size,
            quality = '720p',
            file_id = ''
    ''', (dorama_id, ep_num, mid, fsize))

cur.execute('''
    UPDATE doramas 
    SET total_episodes = 77, status = 'Ongoing'
    WHERE id = ?
''', (dorama_id,))

conn.commit()

cur.execute('SELECT COUNT(*) FROM episodes WHERE dorama_id = ?', (dorama_id,))
print("Total episodes in DB for 666:", cur.fetchone()[0])
conn.close()
