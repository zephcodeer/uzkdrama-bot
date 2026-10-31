import sqlite3

conn = sqlite3.connect('doramas.db')
c = conn.cursor()
c.execute("SELECT code, title, status, total_episodes, (SELECT count(*) FROM episodes e WHERE e.dorama_id = d.id) FROM doramas d WHERE status = 'Ongoing' LIMIT 5")
for r in c.fetchall():
    print(r)
conn.close()
