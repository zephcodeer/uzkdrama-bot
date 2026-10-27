import os
import re
import sys
import json
import urllib.request
import urllib.parse

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

POSTERS_DIR = r"E:\Agent\Drama Bot\posters"
os.makedirs(POSTERS_DIR, exist_ok=True)

OMDB_API_KEY = "bd182e04"

# Mapping: (slug, search_title, year, type_param, fallback_url)
DORAMA_POSTERS = [
    ("yovuzlarning_yovuzi", "The Worst of Evil", "2023", "series", None),
    ("pinokkio", "Pinocchio", "2014", "series", None),
    ("dozaxdagi_notanishlar", "Hell Is Other People", "2019", "series", "https://upload.wikimedia.org/wikipedia/en/2/29/Hell_Is_Other_People.jpg"),
    ("aqldan_ozgan_ammo_hammasi_joyda", "It's Okay to Not Be Okay", "2020", "series", None),
    ("doona", "Doona!", "2023", "series", None),
    ("oltin_qoshiq", "The Golden Spoon", "2022", "series", None),
    ("alvon_yuraklar_koryo", "Moon Lovers: Scarlet Heart Ryeo", "2016", "series", None),
    ("orol_s2", "Island", "2023", "series", "https://upload.wikimedia.org/wikipedia/en/9/91/Island_TVING.jpg"),
    ("orol_s1", "Island", "2022", "series", "https://upload.wikimedia.org/wikipedia/en/9/91/Island_TVING.jpg"),
    ("qish_sonatasi", "Winter Sonata", "2002", "series", None),
    ("vorislar", "Heirs", "2013", "series", None),
    ("notanish_doktor", "Doctor Stranger", "2014", "series", None),
    ("darbadar_ruh_s1", "Alchemy of Souls", "2022", "series", None),
    ("darbadar_ruh_s2", "Alchemy of Souls", "2022", "series", "https://upload.wikimedia.org/wikipedia/en/4/41/Alchemy_of_Souls_Part_2.jpg"),
    ("piramida_oyini", "Pyramid Game", "2024", "series", None),
    ("pentxaus_s1", "The Penthouse: War in Life", "2020", "series", None),
    ("pentxaus_s2", "The Penthouse: War in Life", "2021", "series", "https://upload.wikimedia.org/wikipedia/en/a/a2/The_Penthouse_2_War_in_Life.png"),
    ("pentxaus_s3", "The Penthouse: War in Life", "2021", "series", "https://upload.wikimedia.org/wikipedia/en/5/52/The_Penthouse_3_War_in_Life.png"),
    ("zombilar_qirolligi_s1", "Kingdom", "2019", "series", None),
    ("zombilar_qirolligi_s2", "Kingdom", "2020", "series", None),
    ("zombilar_qirolligi_ashin", "Kingdom: Ashin of the North", "2021", "movie", None),
    ("jonajon_uy_s1", "Sweet Home", "2020", "series", None),
    ("jonajon_uy_s2", "Sweet Home", "2023", "series", None),
    ("yovuzlik_guli", "Flower of Evil", "2020", "series", None),
    ("dozax_chaqiruvi", "Hellbound", "2021", "series", None),
    ("maktabdan_keyingi_majburiyatlar", "Duty After School", "2023", "series", None),
    ("maktabga_qaytgan_bezori", "High School Return of a Gangster", "2024", "series", None),
    ("yovuz_va_telba", "Bad and Crazy", "2021", "series", None),
    ("parallel_olamlar_w", "W", "2016", "series", None),
    ("jahldor_rohib", "The Fiery Priest", "2019", "series", None),
    ("badavlat_x_politsiyachi", "Flex X Cop", "2024", "series", None),
    ("quyosh_avlodlari", "Descendants of the Sun", "2016", "series", None),
    ("do_bong_sun", "Strong Girl Bong-soon", "2017", "series", None),
    ("kotiba_kimga_nima_boldi", "What's Wrong with Secretary Kim", "2018", "series", None),
    ("yer_qiroli", "King the Land", "2023", "series", None),
    ("janob_plankton", "Mr. Plankton", "2024", "series", None),
    ("yigirma_besh_yigirma_bir", "Twenty-Five Twenty-One", "2022", "series", None),
    ("zolimning_oshpazi", "Bon Appetit, Your Majesty", "2025", "series", None),
    ("oy_ogushidagi_quyosh", "Moon Embracing the Sun", "2012", "series", None),
    ("ierarxiya", "Hierarchy", "2024", "series", None),
    ("zolushka_va_tort_ritsar", "Cinderella and the Four Knights", "2016", "series", None),
    ("yuz_kunlik_yolgon", "100 Days of Deception", "2026", "series", "https://upload.wikimedia.org/wikipedia/en/thumb/8/89/100_Days_of_Deception.jpg/800px-100_Days_of_Deception.jpg"),
    ("ottiz_lekin_on_yetti", "Still 17", "2018", "series", None),
    ("orzular_qanotida", "Dream High", "2011", "series", None)
]

def make_high_res_amazon(url: str) -> str:
    # Amazon image URLs often contain ._V1_SX300.jpg -> replace with ._V1_FMjpg_UY1200_.jpg
    return re.sub(r"\._V1_.*?\.", "._V1_FMjpg_UY1200_.", url)

def download_image(url: str, dest_path: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        with open(dest_path, "wb") as f:
            f.write(resp.read())

print(f"🎬 Jami {len(DORAMA_POSTERS)} ta dorama uchun posterlar yuklanmoqda...\n")

success = 0
failed = []

for slug, search_title, year, typ, fallback in DORAMA_POSTERS:
    dest_path = os.path.join(POSTERS_DIR, f"{slug}.jpg")
    
    # Check if already exists and > 20KB
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 20000:
        print(f"⏩ [Mavjud] {slug} ({os.path.getsize(dest_path)//1024} KB)")
        success += 1
        continue
    
    poster_url = None
    # 1. Try OMDB
    try:
        omdb_url = f"http://www.omdbapi.com/?t={urllib.parse.quote(search_title)}&y={year}&type={typ}&apikey={OMDB_API_KEY}"
        req = urllib.request.urlopen(omdb_url, timeout=6)
        data = json.loads(req.read().decode())
        if data.get("Response") == "True" and data.get("Poster") and data.get("Poster") != "N/A":
            raw_url = data.get("Poster")
            poster_url = make_high_res_amazon(raw_url)
    except Exception as e:
        print(f"OMDB lookup error for {slug}: {e}")
    
    # 2. If OMDB failed or fallback specified
    if not poster_url and fallback:
        poster_url = fallback
    
    if poster_url:
        try:
            download_image(poster_url, dest_path)
            sz = os.path.getsize(dest_path)
            if sz > 5000:
                print(f"✅ [Yuklandi] {slug} -> {sz//1024} KB")
                success += 1
            else:
                print(f"⚠️ [Kichik fayl] {slug} -> {sz} bytes")
                failed.append((slug, "Fayl juda kichik"))
        except Exception as e:
            print(f"❌ [Yuklash xatosi] {slug}: {e}")
            failed.append((slug, str(e)))
    else:
        print(f"❌ [Topilmadi] {slug}")
        failed.append((slug, "Poster URL topilmadi"))

print(f"\n==========================================")
print(f"NATIJA: {success}/{len(DORAMA_POSTERS)} ta poster muvaffaqiyatli!")
if failed:
    print(f"Xatolar: {failed}")
