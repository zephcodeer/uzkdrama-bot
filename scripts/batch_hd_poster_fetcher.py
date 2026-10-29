import json
import os
import re
import sys
import urllib.request
import urllib.parse
from PIL import Image
import io

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POSTERS_DIR = r"E:\Agent\Drama Bot\posters"
OMDB_API_KEY = "bd182e04"

# Manual mapping for titles where English title is nuanced or special
SPECIAL_MAPPINGS = {
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
    292: ("Omniscient Reader", "2025"),
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

def fetch_omdb_poster(search_title, year=None):
    params = {"apikey": OMDB_API_KEY, "t": search_title}
    if year:
        params["y"] = str(year)
    url = f"https://www.omdbapi.com/?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=7) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("Response") == "True" and data.get("Poster") and data.get("Poster") != "N/A":
            p_url = data["Poster"]
            # Convert to Amazon original HQ resolution
            hd_url = re.sub(r'\._V1_.*\.jpg$', '._V1_.jpg', p_url)
            return hd_url, data.get("Title"), data.get("Year")
    except Exception as e:
        pass
    
    # Try search query if direct title failed
    try:
        params_s = {"apikey": OMDB_API_KEY, "s": search_title}
        url_s = f"https://www.omdbapi.com/?{urllib.parse.urlencode(params_s)}"
        req = urllib.request.Request(url_s, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=7) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for item in data.get("Search", []):
            if item.get("Poster") and item.get("Poster") != "N/A":
                p_url = item["Poster"]
                hd_url = re.sub(r'\._V1_.*\.jpg$', '._V1_.jpg', p_url)
                return hd_url, item.get("Title"), item.get("Year")
    except Exception:
        pass
        
    return None, None, None

def download_and_verify_image(url, save_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = resp.read()
        im = Image.open(io.BytesIO(data))
        w, h = im.size
        ratio = h / w if w > 0 else 0
        if w < 400 or h < 600 or ratio < 1.15:
            return False, f"Too small or landscape: {w}x{h} (r={ratio:.2f})"
        
        # Save as optimized JPEG
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.save(save_path, "JPEG", quality=92)
        return True, f"{w}x{h} ({round(len(data)/1024, 1)} KB)"
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    test_codes = [129, 207, 264, 267, 268, 282, 296, 303, 305, 306, 307, 308]
    print(f"Testing HQ fetch on {len(test_codes)} famous titles...")
    for code in test_codes:
        title, year = SPECIAL_MAPPINGS.get(code, (None, None))
        hd_url, omdb_title, omdb_year = fetch_omdb_poster(title, year)
        print(f"[{code}] {title} ({year}) -> OMDB: {omdb_title} ({omdb_year})")
        if hd_url:
            print(f"    HD URL: {hd_url}")
        else:
            print("    NOT FOUND ON OMDB")
