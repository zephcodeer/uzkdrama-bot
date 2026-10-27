import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
req = urllib.request.Request('https://asilmedia.biz/load/serialy/tarzhima_serial_tarjima_seriallar/doktor_x_barcha_qismlari_uzbek_tilida/7-1-0-1457', headers=headers)
with urllib.request.urlopen(req) as r:
    html = r.read().decode('utf-8', 'ignore')

print("Searching Asilmedia buttons/episodes:")
for line in html.splitlines():
    if any(k in line.lower() for k in ['qism', 'mover.uz', 'player', 'change']):
        if any(c in line for c in ['http', 'onclick', 'data-']):
            print(line.strip()[:140])
