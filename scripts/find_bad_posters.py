import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open(r"E:\Agent\Drama Bot\scripts\poster_audit.json", "r", encoding="utf-8") as f:
    items = json.load(f)

bad_posters = []
for item in items:
    w, h = map(int, item['res'].split('x'))
    if w < 500 or h < 700 or item['ratio'] < 1.15:
        bad_posters.append(item)

print(f"Total posters needing replacement: {len(bad_posters)}")
for b in bad_posters:
    print(f"[{b['code']}] {b['title']} -> {b['res']} ({b['size_kb']} KB)")

with open(r"E:\Agent\Drama Bot\scripts\bad_posters.json", "w", encoding="utf-8") as f:
    json.dump(bad_posters, f, ensure_ascii=False, indent=2)
