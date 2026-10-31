import re, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

file_path = r"c:\Users\MuhammadSodiq\Downloads\drama_links_2026-10-31.md"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# Blocks are separated by ==================== or start of file
blocks = re.split(r"={10,}", text)
print(f"Total raw blocks found: {len(blocks)}")

parsed_dramas = []
for idx, b in enumerate(blocks):
    lines = [l.strip() for l in b.strip().split("\n") if l.strip()]
    if not lines:
        continue
    
    # First line or lines before numbers is title
    title_lines = []
    episodes = []
    for line in lines:
        m = re.match(r"^(\d+)\s*[\.:\)]\s*(https://t\.me/c/\d+/(\d+))", line)
        if m:
            ep_num = int(m.group(1))
            link = m.group(2)
            msg_id = int(m.group(3))
            episodes.append((ep_num, msg_id, link))
        else:
            if not episodes:
                title_lines.append(line)
    
    raw_title = " ".join(title_lines).strip()
    if raw_title and episodes:
        parsed_dramas.append({
            "block_index": idx,
            "raw_title": raw_title,
            "episodes": episodes
        })

print(f"Total parsed dramas with episodes: {len(parsed_dramas)}")
total_eps = sum(len(d['episodes']) for d in parsed_dramas)
print(f"Total episodes across all dramas: {total_eps}")
for d in parsed_dramas[:10]:
    print(f"Title: {d['raw_title']!r} | Episodes count: {len(d['episodes'])} | First ep: {d['episodes'][0]} | Last ep: {d['episodes'][-1]}")
