import sqlite3

conn = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
c = conn.cursor()
c.execute("""
    SELECT d.id, d.code, d.title, d.total_episodes, 
           (SELECT COUNT(*) FROM episodes e WHERE e.dorama_id = d.id) as ep_count,
           d.status, d.aliases 
    FROM doramas d 
    WHERE d.code = 168 OR d.title LIKE '%100%' OR d.title LIKE '%yolg%' OR d.aliases LIKE '%100%'
""")
rows = c.fetchall()
print(f"Total matching doramas: {len(rows)}")
for r in rows:
    print(r)
conn.close()
