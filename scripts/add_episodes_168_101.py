import sqlite3

conn = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
c = conn.cursor()

# 1. Update 100 kunlik yolg'on (code 168)
c.execute("SELECT id FROM doramas WHERE code = 168")
d168_id = c.fetchone()[0]

c.execute("SELECT id FROM episodes WHERE dorama_id = ? AND episode_number = 6", (d168_id,))
existing = c.fetchone()
if existing:
    c.execute("UPDATE episodes SET channel_message_id = 5058, file_id = '' WHERE id = ?", (existing[0],))
    print("Updated episode 6 for 100 kunlik yolg'on (code 168)")
else:
    c.execute("""
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_id, file_size, quality)
        VALUES (?, 6, 5058, '', 0, '720p')
    """, (d168_id,))
    print("Inserted episode 6 for 100 kunlik yolg'on (code 168)")

# 2. Update Doktor X (code 101)
c.execute("SELECT id FROM doramas WHERE code = 101")
d101_id = c.fetchone()[0]

c.execute("SELECT id FROM episodes WHERE dorama_id = ? AND episode_number = 6", (d101_id,))
existing = c.fetchone()
if existing:
    c.execute("UPDATE episodes SET channel_message_id = 5059, file_id = '' WHERE id = ?", (existing[0],))
    print("Updated episode 6 for Doktor X (code 101)")
else:
    c.execute("""
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_id, file_size, quality)
        VALUES (?, 6, 5059, '', 0, '720p')
    """, (d101_id,))
    print("Inserted episode 6 for Doktor X (code 101)")

conn.commit()

# Verify
print("\n--- VERIFICATION ---")
c.execute("SELECT episode_number, channel_message_id FROM episodes WHERE dorama_id = ? ORDER BY episode_number", (d168_id,))
print("100 kunlik yolg'on episodes:", c.fetchall())

c.execute("SELECT episode_number, channel_message_id FROM episodes WHERE dorama_id = ? ORDER BY episode_number", (d101_id,))
print("Doktor X episodes:", c.fetchall())

conn.close()
