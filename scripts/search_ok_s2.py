import urllib.request
import urllib.parse
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

query = "ovchi itlar 2 fasl"
url = f"https://ok.ru/video/search?cmd=SearchVideo&q={urllib.parse.quote(query)}"
req = urllib.request.Request(
    url,
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'uz,ru;q=0.9,en;q=0.8'
    }
)

try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        print(f"OK search HTML: {len(html)}")
        video_ids = re.findall(r'/video/(\d+)', html)
        print("Found video IDs:", list(dict.fromkeys(video_ids))[:15])
        
        # Look for video titles
        titles = re.findall(r'aria-label="([^"]*ovchi[^"]*)"', html, re.I)
        print("Titles with ovchi:", titles[:10])
except Exception as e:
    print("Error:", e)
