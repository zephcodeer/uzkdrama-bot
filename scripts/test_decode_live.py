import base64
import urllib.request
import re
import ssl

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

# Test with live page
req = urllib.request.Request(
    "https://doramalar.net/dorama/ovchi-itlar-37/2-fasl-6-qism",
    headers={'User-Agent': 'Mozilla/5.0'}
)

with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Extract #2 strings
b64_matches = re.findall(r'#2[a-zA-Z0-9+/=]+', html)
for i, m in enumerate(b64_matches):
    print(f"\n--- Match {i} ---")
    print("Raw:", m[:60] + "...")
    decoded = decode_doramalar(m)
    print("Decoded:")
    print(decoded)
