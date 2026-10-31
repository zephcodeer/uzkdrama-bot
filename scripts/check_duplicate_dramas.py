import sqlite3, sys, os, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.parse_new_dramas import parsed_dramas

conn = sqlite3.connect('doramas.db')
c = conn.cursor()

c.execute("SELECT code, title, slug FROM doramas")
existing_doramas = c.fetchall()

c.execute("SELECT channel_message_id, dorama_id, episode_number FROM episodes")
existing_episodes = {row[0]: (row[1], row[2]) for row in c.fetchall()}

print(f"Existing doramas in DB: {len(existing_doramas)}")
print(f"Existing episodes in DB: {len(existing_episodes)}")

# Check matching message IDs
matched_msgs = 0
for d in parsed_dramas:
    for ep_num, msg_id, link in d['episodes']:
        if msg_id in existing_episodes:
            matched_msgs += 1

print(f"Number of episodes whose channel_message_id is already in DB: {matched_msgs}")

# Check matching titles
from database import normalize_search_text

def clean_title(t):
    # remove hashtags, comments like || davom etmoqda
    t = re.sub(r'#|\b(davom etmoqda|ongoing|yakunlangan)\b', '', t, flags=re.IGNORECASE)
    return normalize_search_text(t)

existing_titles_norm = {clean_title(r[1]): r for r in existing_doramas}

already_existing_dramas = []
new_dramas = []

for d in parsed_dramas:
    c_title = clean_title(d['raw_title'])
    found = None
    for ex_norm, ex_row in existing_titles_norm.items():
        if c_title and (c_title == ex_norm or c_title in ex_norm or ex_norm in c_title):
            found = ex_row
            break
    if found:
        already_existing_dramas.append((d, found))
    else:
        new_dramas.append(d)

print(f"Potential existing drama title matches: {len(already_existing_dramas)}")
for d, ex in already_existing_dramas[:15]:
    print(f"   Parsed: {d['raw_title']!r} -> Existing: [{ex[0]}] {ex[1]!r}")

print(f"Completely new dramas: {len(new_dramas)}")
