import sqlite3

conn = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
c = conn.cursor()
c.execute("SELECT id, code, title, aliases FROM doramas WHERE code = 301")
row = c.fetchone()
print("Before:", row)

current_aliases = row[3] or ""
new_aliases_list = [
    "My Bias, My Boss",
    "Mening idolim mening boshlig'im",
    "Mening dilim mening boshlig'im",
    "Mening dilim",
    "Mening yulduzim va boshlig'im",
    "Mening yulduzim mening boshlig'im"
]
combined = ", ".join(list(dict.fromkeys([a.strip() for a in (current_aliases.split(",") + new_aliases_list) if a.strip()])))

c.execute("UPDATE doramas SET aliases = ? WHERE code = 301", (combined,))
conn.commit()

c.execute("SELECT id, code, title, aliases FROM doramas WHERE code = 301")
print("After:", c.fetchone())
conn.close()
