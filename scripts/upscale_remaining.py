from PIL import Image, ImageEnhance
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = r"E:\Agent\Drama Bot"

low_res_codes = [214, 245, 252, 259, 261, 272, 273, 285, 286, 290, 293]

import sqlite3
con = sqlite3.connect(os.path.join(BASE_DIR, "doramas.db"))
cur = con.cursor()

for code in low_res_codes:
    cur.execute("SELECT title, poster_url FROM doramas WHERE code = ?", (code,))
    row = cur.fetchone()
    if not row:
        continue
    title, rel_p = row
    abs_p = os.path.join(BASE_DIR, rel_p)
    if not os.path.exists(abs_p):
        continue
    
    with Image.open(abs_p) as im:
        if im.mode != "RGB":
            im = im.convert("RGB")
        w, h = im.size
        if w >= 750:
            continue
        # Target width 750, height calculated by ratio
        target_w = 750
        target_h = int(h * (target_w / w))
        
        # Lanczos high quality resample
        upscaled = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        # Gentle sharpen filter
        enhancer = ImageEnhance.Sharpness(upscaled)
        crisp = enhancer.enhance(1.25)
            
        crisp.save(abs_p, "JPEG", quality=93, optimize=True)
        print(f"[{code}] {title}: Upscaled from {w}x{h} -> {crisp.size} ({round(os.path.getsize(abs_p)/1024, 1)} KB)")

con.close()
print("All low-res posters upscaled and sharpened successfully!")
