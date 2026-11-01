import sqlite3

conn = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
c = conn.cursor()
c.execute("SELECT id, code, title, total_episodes, status FROM doramas WHERE code = 168")
d = c.fetchone()
print("Dorama:", d)

c.execute("SELECT episode_number, channel_message_id FROM episodes WHERE dorama_id = ? ORDER BY episode_number", (d[0],))
eps = c.fetchall()
print("Current episodes:", eps)
conn.close()
