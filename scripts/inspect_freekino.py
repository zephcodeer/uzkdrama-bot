import urllib.request
import ssl
import re
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://freekino.net/serie/2647-ojiz-qahramon-uz-1-fasl-1-qism"
req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        html = r.read().decode("utf-8", errors="ignore")
    print(f"Fetched HTML length: {len(html)}")

    t = re.search(r"<title>([^<]+)</title>", html)
    print(f"Title: {t.group(1) if t else 'None'}")

    # Check for player or episode navigation
    ep_links = re.findall(r'href=["\'](https://freekino\.net/serie/2647-[^"\']+)["\']', html)
    print(f"Direct episode links: {len(ep_links)}")
    for l in set(ep_links):
        print(f"  {l}")

    # Check for general episode links
    all_ep_links = re.findall(r'href=["\'](/serie/[^"\']+)["\']', html)
    print(f"All serie links on page: {len(all_ep_links)}")
    for l in list(set(all_ep_links))[:10]:
        print(f"  {l}")

    # Check for iframes
    iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
    print(f"Iframes: {iframes}")

    # Check for playerjs, file:, or video sources
    files = re.findall(r'file\s*:\s*["\']([^"\']+)["\']', html)
    print(f"File matches: {files}")

    sources = re.findall(r'<source[^>]+src=["\']([^"\']+)["\']', html)
    print(f"Source matches: {sources}")

    # Search for any player config or script payloads
    b64s = re.findall(r'#2[a-zA-Z0-9+/=]+', html)
    print(f"Playerjs #2 matches: {len(b64s)}")

    # Check for poster
    posters = re.findall(r'src=["\']([^"\']+\.(?:jpg|png|webp|jpeg)[^"\']*)["\']', html)
    print(f"Image links: {posters[:5]}")

    with open(r"E:\Agent\Drama Bot\freekino_sample.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved freekino_sample.html for in-depth analysis.")

except Exception as e:
    print(f"Error: {e}")
