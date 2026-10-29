import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open(r"E:\Agent\Drama Bot\scripts\bad_posters.json", "r", encoding="utf-8") as f:
    bad = json.load(f)

for b in bad:
    print(f"[{b['code']}] title='{b['title']}' | year={b['year']} | poster='{b['poster']}'")
