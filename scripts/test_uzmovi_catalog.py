import urllib.request
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://uzmovi.me/'
}

req = urllib.request.Request("https://uzmovi.me/seriall/", headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', 'ignore')
        print("HTML len:", len(html))
        # Find serial links
        items = re.findall(r'href="(https://uzmovi\.me/seriall/[^"]+)"[^>]*>([^<]+)</a>', html)
        print("Serials count:", len(items))
        for link, title in items[:15]:
            print(f"  {title.strip()[:40]} -> {link}")
except Exception as e:
    print("Error:", e)
