import urllib.request
import urllib.parse
import json

OMDB_API_KEY = "bd182e04"

def test_omdb(title, year=None):
    params = {"apikey": OMDB_API_KEY, "t": title}
    if year:
        params["y"] = year
    url = f"https://www.omdbapi.com/?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        return data.get("Title"), data.get("Year"), data.get("Poster")
    except Exception as e:
        return None, None, str(e)

if __name__ == "__main__":
    for t, y in [("Vincenzo", "2021"), ("Healer", "2014"), ("Avengers: Endgame", "2019"), ("The Avengers", "2012"), ("While You Were Sleeping", "2017")]:
        print(t, "->", test_omdb(t, y))
