import urllib.request
import urllib.parse
import json
import re

def search_ddg_images(query):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    token_url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(token_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return f"Token error: {e}"
        
    m = re.search(r'vqd=([\d-]+)', html) or re.search(r'vqd=["\']([\d-]+)["\']', html)
    if not m:
        return "No VQD found"
    vqd_val = m.group(1)
    
    img_url = f"https://duckduckgo.com/i.js?l=us-en&o=json&q={urllib.parse.quote(query)}&vqd={vqd_val}&f=,,,&p=1"
    req2 = urllib.request.Request(img_url, headers=headers)
    try:
        with urllib.request.urlopen(req2, timeout=5) as resp2:
            res = json.loads(resp2.read().decode("utf-8"))
        return [(r["image"], r["width"], r["height"]) for r in res.get("results", [])[:5]]
    except Exception as e:
        return f"Fetch error: {e}"

if __name__ == "__main__":
    for q in ["Vincenzo kdrama poster imdb", "Ballerina 2023 korean movie poster imdb", "Avengers Endgame poster imdb"]:
        print(q, "->", search_ddg_images(q))
