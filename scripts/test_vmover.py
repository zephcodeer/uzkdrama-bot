import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    "http://v.mover.uz/uGmXQUji_h.mp4",
    "https://v.mover.uz/uGmXQUji_h.mp4",
    "http://v.mover.uz/uGmXQUji_m.mp4",
    "https://v.mover.uz/uGmXQUji_m.mp4"
]

for u in urls:
    print(f"\nTesting: {u}")
    req = urllib.request.Request(u, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://mover.uz/',
        'Origin': 'https://mover.uz',
        'Range': 'bytes=0-100'
    })
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            print(f"Status: {r.status}, Content-Length: {r.headers.get('Content-Length')}")
    except Exception as e:
        print(f"Error: {e}")
