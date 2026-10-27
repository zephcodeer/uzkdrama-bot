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
        decoded = base64.b64decode(t).decode('utf-8')
        return decoded
    except Exception as e:
        return f"Decode error: {e}"

for ep in range(1, 8):
    url = f"https://doramalar.net/dorama/ovchi-itlar-37/2-fasl-{ep}-qism"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            b64_matches = re.findall(r'#2[a-zA-Z0-9+/=]+', html)
            if b64_matches:
                # usually match 0 is m3u8, match 1 is mp4
                decoded_m3u8 = decode_doramalar(b64_matches[0])
                decoded_mp4 = decode_doramalar(b64_matches[1]) if len(b64_matches) > 1 else ""
                print(f"✅ 2-fasl {ep}-qism:")
                print(f"   M3U8: {decoded_m3u8[:120]}...")
                if "[720p]" in decoded_mp4:
                    mp4_url = decoded_mp4.split("[720p]")[1].split(" or ")[0].split(",")[0]
                    print(f"   MP4 (720p): {mp4_url[:120]}...")
            else:
                print(f"❌ 2-fasl {ep}-qism: No player found")
    except Exception as e:
        print(f"❌ 2-fasl {ep}-qism Error: {e}")
