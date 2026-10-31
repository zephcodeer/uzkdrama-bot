import sys, os
sys.path.insert(0, r"E:\Agent\Drama Bot")
import re

with open(r"E:\Agent\Drama Bot\bot.py", "r", encoding="utf-8") as f:
    content = f.read()

# find where dorama details/caption are formatted
matches = re.findall(r"def .*dorama.*\(.*?\):", content)
print("Dorama related funcs:", matches)

# Find caption generation
for m in re.finditer(r"status.*total_episodes|total_episodes.*status", content, re.IGNORECASE):
    start = max(0, m.start() - 200)
    end = min(len(content), m.end() + 200)
    print("--- SNIPPET ---")
    print(content[start:end])
