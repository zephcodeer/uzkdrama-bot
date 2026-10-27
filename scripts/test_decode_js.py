import urllib.request
import re
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    "https://doramalar.net/assets/dorama/pleyer/pleyer.js",
    "https://doramalar.net/assets/dorama/pleyer/mount.min.js",
    "https://doramalar.net/assets/dorama/pleyer/vendor.js"
]

for u in urls:
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            print(f"{u} size: {len(content)}")
            # Search for decode or #2 or atob or unescape
            matches = re.findall(r'(?:#2|decode|atob|unescape|replace)[^\n]{0,100}', content)
            print(f"Matches in {u}: {len(matches)}")
            for m in matches[:10]:
                if any(x in m for x in ['#2', 'atob', 'substr', 'replace']):
                    print("  ", m)
    except Exception as e:
        print(f"Error {u}: {e}")
