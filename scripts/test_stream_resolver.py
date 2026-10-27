import base64
import urllib.request
import re
import ssl
import sys
import os

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

def download_doramalar_episode(page_url, out_path, chunk_size=1024*1024):
    req = urllib.request.Request(page_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    
    b64_matches = re.findall(r'#2[a-zA-Z0-9+/=]+', html)
    if not b64_matches:
        raise ValueError("Playerjs payload topilmadi")
    
    decoded_mp4 = decode_doramalar(b64_matches[1]) if len(b64_matches) > 1 else ""
    urls = re.findall(r'https://[^\s,]+', decoded_mp4)
    # Filter 720p urls
    mp4_urls = [u for u in urls if 's02_e06_ovchi-itlar.mp4' in u or '.mp4?' in u]
    if not mp4_urls:
        mp4_urls = urls

    stream_url = None
    for u in mp4_urls:
        try:
            test_req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Referer': 'https://doramalar.net/'})
            with urllib.request.urlopen(test_req, context=ctx, timeout=5) as tr:
                if tr.status == 200:
                    stream_url = u
                    break
        except Exception:
            continue
    
    if not stream_url:
        raise ValueError("Birorta ham ishlaydigan mirror topilmadi")
    
    print(f"Tanlangan stream: {stream_url}")
    return stream_url

stream = download_doramalar_episode("https://doramalar.net/dorama/ovchi-itlar-37/2-fasl-6-qism", "dummy.mp4")
print("Resolved stream:", stream[:80])
