import urllib.request
import urllib.parse
import re

def search_asianwiki(query):
    url = f"https://asianwiki.com/index.php?title=Special%3ASearch&search={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        # Find search results
        results = re.findall(r'<div class="mw-search-result-heading"><a href="(/[^"]+)" title="([^"]+)"', html)
        return results[:3]
    except Exception as e:
        return [str(e)]

if __name__ == "__main__":
    queries = [
        "Head over Heels",
        "Gyeonwoo and Fairy",
        "Human from Today",
        "My Love from the Star",
        "As You Stood By",
        "Siren's Kiss",
        "Boyfriend on Demand",
        "Dream to You",
        "Lament of the River Immortal",
        "Bloom Again"
    ]
    for q in queries:
        print(q, "->", search_asianwiki(q))
