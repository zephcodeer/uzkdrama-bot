import sqlite3, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = sqlite3.connect(r'E:\Agent\Drama Bot\doramas.db')
c = conn.cursor()

# 1. Update episode 9 message ID
c.execute("""
    UPDATE episodes
    SET channel_message_id = 5051,
        file_id = '',
        file_size = 0
    WHERE dorama_id = 142 AND episode_number = 9
""")
print(f"Updated episodes rows: {c.rowcount}")

# 2. Update aliases for dorama 242 (add Yuragimni quvatla)
c.execute("SELECT aliases FROM doramas WHERE id = 142")
current_aliases = c.fetchone()[0] or ""
new_aliases = current_aliases + ", Yuragimni quvatla, Meni quvatla"
c.execute("UPDATE doramas SET aliases = ? WHERE id = 142", (new_aliases,))
print(f"Updated aliases for [242]: {new_aliases}")

conn.commit()

# Verify
c.execute("SELECT episode_number, channel_message_id, file_id FROM episodes WHERE dorama_id = 142 ORDER BY episode_number")
eps = c.fetchall()
print("Updated episodes for dorama 142 (code 242):")
for ep in eps:
    print(f"   Ep {ep[0]}: msg {ep[1]} (file_id: {ep[2]!r})")

# 3. Update DRAMALAR_ROYXATI.txt
c.execute("""
    SELECT d.code, d.title, d.year, COUNT(e.id) as real_eps, d.total_episodes, d.status
    FROM doramas d
    LEFT JOIN episodes e ON d.id = e.dorama_id
    GROUP BY d.id
    ORDER BY d.code ASC
""")
all_rows = c.fetchall()

master_file = r"E:\Agent\Drama Bot\DRAMALAR_ROYXATI.txt"
with open(master_file, "w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write(f"UZKDRAMA BOT — BARCHA DRAMALAR RO'YXATI (JAMI: {len(all_rows)} TA)\n")
    f.write("=" * 80 + "\n")
    f.write(f"{'KOD':<6} | {'NOMI':<46} | {'YILI':<6} | {'QISMLAR':<12} | {'STATUS':<12}\n")
    f.write("-" * 80 + "\n")
    for r in all_rows:
        code_val, title_val, year_val, real_cnt, total_ep, status_val = r
        ep_display = f"{real_cnt}/{total_ep}"
        f.write(f"{code_val:<6} | {title_val[:46]:<46} | {year_val:<6} | {ep_display:<12} | {status_val:<12}\n")

print(f"Re-generated {master_file}")
conn.close()
