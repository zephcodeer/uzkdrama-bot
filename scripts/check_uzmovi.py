import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'https://uzmovi.me/'
}

url = 'https://uzmovi.me/seriall/7407-doktor-x-oq-mafia-1-2-3-4-5-6-7-8-9-10-11-qism-drama-korea-seriali-uzbek-tilida-barcha-qismlar-2026-hd-skachat.html'
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', 'ignore')

mp4s = re.findall(r'https?://[^\s"\'<>]+\.mp4', html)
print(f"Total MP4 links found: {len(mp4s)}")

# Also look for player playlist or series config in JS
js_blocks = re.findall(r'<script[^>]*>(.*?)</script>', html, re.S)
for js in js_blocks:
    if 'player' in js.lower() or 'file' in js.lower():
        print("\n--- Script block ---")
        for line in js.splitlines():
            if any(k in line.lower() for k in ['file', 'mp4', 'playlist', 'series', 'qism']):
                print(line.strip()[:150])

print("\n--- Testing MP4 URLs ---")
for m in sorted(set(mp4s)):
    print(f"URL: {m}")
    try:
        head_req = urllib.request.Request(m, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://uzmovi.me/'}, method='HEAD')
        with urllib.request.urlopen(head_req, timeout=5) as r:
            sz = int(r.headers.get('Content-Length', 0)) / (1024*1024)
            print(f"   -> Status {r.status}, Size: {sz:.1f} MB")
    except Exception as e:
        print(f"   -> Error: {e}")
