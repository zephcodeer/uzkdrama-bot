import urllib.request
import re
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(
    'https://doramalar.net/dorama/ovchi-itlar-37',
    headers={'User-Agent': 'Mozilla/5.0'}
)

with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Find all links containing 2-fasl
links = re.findall(r'href=["\']([^"\']*2-fasl[^"\']*)["\']', html)
print("All 2-fasl links on main page:", sorted(set(links)))
