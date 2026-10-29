import urllib.request
import urllib.parse
import json

def get_imdb_id_from_wiki(wiki_title):
    headers = {"User-Agent": "UzKdramaBot/2.0 (admin@uzkdrama.org)"}
    # 1. Get Wikidata item ID
    url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageprops&ppprop=wikibase_item&titles={urllib.parse.quote(wiki_title)}&format=json"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode())
        pages = data.get("query", {}).get("pages", {})
        qid = None
        for pid, p in pages.items():
            qid = p.get("pageprops", {}).get("wikibase_item")
            break
        if not qid:
            return None
        # 2. Get Wikidata P345 (IMDb ID)
        wd_url = f"https://www.wikidata.org/w/api.php?action=wbgetclaims&entity={qid}&property=P345&format=json"
        req2 = urllib.request.Request(wd_url, headers=headers)
        with urllib.request.urlopen(req2, timeout=6) as resp2:
            data2 = json.loads(resp2.read().decode())
        claims = data2.get("claims", {}).get("P345", [])
        if claims:
            return claims[0].get("mainsnak", {}).get("datavalue", {}).get("value")
    except Exception as e:
        print("Error:", e)
    return None

if __name__ == "__main__":
    titles = [
        "Welcome to Samdal-ri",
        "Anna (South Korean TV series)",
        "My Love from the Star",
        "Tale of the Nine Tailed 1938",
        "Today's Webtoon"
    ]
    for t in titles:
        print(t, "-> IMDb ID:", get_imdb_id_from_wiki(t))
