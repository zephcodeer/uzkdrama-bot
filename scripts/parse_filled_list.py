import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r"C:\Users\MuhammadSodiq\.gemini\antigravity\brain\680976b1-3abc-4cda-8304-fa727e684760\doramalar_royxati.md", "r", encoding="utf-8") as f:
    text = f.read()

lines = text.splitlines()

parsed_doramas = []
current_title = None
current_links = []

for line in lines:
    line = line.strip()
    if not line or line.startswith("="):
        if current_title and current_links:
            parsed_doramas.append((current_title, current_links))
            current_title = None
            current_links = []
        continue
    
    # Check if line contains a dorama name followed by links
    m_name = re.match(r"^([A-Za-z0-9\s':\(\)\/\-\?,!]+?)\s+(?:1\.|#?\s*1\.)https?://", line)
    if m_name:
        if current_title and current_links:
            parsed_doramas.append((current_title, current_links))
        current_title = m_name.group(1).strip()
        links = re.findall(r"(?:#\s*)?(\d+)\.(https?://t\.me/c/\d+/(\d+))", line)
        current_links = [(int(ep), url, int(msg_id)) for ep, url, msg_id in links]
        continue
    
    # If it's a continuation line with links
    if current_title:
        links = re.findall(r"(?:#\s*)?(\d+)\.(https?://t\.me/c/\d+/(\d+))", line)
        if links:
            for ep, url, msg_id in links:
                current_links.append((int(ep), url, int(msg_id)))

if current_title and current_links:
    parsed_doramas.append((current_title, current_links))

print(f"Jami aniqlangan doramalar: {len(parsed_doramas)} ta\n")
total_eps = 0
for title, eps in parsed_doramas:
    # Deduplicate links by msg_id if any duplicate
    seen_msgs = set()
    dedup_eps = []
    for ep, u, m in eps:
        if m not in seen_msgs:
            seen_msgs.add(m)
            dedup_eps.append((len(dedup_eps) + 1, u, m))
    total_eps += len(dedup_eps)
    print(f"🎬 {title:38s}: {len(dedup_eps):2d} ta qism (Msg {dedup_eps[0][2]} .. {dedup_eps[-1][2]})")

print(f"\nJAMI QISMLAR SONI: {total_eps} ta!")
