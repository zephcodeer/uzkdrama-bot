import urllib.request
import re
import urllib.parse
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

for ep in range(3, 9):
    q = f"Ovchi itlar 1-fasl {ep}-qism"
    url = f"https://ok.ru/search?cmd=SearchBox&st.mode=Video&st.grmode=All&st.query={urllib.parse.quote(q)}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', 'ignore')
            matches = re.findall(r'href=["\']/video/(\d+)["\'][^>]*title=["\']([^"\']+)["\']', html)
            if not matches:
                matches = re.findall(r'/video/(\d+)', html)
                print(f"Ep {ep} raw video IDs:", matches[:3])
            else:
                for vid, title in matches[:3]:
                    print(f"Ep {ep} -> https://ok.ru/video/{vid} | {title}")
    except Exception as e:
        print(f"Error for ep {ep}: {e}")
