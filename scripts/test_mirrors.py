import base64
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

def decode_doramalar(s):
    t = s[2:]
    for item in reversed(['6u3kEQLAkT', '4e0OIbkv8D', 'EXOThnsl1y', 'wHiWWKB8U9', 'rMTS46lVY0']):
        r = '//' + base64.b64encode(item.encode()).decode()
        n = t.find(r)
        if n != -1: t = t[:n] + t[n+len(r):]
    return base64.b64decode(t).decode('utf-8', errors='ignore')

req = urllib.request.Request('https://doramalar.net/dorama/ovchi-itlar-37/2-fasl-6-qism', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
with urllib.request.urlopen(req, context=ctx) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

b64_matches = re.findall(r'#2[a-zA-Z0-9+/=]+', html)
decoded_mp4 = decode_doramalar(b64_matches[1])
# Extract all URLs
urls = re.findall(r'https://[^\s,]+', decoded_mp4)
print(f"Found {len(urls)} URLs in decoded payload:")

for u in urls:
    try:
        test_req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Referer': 'https://doramalar.net/'})
        with urllib.request.urlopen(test_req, context=ctx, timeout=7) as test_resp:
            print(f"✅ Status {test_resp.status} - Content-Length: {test_resp.headers.get('Content-Length')} -> {u[:60]}...")
    except Exception as e:
        print(f"❌ Failed ({e}) -> {u[:60]}...")
