import sqlite3
import json
import os
import sys
import base64
import io
import shutil
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HTML_PATH = r"c:\Users\MuhammadSodiq\Downloads\uzkdrama_246_posterlar_tuzatilgan.html"
BASE_DIR = r"E:\Agent\Drama Bot"
DB_PATH = os.path.join(BASE_DIR, "doramas.db")
BACKUP_DB = os.path.join(BASE_DIR, "doramas.db.backup_pre_246_posters")
POSTERS_DIR = os.path.join(BASE_DIR, "posters")

def slugify(text):
    clean = ""
    for c in text.lower().strip():
        if c.isalnum() or c in (" ", "-", "_"):
            clean += c
    clean = "-".join(clean.split())
    return clean[:40] or "poster"

print("=" * 60)
print("1-BOSQICH: Zaxira nusxa yaratish va faylni o'qish...")
print("=" * 60)

# 1. Backup DB
shutil.copy2(DB_PATH, BACKUP_DB)
print(f"Zaxira nusxa saqlandi: {BACKUP_DB}")

# 2. Read HTML and parse DRAMAS_DATA & EMBEDDED_POSTERS
with open(HTML_PATH, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

s_dd = content.find("const DRAMAS_DATA = [")
e_dd = content.find("];", s_dd)
dramas_data = json.loads(content[s_dd+20:e_dd+1])

s_ep = content.find("const EMBEDDED_POSTERS = {")
e_ep = content.find("};", s_ep)
embedded_posters = json.loads(content[s_ep+25:e_ep+1])

print(f"DRAMAS_DATA: {len(dramas_data)} ta dorama ma'lumotlari topildi.")
print(f"EMBEDDED_POSTERS: {len(embedded_posters)} ta tayyor tuzatilgan poster topildi.")

dramas_by_code = {int(d["code"]): d for d in dramas_data}

# 3. Connect to DB
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("\n" + "=" * 60)
print("2-BOSQICH: Posterlarni dekodlash va bazani yangilash...")
print("=" * 60)

success_count = 0
error_count = 0
alias_updates = 0

# Sort by code ascending
sorted_codes = sorted([int(k) for k in embedded_posters.keys()])

for idx, code in enumerate(sorted_codes, 1):
    b64_str = embedded_posters[str(code)]
    d_meta = dramas_by_code.get(code, {})
    canon_name = d_meta.get("canon_name", "").strip()

    c.execute("SELECT id, title, poster_url, aliases FROM doramas WHERE code = ?", (code,))
    row = c.fetchone()

    if not row:
        print(f"[#{code}] Bazada topilmadi, o'tkazib yuborildi.")
        continue

    d_id, title, curr_poster_rel, curr_aliases = row

    try:
        # Decode base64 image
        if ";base64," in b64_str:
            b64_data = b64_str.split(";base64,")[1]
        else:
            b64_data = b64_str

        raw_bytes = base64.b64decode(b64_data)
        img = Image.open(io.BytesIO(raw_bytes))

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Determine target file path
        if curr_poster_rel and curr_poster_rel.startswith("posters/"):
            dest_rel = curr_poster_rel
        else:
            slug = slugify(title)
            dest_rel = f"posters/{code}_{slug}.jpg"

        dest_abs = os.path.join(BASE_DIR, dest_rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(dest_abs), exist_ok=True)

        # Save image in high quality
        img.save(dest_abs, "JPEG", quality=92, optimize=True)

        # Merge canon_name into aliases if not already present
        new_aliases = curr_aliases or ""
        if canon_name and canon_name.lower() not in (curr_aliases or "").lower():
            if new_aliases:
                new_aliases = f"{new_aliases}, {canon_name}"
            else:
                new_aliases = canon_name
            alias_updates += 1

        c.execute("""
            UPDATE doramas 
            SET poster_url = ?, aliases = ?
            WHERE id = ?
        """, (dest_rel, new_aliases, d_id))

        success_count += 1
        if idx % 25 == 0 or idx == len(sorted_codes):
            print(f"  [{idx:3d}/{len(sorted_codes)}] #{code:3d} «{title[:30]}» -> {dest_rel} ({img.size[0]}x{img.size[1]}) ✅")

    except Exception as ex:
        print(f"[#{code}] XATOLIK: {ex}")
        error_count += 1

conn.commit()
conn.close()

print("\n" + "=" * 60)
print("XULOSA:")
print(f"  ✅ Muvaffaqiyatli yangilangan posterlar: {success_count} / {len(sorted_codes)}")
print(f"  🔍 Aliases boyitilgan: {alias_updates} ta dorama")
print(f"  ❌ Xatolar: {error_count} ta")
print("=" * 60)
