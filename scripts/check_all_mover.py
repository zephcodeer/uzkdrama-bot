import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

mover_ids = [
    (1, "uGmXQUji"),
    (2, "e1muznc1"),
    (3, "cF3is6bE"),
    (4, "QRAJ0tZa"),
    (5, "cTVJwfaX"),
    (6, "slohSEqg"),
    (7, "dEo0owSK"),
    (8, "WcEtHZI")
]

print("=== CHECKING ALL 8 MOVER.UZ 720p STREAMS ===")
for ep, vid in mover_ids:
    url = f"https://v.mover.uz/{vid}_h.mp4"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://mover.uz/',
        'Range': 'bytes=0-10'
    })
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            cr = r.headers.get('Content-Range', '')
            # format: bytes 0-10/1234567
            total_size = cr.split('/')[-1] if '/' in cr else r.headers.get('Content-Length', '0')
            sz_mb = int(total_size) / (1024*1024) if total_size.isdigit() else 0
            print(f"[EP {ep}] {vid} -> HTTP {r.status} | Size: {sz_mb:.1f} MB | URL: {url}")
    except Exception as e:
        print(f"[EP {ep}] {vid} -> ERROR: {e}")
