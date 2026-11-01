import sqlite3

conn = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
c = conn.cursor()
c.execute("""
    SELECT id, code, title, total_episodes, 
           (SELECT COUNT(*) FROM episodes e WHERE e.dorama_id = d.id) as ep_count,
           status, aliases 
    FROM doramas d 
    WHERE title LIKE '%boshlig%' OR aliases LIKE '%boshlig%' 
       OR title LIKE '%yulduz%' OR aliases LIKE '%yulduz%'
""")
rows = c.fetchall()
print(f"Total found: {len(rows)}")
for r in rows:
    print(r)
conn.close()
