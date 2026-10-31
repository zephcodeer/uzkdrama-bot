import json, re, sys, os, urllib.request, urllib.error, ssl, io, time
from PIL import Image, ImageOps

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\Agent\Drama Bot')

HTML_PATH = r'E:\I\PROFILE\PROFILE LIVE\The News\uzkdrama_barcha_129_ta_drama_hd_posterlar_markazi_FIXED.html'
POSTERS_DIR = os.path.join(r'E:\Agent\Drama Bot', 'posters')
os.makedirs(POSTERS_DIR, exist_ok=True)

# 1. Parse DRAMAS_DATA from HTML
with open(HTML_PATH, 'r', encoding='utf-8') as f:
    html_text = f.read()

m = re.search(r'const\s+DRAMAS_DATA\s*=\s*(\[\s*\{[\s\S]*?\}\s*\]);', html_text)
if not m:
    print("Could not find DRAMAS_DATA in HTML!")
    sys.exit(1)

dramas_data = json.loads(m.group(1))
print(f"Loaded {len(dramas_data)} curated dramas from HTML.")

# 2. Setup download session
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://asianwiki.com/"
}

import sqlite3
conn = sqlite3.connect(r'E:\Agent\Drama Bot\doramas.db')
c = conn.cursor()

success_count = 0
failed_count = 0

print("Starting download and application of all 129 curated HD posters...")

for idx, item in enumerate(dramas_data, start=1):
    code = int(item["code"])
    name = item["name"].strip()
    canon_name = item.get("canon_name", "").strip()
    year = int(item.get("year", 2024))
    url = item.get("poster", "").strip()

    poster_filename = f"code_{code}.jpg"
    poster_path = os.path.join(POSTERS_DIR, poster_filename)

    downloaded = False
    if url and url.startswith("http"):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
                raw_bytes = resp.read()
                if len(raw_bytes) > 1000:
                    img = Image.open(io.BytesIO(raw_bytes))
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    # Fit to 500x750 high quality
                    fitted_img = ImageOps.fit(img, (500, 750), method=Image.Resampling.LANCZOS)
                    fitted_img.save(poster_path, "JPEG", quality=92, optimize=True)
                    downloaded = True
        except Exception as e:
            print(f"[{code}] Download error for {url}: {e}")

    if downloaded:
        success_count += 1
        print(f"[{idx:3}/129] Code {code}: {name[:35]:<35} -> OK ({os.path.getsize(poster_path):,} bytes)")
    else:
        failed_count += 1
        print(f"[{idx:3}/129] Code {code}: {name[:35]:<35} -> KEPT EXISTING PLACEHOLDER")

    # Update database
    # Get existing aliases
    c.execute("SELECT aliases FROM doramas WHERE code = ?", (code,))
    row = c.fetchone()
    current_aliases = row[0] if row else ""

    # Merge canon_name into aliases
    aliases_list = [a.strip() for a in current_aliases.split(",") if a.strip()]
    if canon_name and canon_name.lower() not in [a.lower() for a in aliases_list]:
        aliases_list.append(canon_name)
    merged_aliases = ", ".join(aliases_list)

    c.execute("""
        UPDATE doramas
        SET title = ?,
            year = ?,
            aliases = ?,
            poster_url = ?
        WHERE code = ?
    """, (name, year, merged_aliases, f"posters/{poster_filename}", code))

conn.commit()
print(f"\nCompleted! Downloaded and applied: {success_count} / 129 (Failed/Fallback: {failed_count})")

# 3. Update YANGI_DRAMALAR_ROYXATI.txt
c.execute("""
    SELECT code, title, year, total_episodes, status
    FROM doramas
    WHERE code >= 351
    ORDER BY code ASC
""")
new_rows = c.fetchall()

yangi_file = r"E:\Agent\Drama Bot\YANGI_DRAMALAR_ROYXATI.txt"
with open(yangi_file, "w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write(f"UZKDRAMA BOT — YANGI QO'SHILGAN DRAMALAR (JAMI: {len(new_rows)} TA | KODLAR: 351-479)\n")
    f.write("=" * 80 + "\n")
    f.write(f"{'KOD':<6} | {'NOMI':<46} | {'YILI':<6} | {'QISMLAR':<12} | {'STATUS':<12}\n")
    f.write("-" * 80 + "\n")
    for r in new_rows:
        code_val, title_val, year_val, total_ep, status_val = r
        qism_str = f"{total_ep}/{total_ep}"
        f.write(f"{code_val:<6} | {title_val[:46]:<46} | {year_val:<6} | {qism_str:<12} | {status_val:<12}\n")

print(f"Updated {yangi_file}")

# 4. Update DRAMALAR_ROYXATI.txt
c.execute("""
    SELECT d.code, d.title, d.year, COUNT(e.id) as real_eps, d.total_episodes, d.status
    FROM doramas d
    LEFT JOIN episodes e ON d.id = e.dorama_id
    GROUP BY d.id
    ORDER BY d.code ASC
""")
all_rows = c.fetchall()

master_file = r"E:\Agent\Drama Bot\DRAMALAR_ROYXATI.txt"
with open(master_file, "w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write(f"UZKDRAMA BOT — BARCHA DRAMALAR RO'YXATI (JAMI: {len(all_rows)} TA)\n")
    f.write("=" * 80 + "\n")
    f.write(f"{'KOD':<6} | {'NOMI':<46} | {'YILI':<6} | {'QISMLAR':<12} | {'STATUS':<12}\n")
    f.write("-" * 80 + "\n")
    for r in all_rows:
        code_val, title_val, year_val, real_cnt, total_ep, status_val = r
        ep_display = f"{real_cnt}/{total_ep}"
        f.write(f"{code_val:<6} | {title_val[:46]:<46} | {year_val:<6} | {ep_display:<12} | {status_val:<12}\n")

print(f"Updated {master_file} (Total: {len(all_rows)} doramas)")
conn.close()
