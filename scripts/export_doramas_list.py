import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

conn = sqlite3.connect("doramas.db")
c = conn.cursor()

query = """
    SELECT d.code, d.title, d.year, d.total_episodes, COUNT(e.id) as ep_count, d.status
    FROM doramas d
    LEFT JOIN episodes e ON d.id = e.dorama_id
    GROUP BY d.id
    ORDER BY d.code ASC
"""
c.execute(query)
rows = c.fetchall()
conn.close()

# Text file
lines = []
lines.append("=" * 80)
lines.append(f"UZKDRAMA BOT — BARCHA DRAMALAR RO'YXATI (JAMI: {len(rows)} TA)")
lines.append("=" * 80)
lines.append(f"{'KOD':<6} | {'NOMI':<46} | {'YILI':<6} | {'QISMLAR':<12} | {'STATUS'}")
lines.append("-" * 80)

for code, title, year, total_exp, ep_count, status in rows:
    clean_title = title[:44]
    y = str(year) if year else "-"
    s = status or "Noma'lum"
    exp = total_exp if total_exp else "?"
    ep_str = f"{ep_count}/{exp}"
    lines.append(f"{code:<6} | {clean_title:<46} | {y:<6} | {ep_str:<12} | {s}")

with open("DRAMALAR_ROYXATI.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Total: {len(rows)} doramas exported to DRAMALAR_ROYXATI.txt")
