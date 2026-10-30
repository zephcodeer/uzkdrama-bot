import sqlite3
import os
import sys
import re
import json
import urllib.request
import urllib.parse
from PIL import Image
import io

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = r"E:\Agent\Drama Bot"
DB_PATH = os.path.join(BASE_DIR, "doramas.db")
POSTERS_DIR = os.path.join(BASE_DIR, "posters")
OMDB_API_KEY = "bd182e04"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_slug(text):
    text = re.sub(r"[ʻʼ'\`’‘]", "", text.lower())
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")

def download_image(url, save_path):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = resp.read()
        if len(data) < 4000:
            return False
        img = Image.open(io.BytesIO(data))
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(save_path, "JPEG", quality=92)
        return True
    except Exception as e:
        return False

def fetch_omdb_poster_url(title, year=None):
    try:
        params = {"apikey": OMDB_API_KEY, "t": title}
        if year:
            y_m = re.search(r"\d{4}", str(year))
            if y_m:
                params["y"] = y_m.group(0)
        url = f"https://www.omdbapi.com/?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("Response") == "True" and data.get("Poster") and data.get("Poster") != "N/A":
            p_url = data["Poster"]
            hd_url = re.sub(r'\._V1_.*\.jpg$', '._V1_.jpg', p_url)
            return hd_url
    except Exception:
        pass
    
    try:
        params_s = {"apikey": OMDB_API_KEY, "s": title}
        url_s = f"https://www.omdbapi.com/?{urllib.parse.urlencode(params_s)}"
        req = urllib.request.Request(url_s, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for item in data.get("Search", []):
            if item.get("Poster") and item.get("Poster") != "N/A":
                p_url = item["Poster"]
                hd_url = re.sub(r'\._V1_.*\.jpg$', '._V1_.jpg', p_url)
                return hd_url
    except Exception:
        pass
        
    return None

def fetch_bing_poster_url(query):
    try:
        url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query + ' poster')}&qft=+filterui:aspect-tall"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        murls = re.findall(r'murl&quot;:&quot;(http[^&]+)&quot;', html)
        for m in murls:
            if m.endswith((".jpg", ".jpeg", ".png")):
                return m
    except Exception:
        pass
    return None

def get_best_poster(search_title, year, save_path, fallback_url=None):
    if os.path.exists(save_path) and os.path.getsize(save_path) > 10000:
        return True
    
    # 1. Try OMDb
    omdb_url = fetch_omdb_poster_url(search_title, year)
    if omdb_url and download_image(omdb_url, save_path):
        print(f"    [OMDb HD] Downloaded for '{search_title}'")
        return True
        
    # 2. Try Fallback direct URL
    if fallback_url and fallback_url.startswith("http") and "google.com" not in fallback_url:
        if download_image(fallback_url, save_path):
            print(f"    [Table URL] Downloaded for '{search_title}'")
            return True
            
    # 3. Try Bing Image Search
    bing_url = fetch_bing_poster_url(search_title)
    if bing_url and download_image(bing_url, save_path):
        print(f"    [Bing HD] Downloaded for '{search_title}'")
        return True
        
    # 4. Fallback Placeholder
    print(f"    [Placeholder] Creating placeholder for '{search_title}'")
    img = Image.new("RGB", (600, 900), color=(26, 32, 44))
    img.save(save_path, "JPEG")
    return True

# --- NEW DORAMAS DATA (31 items) ---
NEW_DORAMAS = [
    {
        "code": 309,
        "title": "Itevon sinfi / Itaewon klass (Itaewon Class)",
        "slug": "itevon-sinfi-itaewon-class",
        "year": "2020",
        "status": "Tugallangan (Completed)",
        "genre": "Drama, Biznes, Qasos, Romantika",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Park Seo-joon, Kim Da-mi, Yoo Jae-myung, Kwon Nara",
        "description": "Adolatsizlik tufayli otasidan ayrilib, qamoqqa tushgan yosh Park Se-roy ozodlikka chiqqach, Seulning gavjum Itevon tumanida o'z bar-restoranini ochadi va qudratli Jangga korporatsiyasiga qarshi 15 yillik qasos va muvaffaqiyat kurashini boshlaydi.",
        "search_title": "Itaewon Class",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/0/09/Itaewon_Class_poster.jpg",
        "episodes": list(range(2701, 2717)) # 16 eps
    },
    {
        "code": 310,
        "title": "Moviy dengiz afsonasi / Moviy ummon afsonasi (The Legend of the Blue Sea)",
        "slug": "moviy-dengiz-afsonasi-legend-blue-sea",
        "year": "2016",
        "status": "Tugallangan (Completed)",
        "genre": "Romantika, Fentezi, Komediya",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Lee Min-ho, Jun Ji-hyun, Lee Hee-joon, Shin Won-ho",
        "description": "Yer yuzidagi oxirgi suv parisi Sim Chon zamonaviy Seulga tushib qoladi va mohir firibgar Xo Jun-je bilan uchrashadi. Ularning taqdiri Choson davridagi o'tmish hayotlari bilan uzviy bog'liq bo'lib chiqadi.",
        "search_title": "The Legend of the Blue Sea",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/9/90/The_Legend_of_the_Blue_Sea_poster.jpg",
        "episodes": list(range(2717, 2733)) + [3061, 3062, 3063, 3064] # 20 eps
    },
    {
        "code": 311,
        "title": "Kalmar oʻyini 2-fasl (Squid Game Season 2)",
        "slug": "kalmar-oyini-2-fasl-squid-game-2",
        "year": "2024",
        "status": "Tugallangan (Completed)",
        "genre": "Triller, Omon qolish, Drama, Sirli",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Lee Jung-jae, Lee Byung-hun, Wi Ha-joon, Yim Si-wan, Kang Ha-neul",
        "description": "Birinchi o'yinda g'olib bo'lgan Son Gi-xun AQSHga ketishdan voz kechib, dahshatli o'yin ortida turgan tashkilotchilarni fosh qilish va ularni ichkaridan yakson qilish uchun yana qonli maydonga qaytadi.",
        "search_title": "Squid Game 2",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/5/52/Squid_Game_season_2_poster.png",
        "episodes": list(range(2733, 2740)) # 7 eps
    },
    {
        "code": 312,
        "title": "Kalmar oʻyini 1-fasl (Squid Game Season 1)",
        "slug": "kalmar-oyini-1-fasl-squid-game-1",
        "year": "2021",
        "status": "Tugallangan (Completed)",
        "genre": "Triller, Omon qolish, Drama, Psixologik",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Lee Jung-jae, Park Hae-soo, Jung Ho-yeon, Wi Ha-joon, O Yeong-su",
        "description": "Katta qarzlarga botgan 456 nafar ishtirokchi 45.6 milliard vonlik mukofot jamg'armasi uchun an'anaviy bolalar o'yinlarida qatnashishga taklif qilinadi. Ammo yutqazganlar joyida halok bo'ladigan o'lim o'yini boshlanadi.",
        "search_title": "Squid Game",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/d/d7/Squid_Game_title_card.jpg",
        "episodes": list(range(2740, 2749)) # 9 eps
    },
    {
        "code": 313,
        "title": "Farishtaning sevgisi / Dan, yagona sevgim (Angel's Last Mission: Love)",
        "slug": "farishtaning-sevgisi-angels-last-mission-love",
        "year": "2019",
        "status": "Tugallangan (Completed)",
        "genre": "Romantika, Fentezi, Drama, Melodrama",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Shin Hye-sun, Kim Myung-soo (L), Lee Dong-gun, Kim Bo-mi",
        "description": "Samoviy qoidalarni buzgan sho'x farishta Danga jannatga qaytish uchun so'nggi imkoniyat beriladi: u baxtsiz hodisada ko'rish qobiliyatidan va sevgiga ishonchidan ayrilgan mag'rur balerina Li Yon-soning haqiqiy muhabbatini topishiga yordam berishi kerak.",
        "search_title": "Angel's Last Mission: Love",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/c/c5/Angel%27s_Last_Mission-_Love.jpg",
        "episodes": list(range(2749, 2765)) # 16 eps
    },
    {
        "code": 314,
        "title": "Kalmar oʻyini 3-fasl (Squid Game Season 3)",
        "slug": "kalmar-oyini-3-fasl-squid-game-3",
        "year": "2025",
        "status": "Tugallangan (Completed)",
        "genre": "Triller, Omon qolish, Drama",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Lee Jung-jae, Lee Byung-hun, Wi Ha-joon",
        "description": "Dunyoni larzaga solgan «Kalmar o'yini»ning yakuniy hal qiluvchi uchinchi fasli. Barcha sirlar ochiladi va Gi-xun hamda Front Men o'rtasidagi so'nggi to'qnashuv o'yin taqdiriga nuqta qo'yadi.",
        "search_title": "Squid Game",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/d/d7/Squid_Game_title_card.jpg",
        "episodes": list(range(2765, 2771)) # 6 eps
    },
    {
        "code": 315,
        "title": "Sevgi hikoyasi / Melo film (Melo Movie)",
        "slug": "sevgi-hikoyasi-melo-movie",
        "year": "2025",
        "status": "Tugallangan (Completed)",
        "genre": "Romantika, Drama, Yoshlik",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Choi Woo-shik, Park Bo-young, Lee Jun-young, Jeon So-nee",
        "description": "Kino sanoatida o'z yo'lini topishga urinayotgan yosh ijodkorlar — film tanqidchisi bo'lib yetishgan kino shinavandasi va rejissyor bo'lishni orzu qilgan qizning samimiy va hissiyotlarga boy sevgisi haqida hikoya.",
        "search_title": "Melo Movie",
        "fallback_url": None,
        "episodes": list(range(2771, 2781)) # 10 eps
    },
    {
        "code": 316,
        "title": "Shahzodaning mahbubasi / 21-asr shahzodasining rafiqasi (The 21st Century Grand Prince's Wife)",
        "slug": "shahzodaning-mahbubasi-21st-century-grand-prince-wife",
        "year": "2026",
        "status": "Tugallangan (Completed)",
        "genre": "Tarixiy-Zamonaviy, Qirollik, Romantika",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Rowoon, Shin Ye-eun, Kim Min-kyu",
        "description": "21-asrda konstitutsiyaviy monarxiya saqlanib qolgan Koreyada qirol oilasining erkin va isyonkor shahzodasi oddiy oiladan chiqqan qat'iyatli qizga oshiq bo'ladi va saroy qonunlariga qarshi kurashadi.",
        "search_title": "The 21st Century Grand Prince's Wife",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/7/76/Perfect_Crown_poster.png",
        "episodes": list(range(2881, 2893)) # 12 eps
    },
    {
        "code": 317,
        "title": "Yulduzlardan soʻra / Yulduzlar gʻiybati (When the Stars Gossip)",
        "slug": "yulduzlardan-sora-when-the-stars-gossip",
        "year": "2025",
        "status": "Tugallangan (Completed)",
        "genre": "Kosmos, Fantastika, Romantika, Komediya",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Lee Min-ho, Gong Hyo-jin, Oh Jung-se, Han Ji-eun",
        "description": "Kosmik stansiyaga sayyoh sifatida tashrif buyurgan ginekolog shifokor Kong Ryon va stansiyaning professional komandiri, qat'iy astronavt Iv Kim o'rtasida fazoda boshlangan kutilmagan kosmik romantika.",
        "search_title": "When the Stars Gossip",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/b/b5/When_the_Stars_Gossip.jpg",
        "episodes": list(range(2905, 2921)) # 16 eps
    },
    {
        "code": 318,
        "title": "F4 Tailand / Gullardan goʻzal yigitlar (F4 Thailand: Boys Over Flowers)",
        "slug": "f4-tailand-boys-over-flowers",
        "year": "2021",
        "status": "Tugallangan (Completed)",
        "genre": "Maktab, Romantika, Drama, Yoshlik",
        "country": "Tailand",
        "category": "foreign",
        "actors": "Bright Vachirawit, Tu Tontawan, Win Metawin, Dew Jirawat, Nani Hirunkit",
        "description": "Elita maktabida kambag'al oiladan chiqqan jasur qiz Gorya maktabni boshqaruvchi eng boy va qudratli 4 nafar o'g'il bolalardan iborat F4 guruhining zulmiga qarshi bosh ko'taradi va F4 yetakchisi Timening qalbini zabt etadi.",
        "search_title": "F4 Thailand Boys Over Flowers",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/d/d1/F4_Thailand_Boys_Over_Flowers_poster.png",
        "episodes": list(range(2921, 2957)) # 36 eps
    },
    {
        "code": 319,
        "title": "Venzdey 1-fasl (Wednesday Season 1)",
        "slug": "venzdey-1-fasl-wednesday-1",
        "year": "2022",
        "status": "Tugallangan (Completed)",
        "genre": "Fantastika, Detektiv, Qora komediya, Maktab",
        "country": "AQSH",
        "category": "foreign",
        "actors": "Jenna Ortega, Emma Myers, Hunter Doohan, Gwendoline Christie, Christina Ricci",
        "description": "Addamslar oilasining sovuqqon va zukko qizi Venzdey Nevermor akademiyasiga o'qishga yuboriladi. U yerda o'zining ekstrasensorlik qobiliyatini rivojlantirib, shaharchani dahshatga solayotgan sirli qotilliklarni fosh qilishga kirishadi.",
        "search_title": "Wednesday",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/8/87/Wednesday_Netflix_series_poster.png",
        "episodes": list(range(2957, 2965)) # 8 eps
    },
    {
        "code": 320,
        "title": "Venzdey 2-fasl (Wednesday Season 2)",
        "slug": "venzdey-2-fasl-wednesday-2",
        "year": "2025",
        "status": "Tugallangan (Completed)",
        "genre": "Fantastika, Detektiv, Qora komediya",
        "country": "AQSH",
        "category": "foreign",
        "actors": "Jenna Ortega, Emma Myers, Steve Buscemi, Catherine Zeta-Jones",
        "description": "Nevermor akademiyasining ikkinchi o'quv yili. Venzdey yangi dushmanlar, oilaviy sir-asrorlar va Nevermorni tahdid solayotgan yanada xavfli qora kuchlarga qarshi kurashadi.",
        "search_title": "Wednesday Season 2",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/8/87/Wednesday_Netflix_series_poster.png",
        "episodes": list(range(2965, 2973)) # 8 eps
    },
    {
        "code": 321,
        "title": "Kulrang parazitlar / Parazit: Kulrang (Parasyte: The Grey)",
        "slug": "kulrang-parazitlar-parasyte-the-grey",
        "year": "2024",
        "status": "Tugallangan (Completed)",
        "genre": "Jangari, Fantastika, Dahshat, Triller",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Jeon So-nee, Koo Kyo-hwan, Lee Jung-hyun, Kwon Hae-hyo",
        "description": "Fazodan tushgan xavfli parazitlar insonlar miyasini egallab, ularni qotil maxluqlarga aylantira boshlaydi. Yosh qiz Su-in parazit bilan g'ayritabiiy simbiozda yashashga majbur bo'ladi va maxsus «Kulrang» guruhiga duch keladi.",
        "search_title": "Parasyte: The Grey",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/e/e0/Parasyte_The_Grey.jpg",
        "episodes": list(range(2973, 2979)) # 6 eps
    },
    {
        "code": 322,
        "title": "Tabassumingga oshiqma / Kulgingga maftunman (Falling Into Your Smile)",
        "slug": "tabassumingga-oshiqma-falling-into-your-smile",
        "year": "2021",
        "status": "Tugallangan (Completed)",
        "genre": "Kibersport, Romantika, Komediya, Yoshlik",
        "country": "Xitoy",
        "category": "foreign",
        "actors": "Xu Kai, Cheng Xiao, Zhai Xiaowen, Yao Chi",
        "description": "Tong Yao ismli iqtidorli qiz erkaklar hukmron bo'lgan professional e-sport (League of Legends) ligasining ZGDX jamoasiga birinchi professional ayol kiber-sportchi sifatida qabul qilinadi va sovuqqon sardor Lu Si-chao bilan birgalikda jahon chempionligi sari intiladi.",
        "search_title": "Falling Into Your Smile",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/0/0f/Falling_Into_Your_Smile.jpg",
        "episodes": list(range(2979, 3009)) + [3009, 3010] # 32 parts
    },
    {
        "code": 323,
        "title": "Menga yana turmushga chiq / Yana menga uylan (Marry Me Again)",
        "slug": "menga-yana-turmushga-chiq-marry-me-again",
        "year": "2025",
        "status": "Tugallangan (Completed)",
        "genre": "Romantika, Nikoh, Drama",
        "country": "Xitoy",
        "category": "foreign",
        "actors": "He Changxi, Ju Keke",
        "description": "Tushunmovchiliklar tufayli ajrashgan sobiq er-xotin yillar o'tib kutilmagan vaziyatda yana yuzma-yuz kelishadi va eski his-tuyg'ular qayta alangalanib, ikkinchi imkoniyat uchun kurash boshlanadi.",
        "search_title": "Marry Me Again 2025",
        "fallback_url": "https://www.cpophome.com/wp-content/uploads/2025/04/Marry-Me-Again.jpg",
        "episodes": list(range(3011, 3042)) # 31 eps
    },
    {
        "code": 324,
        "title": "Yashirin sevgi / Pinhona muhabbat (Hidden Love)",
        "slug": "yashirin-sevgi-hidden-love",
        "year": "2023",
        "status": "Tugallangan (Completed)",
        "genre": "Romantika, Yoshlik, Melodrama",
        "country": "Xitoy",
        "category": "foreign",
        "actors": "Zhao Lusi, Chen Zheyuan, Victor Ma, Zeng Li",
        "description": "O'smir Sang Zhi akasining eng yaqin do'sti Duan Jiaxuga yashirincha ko'ngil qo'yadi. Yillar o'tib, u ulg'ayib universitetga kirgach, ular yana uchrashadilar va bolalikdagi pinhona mehr chuqur, samimiy sevgiga aylanadi.",
        "search_title": "Hidden Love",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/2/25/Hidden_Love_poster.jpg",
        "episodes": list(range(3042, 3067)) # 25 eps
    },
    {
        "code": 325,
        "title": "Kapalak / Batterflay (Butterfly)",
        "slug": "kapalak-butterfly",
        "year": "2025",
        "status": "Tugallangan (Completed)",
        "genre": "Aygoqchilik, Triller, Jangari",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Daniel Dae Kim, Reina Hardesty, Park Hae-soo, Kim Tae-hee",
        "description": "Koreyada yashirinib yurgan sobiq AQSH razvedka agenti Devid Chon o'tmishdagi qilmishlari oqibati bilan yuzlashadi va uni yo'q qilish uchun yuborilgan yosh, shafqatsiz agent Rebekkadan qochishga majbur bo'ladi.",
        "search_title": "Butterfly 2025 Daniel Dae Kim",
        "fallback_url": None,
        "episodes": list(range(3067, 3077)) # 10 eps
    },
    {
        "code": 326,
        "title": "Mening IDyim Gangnam go‘zali (My ID is Gangnam Beauty)",
        "slug": "mening-idyim-gangnam-gozali-my-id-is-gangnam-beauty",
        "year": "2018",
        "status": "Tugallangan (Completed)",
        "genre": "Romantika, Talabalik, Go'zallik, Drama",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Cha Eun-woo, Im Soo-hyang, Jo Woo-ri, Kwak Dong-yeon",
        "description": "Bolaligida tashqi ko'rinishi tufayli masxara qilingan Kang Mi-re universitetga kirishdan oldin plastik operatsiya qildiradi. Biroq u «Gangnam go'zali» degan yangi tamg'aga duch keladi va maktabdosh Do Kyon-sok bilan haqiqiy ichki go'zallikni anglay boshlaydi.",
        "search_title": "My ID is Gangnam Beauty",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/b/bb/My_ID_is_Gangnam_Beauty.jpg",
        "episodes": list(range(3077, 3093)) # 16 eps
    },
    {
        "code": 327,
        "title": "Birinchi qor / Yashirin sevgi 2: Birinchi izgʻirin (The First Frost)",
        "slug": "birinchi-qor-the-first-frost",
        "year": "2025",
        "status": "Tugallangan (Completed)",
        "genre": "Romantika, Yoshlik, Melodrama",
        "country": "Xitoy",
        "category": "foreign",
        "actors": "Bai Jingting, Zhang Ruonan, Edward Chen",
        "description": "«Yashirin sevgi» olamining davomi: Sang Yanning maktab davridagi ilk muhabbati Ven Yifan bilan yillar o'tib tasodifan bitta xonadonda ijarachi sifatida uchrashib qolishi va o'rtalaridagi unutilmas hislarning qayta uyg'onishi.",
        "search_title": "The First Frost 2025",
        "fallback_url": None,
        "episodes": list(range(3093, 3125)) # 32 eps
    },
    {
        "code": 328,
        "title": "Qoʻrqmas va malika / Zippo va malika (Lighter and Princess)",
        "slug": "qorqmas-va-malika-lighter-and-princess",
        "year": "2022",
        "status": "Tugallangan (Completed)",
        "genre": "Dasturlash, Romantika, Drama, Yoshlik",
        "country": "Xitoy",
        "category": "foreign",
        "actors": "Arthur Chen (Chen Feiyu), Zhang Jingyi, Zhao Zhiwei",
        "description": "Daho dasturchi Li Syun va a'lochi talaba Chju Yun universitetda tanishib, dasturlash jamoasi tuzadilar. Hayotiy sinovlar va xiyonatlar ularni ayirsa-da, ularning o'chmas muhabbati va orzulari qayta birlashtiradi.",
        "search_title": "Lighter and Princess",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/7/77/Lighter_and_Princess.jpg",
        "episodes": list(range(3125, 3161)) # 36 eps
    },
    {
        "code": 329,
        "title": "Zomvivor / Zombilar universiteti (Zomvivor)",
        "slug": "zomvivor-thai-zombie",
        "year": "2025",
        "status": "Tugallangan (Completed)",
        "genre": "Zombi, Dahshat, Omon qolish, Triller",
        "country": "Tailand",
        "category": "foreign",
        "actors": "Zee Pruk Panich, Nunew Chawarin, Boun Noppanut",
        "description": "Kutilmagan xavfli virus tufayli universitet kampusi qonxo'r zombilar bilan to'lib-toshadi. Bir guruh talabalar tashqi dunyodan uzilgan holda omon qolish va do'stlarini qutqarish uchun hayot-mamot jangiga kirishadilar.",
        "search_title": "Zomvivor",
        "fallback_url": None,
        "episodes": list(range(3167, 3173)) + [3073] # 7 eps
    },
    {
        "code": 330,
        "title": "Jodugar qiz 1 - 2 / Jodugar (The Witch: Part 1 & Part 2)",
        "slug": "jodugar-qiz-the-witch-parts",
        "year": "2018",
        "status": "Tugallangan (Film / Movie)",
        "genre": "Qobiliyat, Jangari, Sirli, Triller",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Kim Da-mi, Shin Si-ah, Choi Woo-shik, Park Hee-soon, Lee Jong-suk",
        "description": "Maxfiy genetik laboratoriyadan qochib, xotirasini yo'qotgan yosh qiz oddiy oilada ulg'ayadi. Ammo o'tmishdagi qotillar uni topganda, uning ichidagi dahshatli g'ayritabiiy kuch va qobiliyatlar uyg'onadi.",
        "search_title": "The Witch Part 1 The Subversion",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/7/7b/The_Witch_Part_1._The_Subversion.jpg",
        "episodes": [3074, 3075] # 2 eps
    },
    {
        "code": 331,
        "title": "Daryo uzra suzayotgan oy / Oy chiqadigan daryo (River Where the Moon Rises)",
        "slug": "daryo-uzra-suzayotgan-oy-river-where-the-moon-rises",
        "year": "2021",
        "status": "Tugallangan (Completed)",
        "genre": "Tarixiy, Jangari, Romantika, Drama",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Kim So-hyun, Na In-woo, Lee Ji-hoon, Choi Yu-hwa",
        "description": "Koguryo malikasi Pxyongan harbiy qobiliyatlarga ega askar sifatida ulg'ayadi va taxtni egallab, xalqini birlashtirishni orzu qiladi. U tinchliksevar On Dal bilan uchrashib, tarixiy va fojiali muhabbat kechiradi.",
        "search_title": "River Where the Moon Rises",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/7/7d/River_Where_the_Moon_Rises.jpg",
        "episodes": list(range(3077, 3091)) # 14 eps
    },
    {
        "code": 332,
        "title": "Mukammal toj / 21-asr qirollik oilasi (Perfect Crown)",
        "slug": "mukammal-toj-perfect-crown",
        "year": "2026",
        "status": "Tugallangan (Completed)",
        "genre": "Qirollik, Romantika, Siyosat, Drama",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Rowoon, Shin Ye-eun, Kim Min-kyu",
        "description": "Monarxiya davom etayotgan zamonaviy Janubiy Koreyada toj-taxt vorislari o'rtasidagi siyosiy o'yinlar, oilaviy intriqalar va soxta nikoh ortiga yashiringan chin muhabbat hikoyasi.",
        "search_title": "The 21st Century Grand Prince's Wife Perfect Crown",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/7/76/Perfect_Crown_poster.png",
        "episodes": list(range(3091, 3103)) # 12 eps
    },
    {
        "code": 333,
        "title": "Taxi delux / Namunali taksi (Taxi Driver)",
        "slug": "taxi-delux-taxi-driver-model-taxi",
        "year": "2021",
        "status": "Tugallangan (Completed)",
        "genre": "Qasos, Jinoyat, Jangari, Adolat",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Lee Je-hoon, Kim Eui-sung, Pyo Ye-jin, Jang Hyuk-jin",
        "description": "Qonun jazolay olmagan jinoyatchilardan jabrlangan jabrdiydalar nomidan qasos oluvchi sirli «Rainbow Taxi» xizmati. Sobiq maxsus kuchlar zobiti Kim Do-gi jabrlanuvchilar uchun adolat o'rnatadi.",
        "search_title": "Taxi Driver Korean drama",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/2/29/Taxi_Driver_2021.jpg",
        "episodes": [3104, 3105] # 2 eps
    },
    {
        "code": 334,
        "title": "Tezlik va Muhabbat / Tezlik va sevgi (Speed and Love)",
        "slug": "tezlik-va-muhabbat-speed-and-love-dual-tracks",
        "year": "2025",
        "status": "Tugallangan (Completed)",
        "genre": "Poyga, Avtosport, Romantika, Yoshlik",
        "country": "Xitoy",
        "category": "foreign",
        "actors": "Wang Anyu, Liu Haocun",
        "description": "Poyga trassalaridagi keskin tezlik, xavfli burilishlar va chempionlik sari shiddatli intilish orasida ikki yosh poygachining yuraklarida paydo bo'lgan olovli muhabbat qissasi.",
        "search_title": "Dual Tracks 2025 Chinese drama",
        "fallback_url": None,
        "episodes": list(range(3106, 3135)) # 29 eps
    },
    {
        "code": 335,
        "title": "E boʻlimining marvaridi 2-fasl (He's Into Her Season 2)",
        "slug": "e-bolimining-marvaridi-2-fasl-hes-into-her-2",
        "year": "2022",
        "status": "Tugallangan (Completed)",
        "genre": "Maktab, Yoshlik, Romantika, Drama",
        "country": "Filippin",
        "category": "foreign",
        "actors": "Belle Mariano, Donny Pangilinan",
        "description": "Maktabdagi ziddiyatlardan keyin Makspeyn va Dejvon o'z munosabatlarini rasmiylashtiradilar, ammo ularning sevgisi oilaviy sirlar va yangi raqiblar tomonidan yana jiddiy sinovdan o'tadi.",
        "search_title": "He's Into Her Season 2",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/8/86/He%27s_Into_Her_title_card.jpeg",
        "episodes": list(range(3135, 3144)) # 9 eps
    },
    {
        "code": 336,
        "title": "Bizning ajralmas sevgimiz / Yopishqoq muhabbat (Our Sticky Love)",
        "slug": "bizning-ajralmas-sevgimiz-our-sticky-love",
        "year": "2026",
        "status": "Tugallangan (Completed)",
        "genre": "Romantika, Komediya, Melodrama",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Kim Se-jeong, Lee Jong-won, Baek Sung-chul, Shin Do-hyun",
        "description": "Pivo sotish bo'yicha chempion, maxsus kuchlar sobiq zobiti Chxe Yon-ju o'z kompaniyasini saqlab qolish uchun sirli va nihoyatda nozik pivo ustasi Yun Min-juni topishga intiladi.",
        "search_title": "Brewing Love 2024",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/a/ad/Brewing_Love_poster.jpg",
        "episodes": list(range(3144, 3156)) # 12 eps
    },
    {
        "code": 337,
        "title": "Iblis bilan pari oʻrtasidagi muhabbat / Orxideya va iblis (Love Between Fairy and Devil)",
        "slug": "iblis-bilan-pari-ortasidagi-muhabbat-love-between-fairy-and-devil",
        "year": "2022",
        "status": "Tugallangan (Completed)",
        "genre": "Xianxia, Fentezi, Sehr-jodu, Romantika",
        "country": "Xitoy",
        "category": "foreign",
        "actors": "Dylan Wang (Wang Hedi), Esther Yu (Yu Shuxin), Zhang Linghe",
        "description": "Qadimiy qonxo'r iblis Dongfang Qingcang afsonaviy minoraga qamalgan edi. Mitti orxideya parisi Syaolanhua tasodifan uni ozod qilib yuboradi va ular o'rtasida sehrli tana almashinuvi hamda taqdiriy sevgi boshlanadi.",
        "search_title": "Love Between Fairy and Devil",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/6/6f/Love_Between_Fairy_and_Devil.png",
        "episodes": list(range(3156, 3192)) # 36 eps
    },
    {
        "code": 338,
        "title": "Seongsu-dong brendingi / Seongsuda brending (Branding in Seongsu)",
        "slug": "seongsu-dong-brendingi-branding-in-seongsu",
        "year": "2024",
        "status": "Tugallangan (Completed)",
        "genre": "Romantika, Ruh almashishi, Ofis, Triller",
        "country": "Janubiy Koreya",
        "category": "korea",
        "actors": "Kim Ji-eun, Lomon (Park Solomon), Yang Hye-ji, Kim Ho-young",
        "description": "Seongsu-dong marketing markazida eng qattiqqo'l marketing rahbari Kang Na-on va erkin stajyor So In-uk kutilmagan bo'sa tufayli o'z tanalarini almashtirib oladilar va xavfli fitnalar ichida qoladilar.",
        "search_title": "Branding in Seongsu",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/5/52/Branding_in_Seongsu_poster.jpg",
        "episodes": list(range(3192, 3204)) # 12 eps
    },
    {
        "code": 339,
        "title": "Sevgi qorboʻroni / Qor boʻroni paytidagi sevgi (Amidst a Snowstorm of Love)",
        "slug": "sevgi-qorboroni-amidst-a-snowstorm-of-love",
        "year": "2024",
        "status": "Tugallangan (Completed)",
        "genre": "Bilyard, Romantika, Sport, Qorli sayohat",
        "country": "Xitoy",
        "category": "foreign",
        "actors": "Leo Wu (Wu Lei), Zhao Jinmai, Wang Xingyue, Ding Xiaoying",
        "description": "Kamdan-kam uchraydigan qor bo'roni paytida yosh bilyard ustasi In Guo sobiq daho snukerchi Lin Yiyang bilan tanishib qoladi. Ularning sevgisi Lin Yiyangni yana professional sportga qaytaradi.",
        "search_title": "Amidst a Snowstorm of Love",
        "fallback_url": "https://upload.wikimedia.org/wikipedia/en/6/60/Amidst_a_Snowstorm_of_Love_poster.jpg",
        "episodes": [3204] # 1 ep
    }
]

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("=== 1. UPDATING EXISTING DORAMAS ===")
    
    # 1. Talab bo'yicha yigit (Code 261, ID 161)
    c.execute("""
        UPDATE doramas 
        SET title = 'Talab boʻyicha yigit / Obuna boʻyicha yigit (Boyfriend on Demand)'
        WHERE code = 261
    """)
    print("  [Updated Code 261] Talab bo'yicha yigit -> added Obuna bo'yicha yigit")
    
    # 2. Gyeonwoo va pari (Code 214, ID 114)
    c.execute("""
        UPDATE doramas 
        SET title = 'Gyeonwoo va pari / Kyon-U va Pari (Head Over Heels)',
            total_episodes = 12
        WHERE code = 214
    """)
    c.execute("DELETE FROM episodes WHERE dorama_id = 114")
    gyeonwoo_eps = list(range(2893, 2905)) # 12 eps
    for idx, mid in enumerate(gyeonwoo_eps, 1):
        c.execute("""
            INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality, file_id)
            VALUES (?, ?, ?, '720p', '')
        """, (114, idx, mid))
    print(f"  [Updated Code 214] Gyeonwoo va pari -> 12 episodes re-linked (2893..2904)")
    
    # 3. Xotirasiz sevgi (Code 297, ID 197)
    c.execute("""
        UPDATE doramas 
        SET title = 'Xotirasiz sevgi / Unutilgan muhabbat (Love Reset / 30 Days)'
        WHERE code = 297
    """)
    c.execute("DELETE FROM episodes WHERE dorama_id = 197")
    c.execute("""
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality, file_id)
        VALUES (197, 1, 3076, '720p', '')
    """)
    print("  [Updated Code 297] Xotirasiz sevgi -> message_id 3076 linked")
    
    # 4. Yuragimni quvvatla (Code 242, ID 142)
    # Check if episode 8 already exists
    c.execute("SELECT id FROM episodes WHERE dorama_id = 142 AND episode_number = 8")
    if not c.fetchone():
        c.execute("""
            INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality, file_id)
            VALUES (142, 8, 3205, '720p', '')
        """)
    c.execute("UPDATE doramas SET total_episodes = 8 WHERE code = 242")
    print("  [Updated Code 242] Yuragimni quvvatla -> episode 8 (3205) linked, total_eps=8")
    
    print("\n=== 2. INGESTING 31 NEW DORAMAS ===")
    
    for item in NEW_DORAMAS:
        code = item["code"]
        title = item["title"]
        slug = item["slug"]
        poster_filename = f"{slug}.jpg"
        poster_path = os.path.join(POSTERS_DIR, poster_filename)
        rel_poster_url = f"posters/{poster_filename}"
        
        # Download poster
        print(f"Processing [{code}] {title}...")
        get_best_poster(item["search_title"], item["year"], poster_path, item.get("fallback_url"))
        
        # Check if already in DB by code
        c.execute("SELECT id FROM doramas WHERE code = ?", (code,))
        existing = c.fetchone()
        
        total_eps = len(item["episodes"])
        views = 5 # realistic base
        
        if existing:
            dorama_id = existing[0]
            c.execute("""
                UPDATE doramas SET
                    title = ?, slug = ?, genre = ?, year = ?, description = ?,
                    poster_url = ?, total_episodes = ?, status = ?, country = ?,
                    actors = ?, category = ?
                WHERE id = ?
            """, (
                title, slug, item["genre"], item["year"], item["description"],
                rel_poster_url, total_eps, item["status"], item["country"],
                item["actors"], item["category"], dorama_id
            ))
            print(f"  [DB Update] Dorama ID {dorama_id} updated.")
        else:
            c.execute("""
                INSERT INTO doramas (
                    code, title, slug, genre, year, description,
                    poster_url, total_episodes, views, status, country,
                    actors, category
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                code, title, slug, item["genre"], item["year"], item["description"],
                rel_poster_url, total_eps, views, item["status"], item["country"],
                item["actors"], item["category"]
            ))
            dorama_id = c.lastrowid
            print(f"  [DB Insert] Dorama created with ID {dorama_id}, Code {code}.")
            
        # Re-insert episodes cleanly
        c.execute("DELETE FROM episodes WHERE dorama_id = ?", (dorama_id,))
        for idx, mid in enumerate(item["episodes"], 1):
            c.execute("""
                INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality, file_id)
                VALUES (?, ?, ?, '720p', '')
            """, (dorama_id, idx, mid))
            
        print(f"  [Episodes] Ingested {len(item['episodes'])} episodes for [{code}].")
        
    conn.commit()
    conn.close()
    print("\nAll 35 doramas successfully ingested and committed!")

if __name__ == "__main__":
    main()
