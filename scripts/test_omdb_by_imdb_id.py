import urllib.request
import json
import re

OMDB_API_KEY = "bd182e04"

ids = {
    "Welcome to Samdal-ri": "tt26653824",
    "Anna": "tt21146902",
    "My Love from the Star": "tt3469052",
    "Tale of the Nine Tailed 1938": "tt27329405",
    "Today's Webtoon": "tt21222278"
}

for name, imdb_id in ids.items():
    url = f"https://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    poster = data.get("Poster")
    if poster and poster != "N/A":
        hd_poster = re.sub(r'\._V1_.*\.jpg$', '._V1_.jpg', poster)
        print(f"{name} ({imdb_id}) -> {hd_poster}")
    else:
        print(f"{name} ({imdb_id}) -> No poster")
