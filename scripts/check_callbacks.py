import re

with open(r'E:\Agent\Drama Bot\bot.py', 'r', encoding='utf-8') as f:
    text = f.read()

registered_cbs = re.findall(r'@router\.callback_query\((.*?)\)', text)
print(f"Total registered callback query decorators: {len(registered_cbs)}")
for i, r in enumerate(registered_cbs, 1):
    print(f"{i}: {r.strip()}")
