import sqlite3

conn = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
c = conn.cursor()
c.execute("SELECT code, title, poster_url FROM doramas WHERE code IN (101, 227, 351, 467, 479)")
rows = c.fetchall()
for r in rows:
    print(r)
conn.close()
