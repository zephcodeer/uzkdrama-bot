import sqlite3
import os
import sys
from PIL import Image, ImageOps

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect(r'E:\Agent\Drama Bot\doramas.db')
c = conn.cursor()

BASE_DIR = r'E:\Agent\Drama Bot'
POSTERS_DIR = os.path.join(BASE_DIR, 'posters')
THUMBS_DIR = os.path.join(BASE_DIR, 'channel_thumbs')

print("=== STARTING MASTER POSTER & METADATA APPLICATION ===")

# Helper to merge aliases
def merge_alias(current_aliases, new_items):
    curr = [a.strip() for a in current_aliases.split(',') if a.strip()]
    for item in new_items:
        if item and item.lower() not in [x.lower() for x in curr]:
            curr.append(item)
    return ", ".join(curr)

# 1. CODE 419: Mo'jizakor telbalar (The WONDERfools)
print("\n[1] Updating Code 419: Mo'jizakor telbalar (The WONDERfools)...")
c.execute("SELECT aliases FROM doramas WHERE code = 419")
row = c.fetchone()
curr_aliases_419 = row[0] if row else ""
new_aliases_419 = merge_alias(curr_aliases_419, ["The WONDERfools", "Wonderfools", "원더풀스", "Park Eun-bin", "Cha Eun-woo", "Kim Hae-sook"])

c.execute("""
    UPDATE doramas
    SET title = ?,
        aliases = ?,
        year = ?,
        genre = ?,
        actors = ?,
        description = ?,
        poster_url = ?
    WHERE code = 419
""", (
    "Mo’jizakor telbalar (The WONDERfools)",
    new_aliases_419,
    2026,
    "Komediya, Fantastika, Sarguzasht, Jangari",
    "Park Eun-bin, Cha Eun-woo, Kim Hae-sook, Choi Dae-hoon, Im Sung-jae",
    "1999-yil arafasida Haeseong shahrida oddiy fuqarolar kutilmagan g'ayritabiiy hodisa sabab superqobiliyatlarga ega bo'lib qolishadi. Ammo ularning qobiliyatlari nuqsonli va kulgili bo'lib, shaharni yovuzlardan himoya qilish uchun birlashishga majbur bo'ladilar.",
    "posters/code_419.jpg"
))
print("   -> Code 419 updated successfully.")

# 2. CODE 118: Ovchi itlar 1-fasl
print("\n[2] Updating Code 118: Ovchi itlar 1-fasl...")
c.execute("""
    UPDATE doramas
    SET poster_url = 'posters/ovchi_itlar_s1.jpg'
    WHERE code = 118
""")
print("   -> Code 118 poster_url pointed to posters/ovchi_itlar_s1.jpg.")

# 3. CODE 316: Tabassumingga oshiqman (Falling Into Your Smile)
print("\n[3] Updating Code 316: Tabassumingga oshiqman (Falling Into Your Smile)...")
c.execute("""
    UPDATE doramas
    SET title = ?,
        aliases = ?,
        year = ?,
        genre = ?,
        actors = ?,
        description = ?,
        poster_url = ?
    WHERE code = 316
""", (
    "Tabassumingga oshiqman (Falling Into Your Smile)",
    "Tabassumingga oshiqman, Falling Into Your Smile, Ni Wei Xiao Shi Hen Mei, Xu Kai, Cheng Xiao, 你微笑时很美",
    2021,
    "Romantika, Komediya, E-sport, Drama",
    "Xu Kai, Cheng Xiao, Zhai Xiaowen, Yao Chi, Zhou Yiran",
    "E-sport bo'yicha professional OPL ligasiga qo'shilgan birinchi ayol kiber-sportchi Tong Yao va jamoa sardori Lu Sicheng o'rtasidagi raqobat va shirin sevgi qissasi.",
    "posters/tabassumingga-oshiqman.jpg"
))
print("   -> Code 316 updated successfully.")

# 4. CODE 246 & 295 & 332: De-duplicate earlier posters using authentic channel thumbs
print("\n[4] Updating earlier duplicates (246, 295, 332)...")
earlier_thumbs = [
    (246, 'posters/haqiqiy-talim-study-group.jpg'),
    (295, 'posters/kumixo-1938.jpg'),
    (332, 'posters/mukammal-toj-perfect-crown.jpg')
]
for code, target_rel in earlier_thumbs:
    tpath = os.path.join(THUMBS_DIR, f"thumb_code_{code}.jpg")
    out_path = os.path.join(BASE_DIR, target_rel)
    if os.path.exists(tpath):
        im = Image.open(tpath).convert("RGB")
        fitted = ImageOps.fit(im, (500, 750), method=Image.Resampling.LANCZOS)
        fitted.save(out_path, "JPEG", quality=92, optimize=True)
        c.execute("UPDATE doramas SET poster_url = ? WHERE code = ?", (target_rel, code))
        print(f"   -> Code {code} thumb fitted to {target_rel}")
    else:
        print(f"   -> Code {code} thumb not found on disk!")

# 5. CODE 364: Iljimae
print("\n[5] Updating Code 364: Qasos: Iljimae...")
c.execute("SELECT aliases FROM doramas WHERE code = 364")
row = c.fetchone()
curr_aliases_364 = row[0] if row else ""
new_aliases_364 = merge_alias(curr_aliases_364, ["Iljimae", "The Return of Iljimae", "Lee Joon-gi", "Han Hyo-joo", "Qasos Iljimae"])
c.execute("""
    UPDATE doramas
    SET title = 'Qasos: Iljimae (Iljimae)',
        aliases = ?,
        year = 2008,
        poster_url = 'posters/code_364.jpg'
    WHERE code = 364
""", (new_aliases_364,))

# 6. CODE 402: Pavan (Bajrangi Bhaijaan)
print("\n[6] Updating Code 402: Pavan (Bajrangi Bhaijaan)...")
c.execute("SELECT aliases FROM doramas WHERE code = 402")
row = c.fetchone()
curr_aliases_402 = row[0] if row else ""
new_aliases_402 = merge_alias(curr_aliases_402, ["Bajrangi Bhaijaan", "Pavan", "Salman Khan", "Kareena Kapoor", "Harshaali Malhotra"])
c.execute("""
    UPDATE doramas
    SET title = 'Pavan: Bajrangi birodar (Bajrangi Bhaijaan)',
        aliases = ?,
        year = 2015,
        poster_url = 'posters/code_402.jpg'
    WHERE code = 402
""", (new_aliases_402,))

# 7. CODE 448: Baxt Taomi (Pasta)
print("\n[7] Updating Code 448: Baxt Taomi (Pasta)...")
c.execute("SELECT aliases FROM doramas WHERE code = 448")
row = c.fetchone()
curr_aliases_448 = row[0] if row else ""
new_aliases_448 = merge_alias(curr_aliases_448, ["Pasta", "Baxt taomi", "Lee Sun-kyun", "Gong Hyo-jin"])
c.execute("""
    UPDATE doramas
    SET title = 'Baxt Taomi (Pasta)',
        aliases = ?,
        year = 2010,
        poster_url = 'posters/code_448.jpg'
    WHERE code = 448
""", (new_aliases_448,))

# 8. CODE 452 & 453: Yovuz va badavlat (Bitch X Rich)
print("\n[8] Updating Code 452 & 453: Yovuz va badavlat (Bitch X Rich)...")
c.execute("SELECT aliases FROM doramas WHERE code = 452")
row = c.fetchone()
new_aliases_452 = merge_alias(row[0] if row else "", ["Bitch X Rich", "Cheongdam International High School", "Yeri", "Lee Eun-saem"])
c.execute("""
    UPDATE doramas
    SET title = 'Yovuz va badavlat 1-fasl (Bitch X Rich)',
        aliases = ?,
        year = 2023,
        poster_url = 'posters/code_452.jpg'
    WHERE code = 452
""", (new_aliases_452,))

c.execute("SELECT aliases FROM doramas WHERE code = 453")
row = c.fetchone()
new_aliases_453 = merge_alias(row[0] if row else "", ["Bitch X Rich Season 2", "Cheongdam International High School 2"])
c.execute("""
    UPDATE doramas
    SET title = 'Yovuz va badavlat 2-fasl (Bitch X Rich Season 2)',
        aliases = ?,
        year = 2024,
        poster_url = 'posters/code_453.jpg'
    WHERE code = 453
""", (new_aliases_453,))

# 9. Additional OMDB verified metadata updates
omdb_meta_updates = [
    (354, ["Scent of Time", "Zhou Ye", "Wang Xingyue"]),
    (363, ["Blue Birthday", "Yeri", "Hongseok"]),
    (367, ["The Blooms at Ruyi Pavilion", "Ju Jingyi", "Zhang Zhehan"]),
    (374, ["My Journey to You", "Yun Zhi Yu", "Esther Yu", "Zhang Linghe"]),
    (376, ["Unforgettable Love", "Miles Wei", "Hu Yixuan"]),
    (384, ["Minamahal"]),
    (385, ["Even If This Love Disappears from the World Tonight", "Shunsuke Michieda", "Riko Fukumoto"]),
    (393, ["Amidst a Snowstorm of Love", "Leo Wu", "Zhao Jinmai"]),
    (395, ["Better Days", "Zhou Dongyu", "Jackson Yee"]),
    (400, ["The Story of Pearl Girl", "Zhao Lusi", "Liu Yuning"]),
]
for code, aliases_to_add in omdb_meta_updates:
    c.execute("SELECT aliases FROM doramas WHERE code = ?", (code,))
    row = c.fetchone()
    if row:
        updated_aliases = merge_alias(row[0], aliases_to_add)
        c.execute("UPDATE doramas SET aliases = ?, poster_url = ? WHERE code = ?", (updated_aliases, f"posters/code_{code}.jpg", code))

# 10. Replace all remaining hallucinated/duplicate posters in 351-479 with fitted authentic channel thumbnails
print("\n[10] Applying fitted channel thumbnails for all remaining mismatched/duplicate doramas...")
thumb_target_codes = [
    351, 356, 360, 361, 365, 371, 372, 373, 375, 377, 380, 382, 389, 390, 391,
    401, 403, 404, 406, 407, 409, 410, 412, 413, 414, 415, 416, 418, 420, 421,
    425, 426, 427, 429, 430, 432, 434, 435, 436, 437, 438, 439, 440, 442, 447,
    449, 450, 453, 456, 459, 460, 462, 463, 464, 467, 469, 470, 472, 473, 474,
    475, 476, 478
]

applied_thumbs = 0
for code in thumb_target_codes:
    tpath = os.path.join(THUMBS_DIR, f"thumb_code_{code}.jpg")
    out_path = os.path.join(POSTERS_DIR, f"code_{code}.jpg")
    if os.path.exists(tpath):
        im = Image.open(tpath).convert("RGB")
        fitted = ImageOps.fit(im, (500, 750), method=Image.Resampling.LANCZOS)
        fitted.save(out_path, "JPEG", quality=92, optimize=True)
        c.execute("UPDATE doramas SET poster_url = ? WHERE code = ?", (f"posters/code_{code}.jpg", code))
        applied_thumbs += 1

print(f"   -> Applied authentic channel thumbs to {applied_thumbs} / {len(thumb_target_codes)} doramas.")

conn.commit()
print("\nDatabase committed successfully!")

# 11. Regenerate YANGI_DRAMALAR_ROYXATI.txt
c.execute("""
    SELECT code, title, year, total_episodes, status
    FROM doramas
    WHERE code >= 351
    ORDER BY code ASC
""")
new_rows = c.fetchall()

yangi_file = os.path.join(BASE_DIR, "YANGI_DRAMALAR_ROYXATI.txt")
with open(yangi_file, "w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write(f"UZKDRAMA BOT — YANGI QO'SHILGAN DRAMALAR (JAMI: {len(new_rows)} TA | KODLAR: 351-481)\n")
    f.write("=" * 80 + "\n")
    f.write(f"{'KOD':<6} | {'NOMI':<46} | {'YILI':<6} | {'QISMLAR':<12} | {'STATUS':<12}\n")
    f.write("-" * 80 + "\n")
    for r in new_rows:
        code_val, title_val, year_val, total_ep, status_val = r
        qism_str = f"{total_ep}/{total_ep}"
        f.write(f"{code_val:<6} | {title_val[:46]:<46} | {year_val:<6} | {qism_str:<12} | {status_val:<12}\n")

print(f"Updated {yangi_file}")

# 12. Regenerate DRAMALAR_ROYXATI.txt
c.execute("""
    SELECT d.code, d.title, d.year, COUNT(e.id) as real_eps, d.total_episodes, d.status
    FROM doramas d
    LEFT JOIN episodes e ON d.id = e.dorama_id
    GROUP BY d.id
    ORDER BY d.code ASC
""")
all_rows = c.fetchall()

master_file = os.path.join(BASE_DIR, "DRAMALAR_ROYXATI.txt")
with open(master_file, "w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write(f"UZKDRAMA BOT — BARCHA DRAMALAR RO'YXATI (JAMI: {len(all_rows)} TA)\n")
    f.write("=" * 80 + "\n")
    f.write(f"{'KOD':<6} | {'NOMI':<46} | {'YILI':<6} | {'QISMLAR':<12} | {'STATUS':<12}\n")
    f.write("-" * 80 + "\n")
    for r in all_rows:
        code_val, title_val, year_val, real_eps, total_ep, status_val = r
        ep_count = real_eps if real_eps > 0 else (total_ep if total_ep else 1)
        qism_str = f"{ep_count}/{total_ep if total_ep else ep_count}"
        f.write(f"{code_val:<6} | {title_val[:46]:<46} | {year_val:<6} | {qism_str:<12} | {status_val:<12}\n")

print(f"Updated {master_file}")
conn.close()
print("\n=== MASTER FIX COMPLETED SUCCESSFULLY ===")
