import sqlite3
import os
import sys
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

con = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
con.row_factory = sqlite3.Row
cur = con.cursor()
cur.execute("SELECT code, title, poster_url FROM doramas ORDER BY code ASC")
doramas = cur.fetchall()

for d in doramas:
    p = os.path.join(r"E:\Agent\Drama Bot", d["poster_url"])
    if not os.path.exists(p):
        continue
    with Image.open(p) as im:
        w, h = im.size
        ratio = h / w if w > 0 else 0
        if ratio < 1.15 or (w < 350 or h < 500):
            print(f"[{d['code']}] {d['title']} -> {w}x{h} (ratio: {ratio:.2f})")
