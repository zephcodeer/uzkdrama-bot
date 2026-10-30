import sqlite3
import os
import sys
import urllib.request
import ssl
from PIL import Image
import io

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = r"E:\Agent\Drama Bot"
DB_PATH = os.path.join(BASE_DIR, "doramas.db")
POSTERS_DIR = os.path.join(BASE_DIR, "posters")

def download_poster():
    poster_file = "vision-quest.jpg"
    poster_path = os.path.join(POSTERS_DIR, poster_file)
    if os.path.exists(poster_path) and os.path.getsize(poster_path) > 10000:
        print(f"Poster allaqachon mavjud: {poster_path}")
        return f"posters/{poster_file}"
        
    url = "https://static.tvmaze.com/uploads/images/original_untouched/636/1592334.jpg"
    print(f"Poster yuklanmoqda: {url} -> {poster_path}")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx) as resp:
        img_bytes = resp.read()
        
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img.save(poster_path, "JPEG", quality=90, optimize=True)
    print(f"Poster saqlandi: {img.size}, hajm={os.path.getsize(poster_path)} bytes")
    return f"posters/{poster_file}"

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Poster yuklash
    rel_poster_path = download_poster()
    
    # 2. Mavjudligini tekshirish
    c.execute("SELECT id, code FROM doramas WHERE slug = 'vijnning-izlanishi-vision-quest' OR code = 342")
    row = c.fetchone()
    if row:
        dorama_id = row[0]
        code = row[1]
        print(f"Dorama bazada bor: id={dorama_id}, code={code}")
    else:
        c.execute("SELECT MAX(code) FROM doramas")
        max_code = c.fetchone()[0] or 341
        code = max_code + 1
        
        title = "Vijnning izlanishi / Vijinning jumbog'i (Vision Quest)"
        slug = "vijnning-izlanishi-vision-quest"
        genre = "Fantastika, Jangari, Sarguzasht, Marvel"
        year = 2026
        total_episodes = 8
        status = "Ongoing"
        country = "AQSH"
        category = "marvel"
        actors = "Paul Bettany, James Spader, Todd Stashwick"
        description = "WandaVision voqealaridan so'ng o'z shaxsiyati va insoniy tuyg'ularini anglashga intilayotgan 'Oq Vision' (White Vision) yangi xavf-xatarlar va kutilmagan sirlar girdobiga duch keladi."
        aliases = "Vision Quest, Vijinning jumbog'i, Vijinning jumbogi, Vijnning izlanishi, Oq Vision, White Vision, Vision 2026, Vanda va Vijn 2"
        views = 10
        
        c.execute("""
            INSERT INTO doramas (
                code, title, slug, genre, year, description,
                poster_url, total_episodes, views, status, country,
                actors, category, aliases
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            code, title, slug, genre, year, description,
            rel_poster_path, total_episodes, views, status, country,
            actors, category, aliases
        ))
        dorama_id = c.lastrowid
        print(f"Yangi dorama qo'shildi: id={dorama_id}, code={code}, title='{title}'")

    # 3. Ongoing qismlar
    episodes_map = [
        (1, 3340),
        (2, 3341)
    ]

    c.execute("DELETE FROM episodes WHERE dorama_id = ?", (dorama_id,))
    
    for ep_num, msg_id in episodes_map:
        c.execute("""
            INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality, file_id)
            VALUES (?, ?, ?, ?, ?)
        """, (dorama_id, ep_num, msg_id, "1080p", None))
        
    conn.commit()
    
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
