import urllib.request
import urllib.parse
import json
import re

def search_bing_images(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}&FORM=HDRSC2"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return []
    
    # Bing stores full image URLs in m="{...&quot;murl&quot;:&quot;URL&quot;...}"
    murls = re.findall(r'murl&quot;:&quot;(http[^&]+)&quot;', html)
    if not murls:
        murls = re.findall(r'"murl":"(http[^"]+)"', html)
    return murls[:5]

if __name__ == "__main__":
    queries = [
        "Vincenzo kdrama poster pinterest 1000x1500",
        "Avengers Endgame official poster high resolution",
        "While You Were Sleeping kdrama poster tmdb",
        "Healer kdrama poster high resolution",
        "Hwarang kdrama poster pinterest"
    ]
    for q in queries:
        urls = search_bing_images(q)
        print(q, "found:", len(urls))
        for u in urls[:2]:
            print("  ", u)
