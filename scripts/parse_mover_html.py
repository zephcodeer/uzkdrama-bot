import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('E:/Agent/Drama Bot/mover_test.html', 'r', encoding='utf-8') as f:
    html = f.read()

# find title
title = re.search(r'<title>([^<]+)</title>', html)
print("Title:", title.group(1) if title else "No title")

# find iframe or player container
for m in re.finditer(r'<iframe[^>]+src=["\']([^"\']+)["\']', html):
    print("Iframe:", m.group(1))

# find scripts with player/video/stream/api
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for i, s in enumerate(scripts):
    if any(k in s for k in ['video', 'player', 'm3u8', 'mp4', 'file', 'stream', 'hls', 'mover', 'api']):
        print(f"\n================ Script {i} (len: {len(s)}) ================")
        print(s[:600])

# check vue or window data
for m in re.finditer(r'window\.[a-zA-Z0-9_]+\s*=\s*\{[^;]+', html):
    print("\nWindow object:", m.group(0)[:300])
