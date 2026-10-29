import urllib.request
import urllib.parse
import json
import re

def get_wikipedia_infobox_image(page_title):
    headers = {"User-Agent": "UzKdramaBot/2.0 (admin@uzkdrama.org)"}
    # First get the page wikitext or parse the infobox
    url = f"https://en.wikipedia.org/w/api.php?action=parse&page={urllib.parse.quote(page_title)}&prop=wikitext&format=json&redirects=1"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
    except Exception as e:
        return None, f"Parse error: {e}"
        
    m = re.search(r'\|\s*image\s*=\s*([^|\n\r\}]+)', wikitext, re.IGNORECASE)
    if not m:
        return None, "No image in infobox"
    
    image_name = m.group(1).strip()
    image_name = re.sub(r'\[\[File:', '', image_name, flags=re.IGNORECASE)
    image_name = re.sub(r'\[\[Image:', '', image_name, flags=re.IGNORECASE)
    image_name = image_name.split('|')[0].strip()
    if not image_name.startswith("File:"):
        image_name = "File:" + image_name
        
    # Now get direct original image URL
    info_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(image_name)}&prop=imageinfo&iiprop=url|size&format=json"
    req2 = urllib.request.Request(info_url, headers=headers)
    try:
        with urllib.request.urlopen(req2, timeout=6) as resp2:
            data2 = json.loads(resp2.read().decode("utf-8"))
        pages = data2.get("query", {}).get("pages", {})
        for _, page in pages.items():
            if "imageinfo" in page and len(page["imageinfo"]) > 0:
                info = page["imageinfo"][0]
                return info.get("url"), f"{info.get('width')}x{info.get('height')}"
    except Exception as e:
        return None, f"Info error: {e}"
        
    return None, "Not found"

if __name__ == "__main__":
    tests = [
        "Vincenzo (TV series)",
        "Healer (TV series)",
        "Hwarang: The Poet Warrior Youth",
        "My Love from the Star",
        "While You Were Sleeping (2017 TV series)",
        "The Avengers (2012 film)",
        "Avengers: Age of Ultron",
        "Avengers: Infinity War",
        "Avengers: Endgame",
        "Doctors (South Korean TV series)",
        "Welcome to Samdal-ri",
        "Tale of the Nine Tailed 1938",
        "Page Turner (TV series)",
        "Daily Dose of Sunshine",
        "The Gangster, the Cop, the Devil",
        "Connect (TV series)",
        "Warm Bodies (film)",
        "Love Reset",
        "The Childe"
    ]
    for t in tests:
        url, meta = get_wikipedia_infobox_image(t)
        print(f"{t} -> {meta} | {url}")
