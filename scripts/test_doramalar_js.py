import urllib.request
import re
import ssl
import base64

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://doramalar.net/dorama/ovchi-itlar-37/2-fasl-6-qism"
req = urllib.request.Request(
    url,
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
)

with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Let's inspect the playerjs script or look for the decode algorithm
scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', html, re.I)
print("External scripts:", scripts)

# Let's check inline scripts
inline = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL | re.I)
for i, s in enumerate(inline):
    if "Playerjs" in s or "playerjs" in s or "#2" in s:
        print(f"Inline script {i}:")
        print(s[:1000])
