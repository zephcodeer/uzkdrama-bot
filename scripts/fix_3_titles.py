import sqlite3, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\Agent\Drama Bot')

from scripts.ingest_helper import create_cinematic_poster, POSTERS_DIR

conn = sqlite3.connect(r'E:\Agent\Drama Bot\doramas.db')
c = conn.cursor()

UPDATES = [
    {
        "code": 355,
        "title": "Choson nikoh agentligi (Flower Crew: Joseon Marriage Agency)",
        "slug": "choson-nikoh-agentligi-355",
        "genre": "Tarixiy, Romantika, Komediya",
        "year": 2019,
        "aliases": "Choson nikoh agentligi, Flower Crew Joseon Marriage Agency, Kim Min-jae, Gong Seung-yeon",
        "desc": "Choson davlatining eng ko'rkam uch nafar sovchisi yosh podshohning iltimosiga binoan oddiy qashshoq qizni zodagon xonimga aylantirish bo'yicha imkonsiz topshiriqni bajarishga kirishadi.",
        "status": "Ongoing"
    },
    {
        "code": 362,
        "title": "Mening sevimli yolg'onchim (My Lovely Liar)",
        "slug": "mening-sevimli-yolgonchim-362",
        "genre": "Romantika, Fantastika, Komediya, Detektiv",
        "year": 2023,
        "aliases": "Mening sevimli yolgonchim, My Lovely Liar, Kim So-hyun, Hwang Min-hyun",
        "desc": "Insonlarning yolg'on gapirayotganini eshita oladigan 'yolg'on ovchisi' Mok Sol-xi va qotillikda nohaq gumon qilinib o'z shaxsini yashirib yurgan daho bastakor Kim Do-xaning taqdiri kesishadi.",
        "status": "Tugallangan"
    },
    {
        "code": 367,
        "title": "Ruyi pavilonidagi gullar (The Blooms at Ruyi Pavilion)",
        "slug": "ruyi-pavilonidagi-gullar-367",
        "genre": "Tarixiy, Romantika, Fantastika, Sirli",
        "year": 2020,
        "aliases": "Ruyi Pavillionidagi Gullar, The Blooms at Ruyi Pavilion, Ju Jingyi, Zhang Zhehan",
        "desc": "Tushlarida kelajakdagi o'z fojiasini ko'rib, taqdirini o'zgartirishga ahd qilgan jasur zodagon qiz va saroy shahzodasining sirli tergovlar va muhabbatga to'la hayoti.",
        "status": "Tugallangan"
    }
]

for u in UPDATES:
    c.execute("""
        UPDATE doramas
        SET title = ?, slug = ?, genre = ?, year = ?, aliases = ?, description = ?, status = ?
        WHERE code = ?
    """, (u['title'], u['slug'], u['genre'], u['year'], u['aliases'], u['desc'], u['status'], u['code']))
    
    # Poster qayta yaratish
    poster_path = os.path.join(POSTERS_DIR, f"code_{u['code']}.jpg")
    create_cinematic_poster(poster_path, u['title'], u['year'], u['genre'], u['code'])
    print(f"Updated code {u['code']} -> {u['title']}")

conn.commit()

# Re-write YANGI_DRAMALAR_ROYXATI.txt
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

# Re-write master DRAMALAR_ROYXATI.txt
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
