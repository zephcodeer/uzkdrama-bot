import urllib.request
import re
import html as html_lib
import time
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://uzmovi.me/'
}

TARGET_TITLES = [
    "oltin qoshiq", "alvon yuraklar", "biz barchamiz", "yovuzlarning",
    "darbadar ruh", "pinokkio", "baxt", "biznes taklifi", "notanishlar",
    "aqldan ozgan", "bezori", "doona", "k2", "ajal", "sichqon",
    "tulki", "ovchi itlar", "orol", "qish sonatasi", "samoviy ishq", "vorislar",
    "sudya", "qotillar", "qasosi", "notanish doktor", "mening ismim",
    "asl gozallik", "vinchenzo", "goblin", "hushyor", "tarvuz", "tun kirganda", "doktor slump"
]

found_doramas = {}

print("Scanning uzmovi.me serial catalog...")
for page in range(1, 35):
    url = f"https://uzmovi.me/seriall/page/{page}/" if page > 1 else "https://uzmovi.me/seriall/"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', 'ignore')
            items = re.findall(r'href="(https://uzmovi\.me/seriall/[^"]+)"[^>]*>([^<]+)</a>', html)
            for link, title_raw in items:
                title_clean = html_lib.unescape(title_raw).strip()
                t_lower = title_clean.lower()
                for t in TARGET_TITLES:
                    if t in t_lower and link not in found_doramas:
                        found_doramas[link] = (title_clean, t)
                        print(f"TOPILDI [{t.upper()}]: {title_clean} -> {link}")
    except Exception as e:
        pass
    time.sleep(0.3)

print(f"\nJami topildi: {len(found_doramas)} ta mos dorama.")
