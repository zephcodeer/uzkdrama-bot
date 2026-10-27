import urllib.request
import re
import ssl
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://ok.ru/video/15973306665522"
req = urllib.request.Request(
    url,
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
)

with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Find uploader / group link
groups = re.findall(r'/(?:group|profile)/(\d+)', html)
print("Groups / Profiles found:", set(groups))

# Find other video links from same author
vids = re.findall(r'/video/(\d{10,})', html)
print("Related video IDs:", list(dict.fromkeys(vids))[:10])
