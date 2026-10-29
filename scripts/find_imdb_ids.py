import urllib.request
import urllib.parse
import re

queries = [
    "Welcome to Samdal-ri imdb tt",
    "Anna 2022 bae suzy imdb tt",
    "My Love from the Star 2013 imdb tt",
    "Tale of the Nine Tailed 1938 imdb tt",
    "Today's Webtoon imdb tt",
    "Dear Hongrang imdb tt"
]

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
for q in queries:
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        m = re.findall(r'title/(tt\d+)', html)
        if m:
            print(q, "->", list(dict.fromkeys(m))[:3])
        else:
            print(q, "-> None")
    except Exception as e:
        print(q, "-> Error:", e)
