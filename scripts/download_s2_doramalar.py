import base64
import urllib.request
import re
import ssl
import sys
import subprocess
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

TEMP_DIR = Path(r"E:\Agent\Drama Bot\temp_downloads")

def decode_doramalar(s: str) -> str:
    if not isinstance(s, str) or not s.startswith("#2"):
        return s
    t = s[2:]
    for item in reversed(['6u3kEQLAkT', '4e0OIbkv8D', 'EXOThnsl1y', 'wHiWWKB8U9', 'rMTS46lVY0']):
        r = '//' + base64.b64encode(item.encode()).decode()
        n = t.find(r)
        if n != -1:
            t = t[:n] + t[n + len(r):]
    try:
        return base64.b64decode(t).decode('utf-8', errors='ignore')
    except Exception:
        return ""

def resolve_stream(page_url: str) -> str:
    req = urllib.request.Request(page_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    
    b64_matches = re.findall(r'#2[a-zA-Z0-9+/=]+', html)
    if not b64_matches:
        raise ValueError("Playerjs ma'lumotlari topilmadi")
    
    decoded_mp4 = decode_doramalar(b64_matches[1]) if len(b64_matches) > 1 else ""
    urls = re.findall(r'https://[^\s,]+', decoded_mp4)
    mp4_urls = [u for u in urls if '.mp4?' in u] or urls
    
    for u in mp4_urls:
        try:
            test_req = urllib.request.Request(u, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Referer': 'https://doramalar.net/'
            })
            with urllib.request.urlopen(test_req, context=ctx, timeout=6) as tr:
                if tr.status == 200:
                    return u
        except Exception:
            continue
            
    return decode_doramalar(b64_matches[0])

def download_ep(ep_num: int, page_url: str):
    dest = TEMP_DIR / f"ovchi_itlar_s2_ep{ep_num}.mp4"
    if dest.exists() and dest.stat().st_size > 50 * 1024 * 1024:
        print(f"⏩ {ep_num}-qism allaqachon mavjud.")
        return
    
    stream_url = resolve_stream(page_url)
    print(f"📥 2-Fasl {ep_num}-qism stream olinmoqda: {stream_url[:80]}...")
    cmd = [
        "yt-dlp",
        "--add-header", "Referer:https://doramalar.net/",
        "-o", str(dest),
        stream_url,
        "--no-playlist"
    ]
    subprocess.run(cmd)

if __name__ == "__main__":
    download_ep(6, "https://doramalar.net/dorama/ovchi-itlar-37/2-fasl-6-qism")
    download_ep(7, "https://doramalar.net/dorama/ovchi-itlar-37/2-fasl-7-qism")
