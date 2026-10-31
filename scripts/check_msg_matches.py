import sqlite3, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.parse_new_dramas import parsed_dramas

conn = sqlite3.connect(r'E:\Agent\Drama Bot\doramas.db')
c = conn.cursor()
c.execute('SELECT channel_message_id, dorama_id, episode_number FROM episodes')
existing_episodes = {row[0]: (row[1], row[2]) for row in c.fetchall()}

for d in parsed_dramas:
    matches = []
    for ep_num, msg_id, link in d['episodes']:
        if msg_id in existing_episodes:
            matches.append((ep_num, msg_id, existing_episodes[msg_id]))
    if matches:
        title = d['raw_title']
        print(f"Drama {title!r} has matching message IDs in DB:")
        for m in matches:
            c.execute('SELECT code, title FROM doramas WHERE id = ?', (m[2][0],))
            d_info = c.fetchone()
            print(f"   ep {m[0]} msg {m[1]} -> matched DB dorama [{d_info[0]}] {d_info[1]!r} ep {m[2][1]}")
