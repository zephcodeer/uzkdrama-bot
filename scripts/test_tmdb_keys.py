import urllib.request
import urllib.parse
import json

TMDB_KEYS = [
    "b6fbc7f474661413f888823919932c83",
    "45bf6592c14a565b9cc1e8b731600db9",
    "3f2f01f059e0a0589d311357065910fa",
    "2b634891b98a0026e6d1eb2b896934c9",
    "15d2ade0fe30ec7fe38b527d2c504319"
]

def test_tmdb_keys():
    for key in TMDB_KEYS:
        url = f"https://api.themoviedb.org/3/search/tv?api_key={key}&query=Vincenzo"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                results = data.get("results", [])
                if results:
                    poster = results[0].get("poster_path")
                    print(f"Key {key} SUCCESS! Poster: https://image.tmdb.org/t/p/w780{poster}")
                    return key
        except Exception as e:
            print(f"Key {key} failed: {e}")
    return None

if __name__ == "__main__":
    working_key = test_tmdb_keys()
    print("Working key:", working_key)
