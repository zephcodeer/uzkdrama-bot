import json
import os
import re
import sys
import sqlite3
import urllib.request
import urllib.parse
from PIL import Image
import io

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = r"E:\Agent\Drama Bot"
POSTERS_DIR = os.path.join(BASE_DIR, "posters")
os.makedirs(POSTERS_DIR, exist_ok=True)

OMDB_API_KEY = "bd182e04"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Accurate titles and years for the 64 doramas needing HD posters
QUERY_MAP = {
    129: ("Vincenzo", "2021"),
    138: ("Tale of the Nine Tailed 1938", "2023"),
    168: ("100 Days My Prince", "2018"),
    187: ("Yong-pal", "2015"),
    192: ("Crushology 101", None),
    207: ("Weightlifting Fairy Kim Bok-joo", "2016"),
    214: ("Head Over Heels", "2025"),
    230: ("Dear X", "2025"),
    234: ("Mr. Queen", "2020"),
    239: ("Today's Webtoon", "2022"),
    244: ("Bring It On, Ghost", "2016"),
    245: ("My Royal Nemesis", "2026"),
    247: ("Phantom Lawyer", None),
    248: ("Daily Dose of Sunshine", "2023"),
    249: ("Can This Love Be Translated?", None),
    251: ("If Wishes Could Kill", None),
    252: ("Dream to You", None),
    253: ("Wedding Impossible", "2024"),
    254: ("Love in Sync", None),
    255: ("The Gangster, the Cop, the Devil", "2019"),
    257: ("Love Untangled", "2024"),
    258: ("Drawing Closer", "2024"),
    259: ("Siren's Kiss", None),
    260: ("Nine Puzzles", "2025"),
    261: ("Boyfriend on Demand", None),
    263: ("Our Universe", None),
    264: ("Healer", "2014"),
    265: ("Spring Fever", None),
    266: ("The Art of Sarah", None),
    267: ("Hwarang: The Poet Warrior Youth", "2016"),
    268: ("My Love from the Star", "2013"),
    270: ("The Mermaid Prince", "2020"),
    271: ("Marry YOU", "2024"),
    272: ("Lament of the River Immortal", None),
    273: ("Bloom Again", None),
    275: ("Shooting Stars", "2022"),
    276: ("Spring of Youth", None),
    277: ("Welcome to Samdal-ri", "2023"),
    278: ("Brewing Love", "2024"),
    279: ("It's Okay to Be Sensitive", "2018"),
    280: ("Please Feel at Ease Mr. Ling", "2021"),
    281: ("Family Plan", "2024"),
    282: ("While You Were Sleeping", "2017"),
    283: ("The Universe's Star", "2017"),
    285: ("Spirit Fingers", None),
    286: ("As You Stood By", None),
    287: ("The First Night with the Duke", None),
    288: ("See You in My 19th Life", "2023"),
    289: ("My Deskmate", "2020"),
    290: ("Hong Rang", "2025"),
    291: ("Warm Bodies", "2013"),
    292: ("Omniscient Reader: The Prophecy", "2025"),
    293: ("Anna", "2022"),
    294: ("Connect", "2022"),
    295: ("Tale of the Nine Tailed 1938", "2023"),
    296: ("Doctors", "2016"),
    297: ("Love Reset", "2023"),
    298: ("The Childe", "2023"),
    300: ("Friendly Rivalry", None),
    301: ("My Bias, My Boss", None),
    303: ("The Avengers", "2012"),
    304: ("Avengers Assemble", "2013"),
    305: ("Avengers: Age of Ultron", "2015"),
    306: ("Avengers: Infinity War", "2018"),
    307: ("Avengers: Endgame", "2019"),
    308: ("Page Turner", "2016")
}

def get_omdb_poster_url(title, year=None):
    if not title:
        return None
    params = {"apikey": OMDB_API_KEY, "t": title}
    if year:
        params["y"] = str(year)
    url = f"https://www.omdbapi.com/?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("Response") == "True" and data.get("Poster") and data.get("Poster") != "N/A":
            p = data["Poster"]
            # Amazon CDN HD transformation: strip ._V1_... downscale
            return re.sub(r'\._V1_.*\.jpg$', '._V1_.jpg', p)
    except Exception:
        pass
        
    # Search fallback in OMDB
    try:
        params_s = {"apikey": OMDB_API_KEY, "s": title}
        url_s = f"https://www.omdbapi.com/?{urllib.parse.urlencode(params_s)}"
        req = urllib.request.Request(url_s, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for item in data.get("Search", []):
            if item.get("Poster") and item.get("Poster") != "N/A":
                p = item["Poster"]
                return re.sub(r'\._V1_.*\.jpg$', '._V1_.jpg', p)
    except Exception:
        pass
    return None

def get_wiki_poster_url(page_title):
    if not page_title:
        return None
    url = f"https://en.wikipedia.org/w/api.php?action=parse&page={urllib.parse.quote(page_title)}&prop=wikitext&format=json&redirects=1"
    req = urllib.request.Request(url, headers={"User-Agent": "UzKdramaBot/2.0 (admin@uzkdrama.org)"})
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
        m = re.search(r'\|\s*image\s*=\s*([^|\n\r\}]+)', wikitext, re.IGNORECASE)
        if m:
            img_name = m.group(1).strip()
            img_name = re.sub(r'\[\[File:', '', img_name, flags=re.IGNORECASE)
            img_name = re.sub(r'\[\[Image:', '', img_name, flags=re.IGNORECASE)
            img_name = img_name.split('|')[0].strip()
            if not img_name.startswith("File:"):
                img_name = "File:" + img_name
            info_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(img_name)}&prop=imageinfo&iiprop=url&format=json"
            req2 = urllib.request.Request(info_url, headers={"User-Agent": "UzKdramaBot/2.0 (admin@uzkdrama.org)"})
            with urllib.request.urlopen(req2, timeout=6) as resp2:
                data2 = json.loads(resp2.read().decode("utf-8"))
            pages = data2.get("query", {}).get("pages", {})
            for _, page in pages.items():
                if "imageinfo" in page and len(page["imageinfo"]) > 0:
                    return page["imageinfo"][0].get("url")
    except Exception:
        pass
    return None

def download_and_save(img_url, dest_path):
    req = urllib.request.Request(img_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            raw = resp.read()
        im = Image.open(io.BytesIO(raw))
        w, h = im.size
        ratio = h / w if w > 0 else 0
        if ratio < 1.15:
            return False, f"Landscape image ({w}x{h}, r={ratio:.2f})"
        if w < 350 or h < 500:
            return False, f"Resolution too low ({w}x{h})"
            
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.save(dest_path, "JPEG", quality=92, optimize=True)
        return True, f"{w}x{h} ({round(os.path.getsize(dest_path)/1024, 1)} KB)"
    except Exception as e:
        return False, str(e)

def run_upgrade():
    with open(os.path.join(BASE_DIR, "scripts", "bad_posters.json"), "r", encoding="utf-8") as f:
        bad_items = json.load(f)
        
    print(f"Starting HD poster upgrade for {len(bad_items)} titles...")
    
    success_count = 0
    failed_items = []
    
    for item in bad_items:
        code = item["code"]
        current_poster = item["poster"]
        dest_file = os.path.join(BASE_DIR, current_poster) if not os.path.isabs(current_poster) else current_poster
        
        q_title, q_year = QUERY_MAP.get(code, (None, None))
        if not q_title:
            # Try extract from parentheses
            m = re.search(r'\(([^)]+)\)', item["title"])
            if m:
                q_title = m.group(1).split('/')[0].strip()
            else:
                q_title = item["title"]
                
        # 1. Try OMDB Amazon HQ
        url = get_omdb_poster_url(q_title, q_year)
        source = "OMDB"
        
        # 2. Try Wikipedia
        if not url:
            wiki_queries = [f"{q_title} (TV series)", f"{q_title} (South Korean TV series)", f"{q_title} (film)", q_title]
            for wq in wiki_queries:
                url = get_wiki_poster_url(wq)
                if url:
                    source = f"Wiki ({wq})"
                    break
                    
        if not url:
            failed_items.append((code, item["title"], "NO_URL_FOUND"))
            print(f"[{code}] {item['title']}: No URL found")
            continue
            
        ok, msg = download_and_save(url, dest_file)
        if ok:
            success_count += 1
            print(f"[{code}] SUCCESS ({source}): {item['title']} -> {msg}")
        else:
            failed_items.append((code, item["title"], f"FAIL_DOWNLOAD: {msg} (URL: {url[:60]}...)"))
            print(f"[{code}] FAIL ({source}): {item['title']} -> {msg}")
            
    print(f"\nFinished upgrade: {success_count} succeeded, {len(failed_items)} failed out of {len(bad_items)}")
    if failed_items:
        print("\nFailed items:")
        for code, t, reason in failed_items:
            print(f"  [{code}] {t}: {reason}")

if __name__ == "__main__":
    run_upgrade()
