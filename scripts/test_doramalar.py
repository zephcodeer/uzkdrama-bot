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

try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        print(f"HTML Length: {len(html)}")

        # Search for player iframes or embeds
        iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.I)
        print("Iframes found:", iframes)

        ok_links = re.findall(r'https?://(?:ok\.ru|odnoklassniki\.ru)/[^\s"\'<>]+', html)
        print("OK links found:", set(ok_links))

        # Look for player config, file: "...", file: "#2...", or similar
        file_matches = re.findall(r'(?:file|source|video|src)\s*:\s*["\']([^"\']+)["\']', html, re.I)
        print("File keys found:", file_matches)

        # Look for base64 encoded strings
        b64_matches = re.findall(r'#2[a-zA-Z0-9+/=]+', html)
        print("Base64 #2 found:", b64_matches)

        # Check all script tags
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL | re.I)
        for i, s in enumerate(scripts):
            if any(k in s.lower() for k in ['player', 'playlist', 'video', 'm3u8', 'mp4', 'iframe']):
                print(f"\n--- Script {i} ---")
                print(s.strip()[:600])

except Exception as e:
    print("Error:", e)
