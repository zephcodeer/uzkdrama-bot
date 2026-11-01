import sqlite3
import os
import sys
import io
import urllib.request
import ssl
from PIL import Image, ImageOps, ImageStat

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r'E:\Agent\Drama Bot'
POSTERS_DIR = os.path.join(BASE_DIR, 'posters')
THUMBS_DIR = os.path.join(BASE_DIR, 'channel_thumbs')

conn = sqlite3.connect(os.path.join(BASE_DIR, 'doramas.db'))
c = conn.cursor()

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': 'https://asianwiki.com/'
}

def download_and_fit(url, target_rel_path):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
        data = resp.read()
    im = Image.open(io.BytesIO(data)).convert("RGB")
    fitted = ImageOps.fit(im, (500, 750), method=Image.Resampling.LANCZOS)
    out_path = os.path.join(BASE_DIR, target_rel_path)
    fitted.save(out_path, "JPEG", quality=92, optimize=True)
    print(f"   [OK] Downloaded & fitted {target_rel_path} ({os.path.getsize(out_path):,} bytes)")

def fit_local_thumb(thumb_filename, target_rel_path):
    tpath = os.path.join(THUMBS_DIR, thumb_filename)
    if not os.path.exists(tpath):
        raise FileNotFoundError(f"Thumb not found: {tpath}")
    im = Image.open(tpath).convert("RGB")
    fitted = ImageOps.fit(im, (500, 750), method=Image.Resampling.LANCZOS)
    out_path = os.path.join(BASE_DIR, target_rel_path)
    fitted.save(out_path, "JPEG", quality=92, optimize=True)
    print(f"   [OK] Fitted local thumb {thumb_filename} -> {target_rel_path} ({os.path.getsize(out_path):,} bytes)")

print("=== STARTING COMPREHENSIVE POSTER & METADATA FIX ===")

# 1. FIX CODE 295 (Kumixo: 1938) - Replace black screen with official HD poster
print("\n[1] Fixing Code 295: Kumixo: 1938...")
download_and_fit('https://asianwiki.com/images/f/f7/Tale_of_the_Nine_Tailed_1938-p2.jpg', 'posters/kumixo-1938.jpg')
c.execute("""
    UPDATE doramas
    SET title = ?,
        year = ?,
        genre = ?,
        actors = ?,
        description = ?,
        aliases = ?,
        poster_url = ?
    WHERE code = ?
""", (
    "Kumixo: 1938 (Tale of the Nine Tailed 1938)",
    2023,
    "Fantastika, Tarixiy, Jangari, Romantika",
    "Lee Dong-wook, Kim So-yeon, Kim Bum, Ryu Kyung-soo",
    "Kutilmagan hodisa sababli 1938-yilgi notinch mustamlakachilik davriga qaytib qolgan to'qqiz dumli tulki Li Yon zamonaviy dunyoga va sevgilisi yoniga qaytish uchun qadimgi dushmanlari va sirli kuchlarga qarshi kurashadi.",
    "Tale of the Nine Tailed 1938, Kumixo 1938, Gumiho 1938, Lee Dong-wook, Kim So-yeon, Kim Bum",
    "posters/kumixo-1938.jpg",
    295
))

# 2. FIX CODE 332 (Mukammal toj / Perfect Crown) - Replace blurry low-res crop with official HD poster
print("\n[2] Fixing Code 332: Mukammal toj (Perfect Crown)...")
download_and_fit('https://asianwiki.com/images/a/a5/Perfect_Crown-p1.jpg', 'posters/mukammal-toj-perfect-crown.jpg')
c.execute("""
    UPDATE doramas
    SET title = ?,
        year = ?,
        genre = ?,
        actors = ?,
        description = ?,
        aliases = ?,
        poster_url = ?
    WHERE code = ?
""", (
    "Mukammal toj / 21-asr qirollik oilasi (Perfect Crown)",
    2026,
    "Romantika, Komediya, Drama",
    "IU, Byeon Woo-seok",
    "Zamonaviy konstitutsiyaviy monarxiya Koreyasida boylik va qudratga ega chaebol merosxo'ri va obro'li ammo siyosiy erki cheklangan shahzoda o'rtasidagi shartnomaviy nikoh va kutilmagan haqiqiy muhabbat qissasi.",
    "Perfect Crown, 21-Asr Qirollik Oilasi, 21st Century Grand Prince Wife, IU, Byeon Woo-seok, Mukammal toj",
    "posters/mukammal-toj-perfect-crown.jpg",
    332
))

# 3. FIX CODE 246 (Haqiqiy ta'lim / Study Group) - Replace blurry low-res crop with official HD poster
print("\n[3] Fixing Code 246: Haqiqiy ta'lim (Study Group)...")
download_and_fit('https://m.media-amazon.com/images/M/MV5BYzQ0MmE0ZTUtNTlkNS00NDU2LThiYTEtNjJjYTdmZDNiOWUyXkEyXkFqcGc@._V1_QL75_UY562_CR1,0,380,562_.jpg', 'posters/haqiqiy-talim-study-group.jpg')
c.execute("""
    UPDATE doramas
    SET title = ?,
        year = ?,
        genre = ?,
        actors = ?,
        description = ?,
        aliases = ?,
        poster_url = ?
    WHERE code = ?
""", (
    "Haqiqiy taʼlim / O'quv guruhi (Study Group)",
    2025,
    "Jangari, Komediya, Maktab, Yoshlar",
    "Hwang Min-hyun, Han Ji-eun, Cha Woo-min",
    "Faqatgina o'qishga kirishni orzu qilgan, ammo darsdan ko'ra mushtlashuvda tengsiz iqtidorga ega bo'lgan Yun Ga-min Koreyaning eng xavfli bezori maktabida do'stlari bilan o'quv guruhi tashkil qiladi.",
    "Study Group, Haqiqiy talim, Oquv guruhi, Hwang Min-hyun, Han Ji-eun",
    "posters/haqiqiy-talim-study-group.jpg",
    246
))

# 4. FIX CODE 359 & 333 (Taxi Driver Season 1) - Replace S2 poster with official Season 1 poster
print("\n[4] Fixing Code 359 & 333: Taxi Driver Season 1...")
s1_taxi_url = 'https://m.media-amazon.com/images/M/MV5BMGM1NmE1OTktZjQ1Ny00N2I0LWI1NTktYTFmMjJkODVmNWM4XkEyXkFqcGc@._V1_SX300.jpg'
download_and_fit(s1_taxi_url, 'posters/code_359.jpg')
download_and_fit(s1_taxi_url, 'posters/taxi-delux-taxi-driver-model-taxi.jpg')
c.execute("""
    UPDATE doramas
    SET poster_url = 'posters/code_359.jpg',
        year = 2021
    WHERE code = 359
""")
c.execute("""
    UPDATE doramas
    SET poster_url = 'posters/taxi-delux-taxi-driver-model-taxi.jpg',
        year = 2021
    WHERE code = 333
""")

# 5. FIX CODE 445 (Shavqat Qilinmaydi) - Replace wrong 'A Shop for Killers' with 'Mercy for None' (So Ji-sub)
print("\n[5] Fixing Code 445: Shavqat Qilinmaydi (Mercy for None)...")
download_and_fit('https://m.media-amazon.com/images/M/MV5BMmY5MzdmYjEtY2RhMS00ZGNkLTliOGEtY2M4NTBmZmU5NDc1XkEyXkFqcGc@._V1_QL75_UY562_CR35,0,380,562_.jpg', 'posters/code_445.jpg')
c.execute("""
    UPDATE doramas
    SET title = ?,
        year = ?,
        genre = ?,
        actors = ?,
        description = ?,
        aliases = ?,
        poster_url = ?
    WHERE code = ?
""", (
    "Shavqat qilinmaydi (Mercy for None)",
    2025,
    "Jangari, Kriminal, Triller, Drama",
    "So Ji-sub, Huh Joon-ho, Ahn Kil-kang, Gong Myung, Choo Young-woo",
    "O'z ukasining fojiali o'limidan so'ng adolat izlab, Seulning shafqatsiz jinoiy olamiga qarshi otlangan sobiq afsonaviy jangchi Nam Ki-junning murosasiz qasos yo'li.",
    "Mercy for None, Shavqat qilinmaydi, Gwangjang, So Ji-sub, Hech kimga shafqat yoq, Plaza",
    "posters/code_445.jpg",
    445
))

# 6. FIX CODE 428 (Mabudlar va ikki dunyo) - Replace wrong 'Creation of the Gods' with 'Along with the Gods: The Two Worlds'
print("\n[6] Fixing Code 428: Mabudlar va ikki dunyo (Along with the Gods)...")
download_and_fit('https://m.media-amazon.com/images/M/MV5BOTM0NWVlNzctNjdjMC00OTZmLTlkMjMtYWI2MGM5N2RkZjk1XkEyXkFqcGc@._V1_QL75_UY562_CR7,0,380,562_.jpg', 'posters/code_428.jpg')
c.execute("""
    UPDATE doramas
    SET title = ?,
        year = ?,
        genre = ?,
        actors = ?,
        description = ?,
        aliases = ?,
        poster_url = ?
    WHERE code = ?
""", (
    "Mabudlar va ikki dunyo (Along with the Gods: The Two Worlds)",
    2017,
    "Fantastika, Drama, Jangari, Sarguzasht",
    "Ha Jung-woo, Cha Tae-hyun, Ju Ji-hoon, Kim Hyang-gi, Lee Jung-jae",
    "Xizmat burchini bajarish paytida halok bo'lgan o't o'chiruvchi Kim Ja-hong narigi dunyoda 49 kun ichida 7 ta ilohiy sud oldida o'z begunohligini isbotlash uchun 3 nafar posbon farishta hamrohligida xatarli sinovlardan o'tadi.",
    "Along with the Gods: The Two Worlds, Mabudlar va ikki dunyo, Along with the Gods, Singwa Hamkke, Ha Jung-woo, Cha Tae-hyun",
    "posters/code_428.jpg",
    428
))

# 7. FIX CODE 424 (Oshxona jangchilari afsonasi) - Replace wrong 'Culinary Class Wars' with 'The Legend of Kitchen Soldier'
print("\n[7] Fixing Code 424: Oshxona jangchilari afsonasi (The Legend of Kitchen Soldier)...")
fit_local_thumb('thumb_code_424.jpg', 'posters/code_424.jpg')
c.execute("""
    UPDATE doramas
    SET title = ?,
        year = ?,
        genre = ?,
        actors = ?,
        description = ?,
        aliases = ?,
        poster_url = ?
    WHERE code = ?
""", (
    "Oshxona jangchilari afsonasi (The Legend of Kitchen Soldier)",
    2024,
    "Komediya, Harbiy, Drama, Fantastika",
    "Park Ji-hoon",
    "Harbiy xizmatga chaqirilgan va polk oshxonasiga oshpaz etib tayinlangan yosh askar Kang Song-je sirli gologramma tizim yordamida harbiy oshxona afsonasiga aylanadi.",
    "The Legend of Kitchen Soldier, Oshxona jangchilari afsonasi, Becoming a Cooking Soldier Legend, Park Ji-hoon, Chwisabyeong",
    "posters/code_424.jpg",
    424
))

# 8. FIX CODE 379 (Qo’g’irchoq joylashgan uy) - Replace wrong Korean daily drama with authentic Japanese horror film
print("\n[8] Fixing Code 379: Qo’g’irchoq joylashgan uy...")
fit_local_thumb('thumb_code_379.jpg', 'posters/code_379.jpg')
c.execute("""
    UPDATE doramas
    SET title = ?,
        year = ?,
        genre = ?,
        country = ?,
        description = ?,
        aliases = ?,
        poster_url = ?
    WHERE code = ?
""", (
    "Qo’g’irchoq joylashgan uy (Doll House)",
    2024,
    "Dahshat, Mistika, Triller",
    "Yaponiya",
    "5 yoshli qizining fojiali vafotidan so'ng qayg'uga botgan ona bozordan qiziga o'xshash sirli qo'g'irchoqni sotib oladi. Ammo oilada yangi farzand tug'ilgach, tashlab qo'yilgan qo'g'irchoq xonadonda dahshatli va qonli voqealarni boshlaydi.",
    "Qo'g'irchoq joylashgan uy, Doll House Japan, Qogirchoq joylashgan uy",
    "posters/code_379.jpg",
    379
))

# 9. FIX CODE 311 & 312 (Squid Game Seasons 1 & 2) - Unswap posters, metadata, and episode IDs
print("\n[9] Fixing Code 311 & 312: Squid Game 1 & 2 unswapping...")
p1_path = os.path.join(POSTERS_DIR, 'kalmar-oyini-1-fasl-squid-game-1.jpg')
p2_path = os.path.join(POSTERS_DIR, 'kalmar-oyini-2-fasl-squid-game-2.jpg')

with open(p1_path, 'rb') as f:
    s2_bytes = f.read()
with open(p2_path, 'rb') as f:
    s1_bytes = f.read()

# Write correctly:
with open(p1_path, 'wb') as f:
    f.write(s1_bytes)
with open(p2_path, 'wb') as f:
    f.write(s2_bytes)
print("   [OK] Swapped poster file contents: kalmar-oyini-1 is now S1 key art, kalmar-oyini-2 is now S2 key art.")

# Update DB doramas:
# Code 311 = Season 1
c.execute("""
    UPDATE doramas
    SET title = ?,
        year = ?,
        total_episodes = ?,
        genre = ?,
        actors = ?,
        description = ?,
        aliases = ?,
        poster_url = ?
    WHERE code = ?
""", (
    "Kalmar o'yini 1-fasl (Squid Game Season 1)",
    2021,
    9,
    "Triller, Omon qolish, Drama, Kriminal",
    "Lee Jung-jae, Park Hae-soo, Wi Ha-joon, Jung Ho-yeon",
    "Katta qarzlarga botgan 456 nafar ishtirokchi 45.6 milliard vonlik mukofot jamg'armasi uchun an'anaviy bolalar o'yinlarida qatnashishga taklif qilinadi. Ammo yutqazganlar joyida halok bo'ladigan o'lim o'yini boshlanadi.",
    "Squid Game, Kalmar oyini, Kalmar o'yini 1, Squid Game Season 1, Lee Jung-jae, Park Hae-soo",
    "posters/kalmar-oyini-1-fasl-squid-game-1.jpg",
    311
))

# Code 312 = Season 2
c.execute("""
    UPDATE doramas
    SET title = ?,
        year = ?,
        total_episodes = ?,
        genre = ?,
        actors = ?,
        description = ?,
        aliases = ?,
        poster_url = ?
    WHERE code = ?
""", (
    "Kalmar o'yini 2-fasl (Squid Game Season 2)",
    2024,
    7,
    "Triller, Omon qolish, Drama, Jangari",
    "Lee Jung-jae, Lee Byung-hun, Wi Ha-joon, Im Si-wan, Kang Ha-neul",
    "Birinchi o'yinda g'olib bo'lgan Son Gi-xun AQSHga ketishdan voz kechib, dahshatli o'yin ortida turgan tashkilotchilarni fosh qilish va ularni ichkaridan yakson qilish uchun yana qonli maydonga qaytadi.",
    "Squid Game 2, Kalmar oyini 2, Kalmar o'yini 2, Squid Game Season 2, Lee Jung-jae, Wi Ha-joon, Im Si-wan",
    "posters/kalmar-oyini-2-fasl-squid-game-2.jpg",
    312
))

# Swap episodes table associations so dorama 311 (id 211) has the 9 S1 episodes (msgs 2740..2748)
# and dorama 312 (id 212) has the 7 S2 episodes (msgs 2733..2739)
c.execute("UPDATE episodes SET dorama_id = -999 WHERE dorama_id = 211")
c.execute("UPDATE episodes SET dorama_id = 211 WHERE dorama_id = 212")
c.execute("UPDATE episodes SET dorama_id = 212 WHERE dorama_id = -999")
print("   [OK] Swapped episodes associations: Code 311 now has 9 episodes, Code 312 now has 7 episodes.")

conn.commit()
print("\nAll database updates committed successfully!")

# 10. Regenerate YANGI_DRAMALAR_ROYXATI.txt
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

# 11. Regenerate DRAMALAR_ROYXATI.txt
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
print("\n=== COMPREHENSIVE FIX COMPLETED SUCCESSFULLY ===")
