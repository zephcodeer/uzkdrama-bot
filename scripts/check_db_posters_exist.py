import sqlite3, os

conn = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
c = conn.cursor()
c.execute("SELECT code, title, poster_url FROM doramas ORDER BY code")
rows = c.fetchall()

missing_posters = []
for code, title, poster_url in rows:
    if not poster_url:
        missing_posters.append((code, title, "NO_URL"))
    elif not os.path.exists(os.path.join(r"E:\Agent\Drama Bot", poster_url)):
        missing_posters.append((code, title, poster_url))

print(f"Total doramas in DB: {len(rows)}")
print(f"Missing poster files on disk: {len(missing_posters)}")
if missing_posters:
    print("First 10 missing:")
    for m in missing_posters[:10]:
        print("  ", m)
conn.close()
