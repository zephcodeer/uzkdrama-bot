import urllib.request
import ssl
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

embed_url = 'https://mover.uz/video/embed/uGmXQUji'
req = urllib.request.Request(embed_url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://mover.uz/watch/uGmXQUji'
})

with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

print("Embed HTML len:", len(html))

# search for file: or playerjs
for m in re.finditer(r'file\s*:\s*["\']([^"\']+)["\']', html):
    print("File found:", m.group(1))

# search for any mp4 or m3u8
media = re.findall(r'https?://[^\s"\'<>]+\.(?:mp4|m3u8)[^\s"\'<>]*', html)
print(f"Media ({len(media)}):")
for m in media:
    print("  ", m)

# search for scripts
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
print(f"Scripts ({len(scripts)}):")
for i, s in enumerate(scripts):
    print(f"\n--- Script {i} ---")
    print(s[:500])
