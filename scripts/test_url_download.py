import urllib.request, urllib.error, ssl, sys, os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

test_urls = [
    ("351", "https://asianwiki.com/images/d/df/Branding_in_Seongsu-mp1.jpeg"),
    ("352", "https://asianwiki.com/images/f/fd/The_Story_Of_Parks_Marriage_Contract-p2.jpg"),
    ("479", "https://image.tmdb.org/t/p/w500/7VPyZ2lwWcynkbV1Rp5WBydQAAl.jpg")
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://asianwiki.com/"
}

for code, url in test_urls:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = resp.read()
            print(f"[{code}] Downloaded {len(data):,} bytes from {url}")
    except Exception as e:
        print(f"[{code}] Failed to download {url}: {e}")
