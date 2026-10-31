import sqlite3
import urllib.request
import urllib.parse
import json
import os
from concurrent.futures import ThreadPoolExecutor

DB_PATH = "doramas.db"
OUTPUT_HTML = "poster_curator.html"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""
    SELECT code, title, year, genre, poster_url, aliases
    FROM doramas
    ORDER BY code DESC
""")
rows = c.fetchall()
conn.close()

print(f"Bazada jami {len(rows)} ta dorama topildi. TVMaze va iTunes orqali qidiruv boshlanmoqda...")

def fetch_alternative_poster(row):
    code, title, year, genre, poster_a, aliases = row
    
    # Specific known mappings
    if code == 346:
        return code, "https://m.media-amazon.com/images/M/MV5BYmNjNTMyMWQtYmViNi00YWYxLWEzZTctNDQ2MTdhNzU2OTVlXkEyXkFqcGc@._V1_QL75_UY562_CR7,0,380,562_.jpg"
    elif code == 345:
        return code, "https://static.tvmaze.com/uploads/images/original_untouched/486/1215665.jpg"
    elif code == 121:
        return code, "https://m.media-amazon.com/images/M/MV5BYzA2ZWI2NmYtNTBhZS00Y2E3LTgyNWQtNDZlMTAxNDFhODRkXkEyXkFqcGc@._V1_.jpg"

    queries = []
    if "(" in title and ")" in title:
        queries.append(title[title.rfind("(") + 1 : title.rfind(")")].strip())

    if aliases:
        for a in aliases.split(","):
            a_clean = a.strip()
            if a_clean and len(a_clean) > 2:
                queries.append(a_clean)
                break

    clean_t = title.split("(")[0].split("-")[0].split(",")[0].strip()
    queries.append(clean_t)

    # 1. TVMaze Search (Unlimited, Free, Original HD)
    for q in queries:
        try:
            url = f"https://api.tvmaze.com/search/shows?q={urllib.parse.quote(q)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode())
                if data and data[0].get("show", {}).get("image"):
                    img = data[0]["show"]["image"].get("original") or data[0]["show"]["image"].get("medium")
                    if img:
                        return code, img
        except Exception:
            pass

    # 2. iTunes Search (High-res 1000x1500 artwork)
    for q in queries[:2]:
        try:
            url = f"https://itunes.apple.com/search?term={urllib.parse.quote(q)}&media=tvShow&limit=1"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode())
                if data.get("results") and data["results"][0].get("artworkUrl100"):
                    img = data["results"][0]["artworkUrl100"].replace("100x100bb.jpg", "1000x1500bb.jpg")
                    return code, img
        except Exception:
            pass

    return code, None

alt_posters = {}
with ThreadPoolExecutor(max_workers=12) as executor:
    for code, alt_url in executor.map(fetch_alternative_poster, rows):
        if alt_url:
            alt_posters[code] = alt_url

print(f"Jami {len(alt_posters)} / {len(rows)} ta dorama uchun muqobil (Option B) posterlar topildi!")

# Assemble dataset for HTML
dataset = []
for r in rows:
    code, title, year, genre, poster_a, aliases = r
    poster_b = alt_posters.get(code, "")
    dataset.append({
        "code": code,
        "title": title,
        "year": year or 2024,
        "genre": genre or "Dorama",
        "poster_a": poster_a,
        "poster_b": poster_b,
        "aliases": aliases or ""
    })

dataset_json = json.dumps(dataset, ensure_ascii=False)

# Read HTML template from existing or write clean
with open("poster_curator.html", "r", encoding="utf-8") as f:
    existing_html = f.read()

# Replace dataset in HTML
idx_start = existing_html.find("const DORAMAS = ") + len("const DORAMAS = ")
idx_end = existing_html.find(";\n\n        const SVG_NO_ALT = ", idx_start)
if idx_end == -1:
    idx_end = existing_html.find(";\n", idx_start)

updated_html = existing_html[:idx_start] + dataset_json + existing_html[idx_end:]

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(updated_html)

print(f"SUCCESS: {OUTPUT_HTML} muvaffaqiyatli yangilandi!")
