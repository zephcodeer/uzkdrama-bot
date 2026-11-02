import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
DB_PATH = r"E:\Agent\Drama Bot\doramas.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

episodes = [
    (384, 7, 5167, '1080p'),
    (384, 8, 5168, '1080p')
]

for dorama_id, ep_num, msg_id, quality in episodes:
    c.execute("""
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
            channel_message_id = excluded.channel_message_id,
            quality = excluded.quality
    """, (dorama_id, ep_num, msg_id, quality))
    print(f"Upserted Episode {ep_num} -> Message {msg_id}")

conn.commit()

c.execute("SELECT episode_number, channel_message_id, quality FROM episodes WHERE dorama_id = 384 ORDER BY episode_number")
rows = c.fetchall()
print(f"Total episodes now in DB for Dorama 384: {len(rows)}")
for r in rows:
    print(f"  Ep {r[0]}: Msg {r[1]} ({r[2]})")

conn.close()
