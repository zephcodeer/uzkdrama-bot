import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open(r"E:\Agent\Drama Bot\scripts\poster_audit.json", "r", encoding="utf-8") as f:
    items = json.load(f)

for item in items:
    print(f"{item['code']} | {item['title']} | {item['poster']} | {item['res']} | {item['status']}")
