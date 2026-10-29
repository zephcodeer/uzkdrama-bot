import urllib.request
import urllib.parse
import json
import re

OMDB_API_KEY = "bd182e04"

def get_omdb_by_id(imdb_id):
    url = f"https://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        if data.get("Poster") and data.get("Poster") != "N/A":
            return re.sub(r'\._V1_.*\.jpg$', '._V1_.jpg', data["Poster"]), data.get("Title")
    except Exception as e:
        return None, str(e)
    return None, "No poster"

def search_omdb(query):
    url = f"https://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        return [(item["Title"], item["Year"], item["imdbID"], item.get("Poster")) for item in data.get("Search", [])]
    except Exception as e:
        return [str(e)]

if __name__ == "__main__":
    queries = [
        "Tale of the Nine Tailed",
        "My Love from the Star",
        "Welcome to Samdal-ri",
        "Anna",
        "Today's Webtoon",
        "Head over Heels"
    ]
    for q in queries:
        print(q, "->", search_omdb(q)[:3])
