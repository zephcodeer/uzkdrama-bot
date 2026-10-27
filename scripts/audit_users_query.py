import sys

with open(r'E:\Agent\Drama Bot\database.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if 'users' in line.lower() or 'WHERE user_id' in line or 'tg_id' in line:
        print(f"{i}: {line.strip()}")
