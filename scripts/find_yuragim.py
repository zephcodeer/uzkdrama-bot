import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
conn = sqlite3.connect(r'E:\Agent\Drama Bot\doramas.db')
c = conn.cursor()
c.execute("SELECT id, code, title, total_episodes, status FROM doramas WHERE title LIKE '%yuragim%' OR aliases LIKE '%yuragim%' OR title LIKE '%quvvat%' OR aliases LIKE '%quvvat%'")
rows = c.fetchall()
for r in rows:
    print('Dorama:', r)
    c.execute('SELECT episode_number, channel_message_id FROM episodes WHERE dorama_id = ? ORDER BY episode_number', (r[0],))
    eps = c.fetchall()
    print('Episodes count:', len(eps), 'Episodes:', eps)
