import sqlite3

conn = sqlite3.connect('E:/Agent/Drama Bot/doramas.db')
c = conn.cursor()
c.execute("SELECT id, code, title, total_episodes, poster_url FROM doramas WHERE title LIKE '%ojiz%' OR title LIKE '%weak%' OR code IN (112, 113, 136, 137)")
for r in c.fetchall():
    print(r)

c.execute("SELECT MAX(code), MAX(id) FROM doramas")
print("Max code and ID:", c.fetchone())
conn.close()
