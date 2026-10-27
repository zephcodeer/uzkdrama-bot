import re
import sys
sys.path.append(r"E:\Agent\Drama Bot")
import emojis

with open(r"E:\Agent\Drama Bot\bot.py", "r", encoding="utf-8") as f:
    text = f.read()

calls = re.findall(r"ce\(['\"](\w+)['\"]\)", text)
missing = []
for k in set(calls):
    val = emojis.ce(k)
    if not val:
        missing.append(k)

print(f"Total unique ce() calls in bot.py: {len(set(calls))}")
for k in sorted(set(calls)):
    res = emojis.ce(k)
    print(f"  {k} -> {res[:30]}...")

print("\nMissing or empty emojis:", missing)
