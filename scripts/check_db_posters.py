import sqlite3

c = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
cur = c.execute("SELECT id, title, code, poster_url FROM doramas WHERE poster_url IS NOT NULL AND poster_url != ''")
rows = cur.fetchall()
print(f"Doramas with posters ({len(rows)}):")
for r in rows:
    print(r)
c.close()
