import sqlite3, sys, os, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\Agent\Drama Bot')

from database import slugify, normalize_search_text
from scripts.parse_new_dramas import parsed_dramas
from scripts.precurated_meta import KNOWN_DRAMA_META
from scripts.ingest_helper import create_cinematic_poster, clean_raw_title, guess_genre, guess_year, POSTERS_DIR

EXCLUDED_MSGS = {4049, 4590, 4591, 4592, 4593, 4594, 4595, 4596, 4597, 4598, 4599, 4600}

# 1. Filter out the 4 already ingested dramas
new_dramas = []
for d in parsed_dramas:
    if all(m[1] in EXCLUDED_MSGS for m in d['episodes']):
        continue
    new_dramas.append(d)

print(f"Total new drama blocks to ingest: {len(new_dramas)}")

# 2. Check current max code in doramas.db
conn = sqlite3.connect(r'E:\Agent\Drama Bot\doramas.db')
c = conn.cursor()
c.execute("SELECT MAX(code) FROM doramas")
current_max_code = c.fetchone()[0] or 350
print(f"Current MAX code in database: {current_max_code}")

next_code = current_max_code + 1

# Track titles to handle the 3 repeated blocks cleanly
seen_clean_titles = set()
ingested_records = []

for d in new_dramas:
    raw_title = d['raw_title']
    cleaned_t, auto_status = clean_raw_title(raw_title)

    # Check known pre-curated metadata
    norm_key = normalize_search_text(cleaned_t)
    meta = KNOWN_DRAMA_META.get(norm_key)

    if meta:
        title = meta['title']
        genre = meta['genre']
        year = meta['year']
        country = meta['country']
        aliases = meta['aliases']
        desc = meta['desc']
        status = auto_status if auto_status == "Ongoing" else "Tugallangan"
    else:
        title = cleaned_t
        genre = guess_genre(cleaned_t)
        year = guess_year(cleaned_t)
        country = "Janubiy Koreya"
        aliases = f"{cleaned_t}, {raw_title}"
        desc = f"{cleaned_t} — qiziqarli syujet, kuchli aktyorlar mahorati va kutilmagan voqealarga boy bo'lgan ommabop dorama. Barcha qismlari o'zbek tilida sifatli taqdim etiladi."
        status = auto_status

    # Agar nom takrorlangan bo'lsa (fayldagi 3 ta dorama uchun), uni 2-variant deb ajratamiz
    if title in seen_clean_titles:
        title = f"{title} (2-variant)"
        aliases = f"{aliases}, 2-variant"
    seen_clean_titles.add(title)

    code = next_code
    next_code += 1

    slug = f"{slugify(title)}-{code}"
    poster_filename = f"code_{code}.jpg"
    poster_rel_path = f"posters/{poster_filename}"
    poster_abs_path = os.path.join(POSTERS_DIR, poster_filename)

    # Poster yaratish
    if not os.path.exists(poster_abs_path):
        create_cinematic_poster(poster_abs_path, title, year, genre, code)

    total_episodes = len(d['episodes'])

    # Doramani bazaga kiritish
    c.execute("""
        INSERT INTO doramas (
            code, title, slug, genre, year, description, poster_url,
            total_episodes, views, category, status, country, actors, aliases, series_group
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        code, title, slug, genre, year, desc, poster_rel_path,
        total_episodes, 0, 'korea', status, country, '', aliases, ''
    ))
    dorama_id = c.lastrowid

    # Qismlarni bazaga kiritish
    for ep_num, msg_id, link in d['episodes']:
        c.execute("""
            INSERT INTO episodes (
                dorama_id, episode_number, channel_message_id, file_id, file_size, quality
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            dorama_id, ep_num, msg_id, '', 0, '1080p'
        ))

    ingested_records.append({
        "code": code,
        "title": title,
        "year": year,
        "episodes": total_episodes,
        "status": status,
        "first_msg": d['episodes'][0][1],
        "last_msg": d['episodes'][-1][1]
    })

conn.commit()
print(f"Successfully ingested {len(ingested_records)} doramas into doramas.db!")

# 3. Yangi dramalar ro'yxatini alohida faylga yozish (YANGI_DRAMALAR_ROYXATI.txt)
yangi_file = r"E:\Agent\Drama Bot\YANGI_DRAMALAR_ROYXATI.txt"
with open(yangi_file, "w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write(f"UZKDRAMA BOT — YANGI QO'SHILGAN DRAMALAR (JAMI: {len(ingested_records)} TA | KODLAR: {ingested_records[0]['code']}-{ingested_records[-1]['code']})\n")
    f.write("=" * 80 + "\n")
    f.write(f"{'KOD':<6} | {'NOMI':<46} | {'YILI':<6} | {'QISMLAR':<12} | {'STATUS':<12}\n")
    f.write("-" * 80 + "\n")
    for r in ingested_records:
        qism_str = f"{r['episodes']}/{r['episodes']}"
        f.write(f"{r['code']:<6} | {r['title'][:46]:<46} | {r['year']:<6} | {qism_str:<12} | {r['status']:<12}\n")

print(f"Written: {yangi_file}")

# 4. To'liq master ro'yxatni yangilash (DRAMALAR_ROYXATI.txt)
c.execute("""
    SELECT d.code, d.title, d.year, COUNT(e.id) as real_eps, d.total_episodes, d.status
    FROM doramas d
    LEFT JOIN episodes e ON d.id = e.dorama_id
    GROUP BY d.id
    ORDER BY d.code ASC
""")
all_doramas = c.fetchall()

master_file = r"E:\Agent\Drama Bot\DRAMALAR_ROYXATI.txt"
with open(master_file, "w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write(f"UZKDRAMA BOT — BARCHA DRAMALAR RO'YXATI (JAMI: {len(all_doramas)} TA)\n")
    f.write("=" * 80 + "\n")
    f.write(f"{'KOD':<6} | {'NOMI':<46} | {'YILI':<6} | {'QISMLAR':<12} | {'STATUS':<12}\n")
    f.write("-" * 80 + "\n")
    for row in all_doramas:
        code_val, title_val, year_val, real_cnt, total_ep, status_val = row
        ep_display = f"{real_cnt}/{total_ep}"
        f.write(f"{code_val:<6} | {title_val[:46]:<46} | {year_val:<6} | {ep_display:<12} | {status_val:<12}\n")

print(f"Updated: {master_file} (Total: {len(all_doramas)} doramas)")

conn.close()
