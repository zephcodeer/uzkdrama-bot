import urllib.request
import re
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(
    'https://doramalar.net/dorama/ovchi-itlar-37/2-fasl-6-qism',
    headers={'User-Agent': 'Mozilla/5.0'}
)

with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Find all episode links or numbers
ep_links = re.findall(r'href=["\']([^"\']*ovchi-itlar[^"\']*)["\']', html)
print("Ovchi itlar links:", sorted(set(ep_links)))

# Find fasl info
fasl_info = re.findall(r'<[^>]+>(?:Fasl|qism|Qism|Сезон|Серия)[^<]*</[^>]+>', html, re.I)
print("Fasl text samples:", fasl_info[:10])
