import urllib.request
import re
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

url = "https://ok.ru/video/16259252619826"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=10) as resp:
    html = resp.read().decode('utf-8', 'ignore')

# Search for group or user links
groups = re.findall(r'href=["\']/(group/\d+|profile/\d+)[^"\']*["\']', html)
print("Groups/Profiles found:", set(groups))

# Search for any other video links on the page
vids = re.findall(r'href=["\']/video/(\d+)["\'][^>]*>([^<]+)</a>', html)
print("Other videos on page count:", len(vids))
for v_id, text in vids[:15]:
    print(f"  https://ok.ru/video/{v_id} -> {text.strip()}")
