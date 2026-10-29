import urllib.request
import re

url = "https://www.themoviedb.org/tv/219651"
req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    # Search for poster image
    m = re.findall(r'https://image\.tmdb\.org/t/p/[^"\']+\.jpg', html)
    print("Found images:", len(m))
    for img in m[:5]:
        print("  ", img)
except Exception as e:
    print("Error:", e)
