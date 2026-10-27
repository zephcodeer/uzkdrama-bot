import urllib.request
import re
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://doramalar.net/dorama/ovchi-itlar-37', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
print("All images:", imgs[:10])
og_image = re.findall(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html)
print("OG Image:", og_image)
