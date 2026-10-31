import sqlite3

conn = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
c = conn.cursor()
c.execute("SELECT code, title, poster_url FROM doramas LIMIT 10")
for r in c.fetchall():
    print(r)
conn.close()
