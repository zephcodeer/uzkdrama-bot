import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
headers = {'User-Agent': 'Mozilla/5.0'}
url = 'https://salomtv.uz/uz/serials/doktor-iks?season_id=97c25d62-9b47-4eba-8b00-8ce8b07d8f4c'
with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
    html = r.read().decode('utf-8', 'ignore')

streams = re.findall(r'https?://[^\s"\'\\]+\.(?:m3u8|mp4)', html)
print("Salomtv video links:", set(streams))

# Search for any json data containing episodes
ep_ids = re.findall(r'\"id\":\"([a-f0-9\-]{36})\"', html)
print("UUIDs found:", len(ep_ids), ep_ids[:5])
