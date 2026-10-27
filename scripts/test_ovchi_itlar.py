import urllib.request
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://uzmovi.me/'
}

url = "https://uzmovi.me/seriall/6964-ovchi-itlar-1-2-fasl-1-2-3-4-5-6-7-8-9-10-11-12-15-qism-koreya-serial-uzbek-tilida-barcha-qismlar-2023-hd.html"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=10) as resp:
    html = resp.read().decode('utf-8', 'ignore')

mp4s = re.findall(r'https?://[^\s"\'<>]+\.mp4', html)
print(f"Total MP4s for Ovchi Itlar: {len(mp4s)}")
for m in sorted(set(mp4s))[:10]:
    print(" ", m)
