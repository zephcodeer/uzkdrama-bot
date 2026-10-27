import base64
import urllib.request
import re
import ssl
import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def decode_doramalar(encoded_str):
    if not isinstance(encoded_str, str) or not encoded_str.startswith("#2"):
        return encoded_str
    t = encoded_str[2:]
    He = "//"
    ke = ["6u3kEQLAkT", "4e0OIbkv8D", "EXOThnsl1y", "wHiWWKB8U9", "rMTS46lVY0"]
    for item in reversed(ke):
        r = He + base64.b64encode(item.encode('utf-8')).decode('utf-8')
        n = t.find(r)
        if n != -1:
            t = t[:n] + t[n + len(r):]
    try:
        return base64.b64decode(t).decode('utf-8')
    except Exception as e:
        return ""

def get_doramalar_stream(page_url):
    req = urllib.request.Request(page_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    
    b64_matches = re.findall(r'#2[a-zA-Z0-9+/=]+', html)
    if not b64_matches:
        return None
    
    # Check if there is mp4
    if len(b64_matches) > 1:
        decoded_mp4 = decode_doramalar(b64_matches[1])
        if "[720p]" in decoded_mp4:
            part = decoded_mp4.split("[720p]")[1].split(" or ")[0].split(",")[0].strip()
            return part
    
    # Or return m3u8
    decoded_m3u8 = decode_doramalar(b64_matches[0])
    return decoded_m3u8

url = "https://doramalar.net/dorama/ovchi-itlar-37/2-fasl-6-qism"
stream = get_doramalar_stream(url)
print("Live stream URL:", stream)

if stream:
    # Test downloading 2MB
    s_req = urllib.request.Request(stream, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://doramalar.net/'})
    t0 = time.time()
    with urllib.request.urlopen(s_req, context=ctx, timeout=15) as s_resp:
        data = s_resp.read(2 * 1024 * 1024)
        dt = time.time() - t0
        print(f"Downloaded {len(data)/(1024*1024):.1f} MB in {dt:.2f}s (Speed: {len(data)/(1024*1024*dt):.2f} MB/s)")
