import sqlite3
import os
import sys

c = sqlite3.connect(r'E:\Agent\Drama Bot\doramas.db')
cur = c.cursor()

print('=== 1. TABLES IN DATABASE ===')
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cur.fetchall()]
print('Tables:', tables)

for t in tables:
    cur.execute(f"PRAGMA table_info({t})")
    cols = [f"{col[1]} ({col[2]})" for col in cur.fetchall()]
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    cnt = cur.fetchone()[0]
    print(f"\nTable {t} ({cnt} rows):")
    print("  Columns:", ", ".join(cols))

print('\n=== 2. DATA INTEGRITY CHECKS ===')
cur.execute("SELECT dorama_id, COUNT(*) FROM episodes GROUP BY dorama_id")
print('Episodes per dorama:', cur.fetchall())

cur.execute("SELECT id, title, code, total_episodes, status FROM doramas WHERE code IS NULL OR title IS NULL")
print('Doramas with NULL code/title:', cur.fetchall())

cur.execute("SELECT dorama_id, episode_number, channel_message_id FROM episodes WHERE channel_message_id IS NULL OR channel_message_id = 0")
print('Episodes with invalid channel_message_id:', cur.fetchall())

# Check duplicate codes in doramas
cur.execute("SELECT code, COUNT(*) FROM doramas GROUP BY code HAVING COUNT(*) > 1")
print('Duplicate dorama codes:', cur.fetchall())

# Check orphaned episodes
cur.execute("SELECT e.id, e.dorama_id, e.episode_number FROM episodes e LEFT JOIN doramas d ON e.dorama_id = d.id WHERE d.id IS NULL")
print('Orphaned episodes (no matching dorama):', cur.fetchall())

# Check users with invalid VIP
cur.execute("SELECT user_id, is_vip, vip_until FROM users WHERE is_vip = 1 AND vip_until IS NULL")
print('Invalid VIP users:', cur.fetchall())

c.close()
