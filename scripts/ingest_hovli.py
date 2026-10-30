import sqlite3
import os
import sys
import re
import urllib.request
import ssl
from PIL import Image
import io

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = r"E:\Agent\Drama Bot"
DB_PATH = os.path.join(BASE_DIR, "doramas.db")
POSTERS_DIR = os.path.join(BASE_DIR, "posters")

def download_poster():
    poster_file = "hovli-avlu.jpg"
    poster_path = os.path.join(POSTERS_DIR, poster_file)
    if os.path.exists(poster_path) and os.path.getsize(poster_path) > 10000:
        print(f"Poster allaqachon mavjud: {poster_path}")
        return f"posters/{poster_file}"
        
    url = "https://static.tvmaze.com/uploads/images/original_untouched/550/1375252.jpg"
    print(f"Poster yuklab olinmoqda: {url} -> {poster_path}")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx) as resp:
        img_bytes = resp.read()
        
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img.save(poster_path, "JPEG", quality=92, optimize=True)
    print(f"Poster saqlandi: {img.size}, hajm={os.path.getsize(poster_path)} bytes")
    return f"posters/{poster_file}"

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Poster yuklash
    rel_poster_path = download_poster()
    
    # 2. Mavjudligini tekshirish
    c.execute("SELECT id, code FROM doramas WHERE title LIKE '%Hovli%' OR slug = 'hovli-avlu-1-2-fasl'")
    row = c.fetchone()
    if row:
        dorama_id = row[0]
        code = row[1]
        print(f"Dorama bazada bor ekan: id={dorama_id}, code={code}")
    else:
        c.execute("SELECT MAX(code) FROM doramas")
        max_code = c.fetchone()[0] or 339
        code = max_code + 1
        
        title = "Hovli (Avlu) 1-2 fasl"
        slug = "hovli-avlu-1-2-fasl"
        genre = "Kriminal, Drama, Triller, Qamoqxona"
        year = 2018
        total_episodes = 123
        status = "Tugallangan"
        country = "Turkiya"
        category = "turk"
        actors = "Demet Evgar, Ceren Moray, Nursel Köse, Kenan Ece, Teoman Kumbaracıbaşı"
        description = "O'zini va qizini zo'ravon eridan himoya qilish asnosida qamoqqa tushgan Deniz ismli ayolning qattiqqo'l ayollar qamoqxonasidagi ayovsiz kurashi va omon qolish uchun olib borgan jasoratli qissasi."
        views = 10
        
        c.execute("""
            INSERT INTO doramas (
                code, title, slug, genre, year, description,
                poster_url, total_episodes, views, status, country,
                actors, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            code, title, slug, genre, year, description,
            rel_poster_path, total_episodes, views, status, country,
            actors, category
        ))
        dorama_id = c.lastrowid
        print(f"Yangi dorama qo'shildi: id={dorama_id}, code={code}, title='{title}'")

    # 3. Qismlar ro'yxatini shakllantirish
    raw_list = [
        (1, 3208), (2, 3209), (3, 3210), (4, 3211), (5, 3212),
        (6, 3213), (7, 3214), (8, 3215), (9, 3216),
        # 10-11 birlashtirilgan
        (10, 3217), (11, 3217)
    ]
    # 12 dan 123 gacha
    # 12 -> 3218, 123 -> 3329
    for ep in range(12, 124):
        msg_id = 3218 + (ep - 12)
        raw_list.append((ep, msg_id))

    print(f"Jami qismlar: {len(raw_list)} ta (1-qismdan 123-qismgacha)")
    
    # Eski qismlarni tozalab qaytadan kiritish
    c.execute("DELETE FROM episodes WHERE dorama_id = ?", (dorama_id,))
    
    for ep_num, msg_id in raw_list:
        c.execute("""
            INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality, file_id)
            VALUES (?, ?, ?, ?, ?)
        """, (dorama_id, ep_num, msg_id, "1080p", None))
        
    conn.commit()
    
    # Tekshiruv
    c.execute("SELECT COUNT(*) FROM episodes WHERE dorama_id = ?", (dorama_id,))
    cnt = c.fetchone()[0]
    print(f"Muvaffaqiyatli saqlandi! Dorama id={dorama_id}, qismlar soni={cnt}")
    
    c.execute("SELECT COUNT(*) FROM doramas")
    tot_d = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM episodes")
    tot_e = c.fetchone()[0]
    print(f"Bazada jami: {tot_d} ta dorama, {tot_e} ta qism mavjud.")
    conn.close()

if __name__ == "__main__":
    main()
