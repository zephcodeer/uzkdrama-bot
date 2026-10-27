import urllib.request
import re
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request("https://doramalar.net/assets/dorama/pleyer/vendor.js", headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
    js = resp.read().decode('utf-8', errors='ignore')

# Search for ke, He, je
for var_name in ['ke', 'He', 'je']:
    matches = re.findall(rf'(?:var\s+{var_name}\b|function\s+{var_name}\b|{var_name}\s*=\s*)[^;]+;', js)
    print(f"Matches for {var_name}:", matches[:5])
