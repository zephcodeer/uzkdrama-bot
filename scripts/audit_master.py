import sqlite3
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

conn = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
c = conn.cursor()

c.execute("""
    SELECT d.id, d.code, d.title, d.total_episodes, COUNT(e.id) as real_eps, d.poster_url
    FROM doramas d
    LEFT JOIN episodes e ON d.id = e.dorama_id
    GROUP BY d.id
    ORDER BY d.code
""")
rows = c.fetchall()

print(f"Jami bazadagi doramalar soni: {len(rows)} ta\n")
total_eps_all = 0
ready_doramas = 0

for r in rows:
    d_id, code, title, tot_eps, real_eps, poster = r
    total_eps_all += real_eps
    poster_exists = os.path.exists(poster) if poster else False
    
    if code == 121 and real_eps == 0:
        print(f"ℹ️ [{d_id:2d}] Kod {code:3d}: {title:35s} | Zaxira")
        continue

    if tot_eps == real_eps and real_eps > 0 and poster_exists:
        ready_doramas += 1
        print(f"✅ [{d_id:2d}] Kod {code:3d}: {title[:35]:35s} | {real_eps:2d}/{tot_eps:2d} qism | Poster: OK")
    else:
        print(f"❌ [{d_id:2d}] Kod {code:3d}: {title[:35]:35s} | Tot: {tot_eps:2d} | Eps: {real_eps:2d} | Poster: {poster_exists}")

print("\n" + "="*70)
print(f"JAMI TO'LIQ ISHLAYOTGAN DORAMALAR: {ready_doramas} ta!")
print(f"JAMI BAZADAGI QISMLAR SONI: {total_eps_all} ta!")
print("="*70)
