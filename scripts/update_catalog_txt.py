import sqlite3

conn = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
c = conn.cursor()
c.execute("SELECT code, title, status, total_episodes, (SELECT count(*) FROM episodes e WHERE e.dorama_id = d.id) FROM doramas d ORDER BY code")
rows = c.fetchall()

with open(r"E:\Agent\Drama Bot\DRAMALAR_ROYXATI.txt", "w", encoding="utf-8") as f:
    f.write(f"BARCHA DRAMALAR RO'YXATI (JAMI {len(rows)} TA)\n")
    f.write("=" * 60 + "\n\n")
    for code, title, status, total_ep, ep_count in rows:
        f.write(f"[{code}] {title} — {ep_count}/{total_ep} qism ({status})\n")

# Also update Downloads copies if needed
downloads_master = r"C:\Users\MuhammadSodiq\Downloads\DRAMALAR_ROYXATI_HAMMASI_380.txt"
with open(downloads_master, "w", encoding="utf-8") as f:
    f.write(f"BARCHA DRAMALAR RO'YXATI (JAMI {len(rows)} TA)\n")
    f.write("=" * 60 + "\n\n")
    for code, title, status, total_ep, ep_count in rows:
        f.write(f"[{code}] {title} — {ep_count}/{total_ep} qism ({status})\n")

print(f"Updated DRAMALAR_ROYXATI.txt with {len(rows)} doramas.")
conn.close()
