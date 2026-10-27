import os
import re
import sys
import sqlite3

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = r"E:\Agent\Drama Bot\doramas.db"
MD_PATH = r"C:\Users\MuhammadSodiq\.gemini\antigravity\brain\680976b1-3abc-4cda-8304-fa727e684760\doramalar_royxati.md"
POSTERS_DIR = r"E:/Agent/Drama Bot/posters"

# 1. Parse doramalar_royxati.md
with open(MD_PATH, "r", encoding="utf-8") as f:
    text = f.read()

lines = text.splitlines()
parsed_dramas = []
current_title = None
current_msgs = []

for line in lines:
    line = line.strip()
    if not line or line.startswith("==="):
        continue
    
    m = re.match(r"^([A-Za-z0-9\s':\(\)\/\-\?,!]+?)\s+(?:#\s*)?1\.(?:https?://t\.me/c/\d+/(\d+))", line)
    if m:
        if current_title and current_msgs:
            parsed_dramas.append((current_title, current_msgs))
        current_title = m.group(1).strip()
        current_msgs = []
        found = re.findall(r"(?:https?://t\.me/c/\d+/(\d+))", line)
        current_msgs.extend([int(x) for x in found])
        continue
    
    links = re.findall(r"(?:https?://t\.me/c/\d+/(\d+))", line)
    if links and current_title:
        current_msgs.extend([int(x) for x in links])

if current_title and current_msgs:
    parsed_dramas.append((current_title, current_msgs))

print(f"✅ MD fayldan {len(parsed_dramas)} ta dorama o'qib olindi.\n")

# Metadata registry for all 44 doramas
# Key is normalized title match
METADATA = {
    "yovuzlarning yovuzi": {
        "title": "Yovuzlarning yovuzi (The Worst of Evil)",
        "slug": "yovuzlarning_yovuzi",
        "code": 105,
        "existing_id": 5,
        "genre": "Jangari, Kriminal, Triller, Drama",
        "year": 2023,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Ji Chang-wook, Wi Ha-joon, Im Se-mi, BIBI",
        "description": "1990-yillarda Seulda Janubiy Koreya, Xitoy va Yaponiya o'rtasidagi yirik narkotik savdosi tarmog'iga yashirin kirib borgan politsiyachi Pak Jun-mo va mafiya yetakchisi Jung Gi-chul o'rtasidagi shafqatsiz kurash.",
    },
    "pinokkio (sirli olam)": {
        "title": "Pinokkio / Sirli Olam (Pinocchio)",
        "slug": "pinokkio",
        "code": 107,
        "existing_id": 7,
        "genre": "Melodrama, Romantika, Drama, Komediya",
        "year": 2014,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Lee Jong-suk, Park Shin-hye, Kim Young-kwang, Lee Yu-bi",
        "description": "Yolg'on gapirganda hiqichoq tutadigan 'Pinokkio sindromi'ga chalingan qiz va o'tmishi sirli yigitning haqiqatni yorituvchi jurnalistga aylanish yo'lidagi sarguzashtlari va samimiy sevgisi.",
    },
    "do'zaxdagi notanishlar": {
        "title": "Do'zaxdagi notanishlar (Strangers from Hell)",
        "slug": "dozaxdagi_notanishlar",
        "code": 110,
        "existing_id": 10,
        "genre": "Psixologik triller, Dahshat, Sirli",
        "year": 2019,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Im Si-wan, Lee Dong-wook, Lee Jung-eun, Park Jong-hwan",
        "description": "Seulga ish izlab kelgan yigit shubhali va qo'rqinchli qo'shnilar yashaydigan arzon yotoqxonaga joylashadi. Tez orada bu yer haqiqiy do'zax ekani fosh bo'ladi.",
    },
    "aqldan ozgan ammo hammasi joyda": {
        "title": "Aqldan ozgan ammo hammasi joyda (It's Okay to Not Be Okay)",
        "slug": "aqldan_ozgan_ammo_hammasi_joyda",
        "code": 111,
        "existing_id": 11,
        "genre": "Psixologik, Romantika, Drama, Fentezi",
        "year": 2020,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Kim Soo-hyun, Seo Yea-ji, Oh Jung-se, Park Gyu-young",
        "description": "Psixiatriya bo'limi xodimi va bolalar kitoblari yozuvchisi bo'lgan antisotsial ayolning bir-birlarining ruhiy jarohatlarini davolashga intilishi haqidagi ajoyib hikoya.",
    },
    "doona!": {
        "title": "Doona! (Doona)",
        "slug": "doona",
        "code": 113,
        "existing_id": 13,
        "genre": "Romantika, Yoshlar, Drama",
        "year": 2023,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Bae Suzy, Yang Se-jong, Ha Young, Park Se-wan",
        "description": "Mashhurlik cho'qqisida kutilmaganda shou-biznesni tark etgan sobiq K-pop yulduzi Duna va oddiy talaba yigitning bir uyda yashashi natijasida paydo bo'lgan nozik munosabatlar.",
    },
    "oltin qoshiq": {
        "title": "Oltin qoshiq (The Golden Spoon)",
        "slug": "oltin_qoshiq",
        "code": 102,
        "existing_id": 2,
        "genre": "Fentezi, Psixologik, Drama, Triller",
        "year": 2022,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Yook Sung-jae, Lee Jong-won, Jung Chae-yeon, Yeonwoo",
        "description": "Kambag'al oilada tug'ilgan iqtidorli yigit sirli sehrli oltin qoshiq yordamida boy oilaning farzandi bilan hayotini almashtirish imkoniyatiga ega bo'ladi.",
    },
    "alvon yuraklar: koryo / oy oshiqlari": {
        "title": "Alvon yuraklar: Koryo / Oy Oshiqlari (Moon Lovers)",
        "slug": "alvon_yuraklar_koryo",
        "code": 103,
        "existing_id": 3,
        "genre": "Tarixiy, Romantika, Fentezi, Melodrama",
        "year": 2016,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Lee Joon-gi, IU (Lee Ji-eun), Kang Ha-neul, Nam Joo-hyuk, Baekhyun",
        "description": "Quyosh tutilishi paytida 21-asrdan Koryo sulolasi davriga tushib qolgan zamonaviy qiz Xa-jin va taxt uchun kurashayotgan shafqatsiz shahzodalar o'rtasidagi muhabbat afsonasi.",
    },
    "orol 2 fasl": {
        "title": "Orol 2-fasl (Island Season 2)",
        "slug": "orol_s2",
        "code": 139,
        "existing_id": None,
        "genre": "Jangari, Fentezi, Dahshat, Triller",
        "year": 2023,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Kim Nam-gil, Lee Da-hee, Cha Eun-woo, Sung Joon",
        "description": "Cheju orolida yovuz kuchlar va iblislar dunyoni vayron qilishga intilayotgan paytda o'lmas jangchi Van, ruhoniy Yoxan va Mi-xoning hal qiluvchi jangi.",
    },
    "orol 1 fasl": {
        "title": "Orol 1-fasl (Island Season 1)",
        "slug": "orol_s1",
        "code": 119,
        "existing_id": 19,
        "genre": "Jangari, Fentezi, Dahshat, Triller",
        "year": 2022,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Kim Nam-gil, Lee Da-hee, Cha Eun-woo, Sung Joon",
        "description": "Qadimiy qarg'ishga duch kelgan sirli Cheju orolida iblis ovchisi, quvg'in qilingan boy merosxo'r va yosh katolik ruhoniyining taqdirlari birlashadi.",
    },
    "qish sonatasi": {
        "title": "Qish sonatasi (Winter Sonata)",
        "slug": "qish_sonatasi",
        "code": 120,
        "existing_id": 20,
        "genre": "Melodrama, Romantika, Klassika",
        "year": 2002,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Bae Yong-joon, Choi Ji-woo, Park Yong-ha, Park Sol-mi",
        "description": "Butun dunyo bo'ylab K-dramalar to'lqinini (Hallyu) boshlab bergan afsonaviy dorama. Birinchi muhabbat, fojiali xotira yo'qotish va taqdirning kutilmagan uchrashuvlari.",
    },
    "vorislar": {
        "title": "Vorislar (The Heirs)",
        "slug": "vorislar",
        "code": 122,
        "existing_id": 22,
        "genre": "Romantika, Yoshlar, Drama, Komediya",
        "year": 2013,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Lee Min-ho, Park Shin-hye, Kim Woo-bin, Kim Ji-won, Kang Ha-neul",
        "description": "Koreyaning eng boy 1% korporatsiyalari vorislari tahsil oladigan elita maktabi va u yerga adashib tushib qolgan oddiy mehnatkash qiz o'rtasidagi unutilmas sevgi.",
    },
    "notanish doktor": {
        "title": "Notanish doktor (Doctor Stranger)",
        "slug": "notanish_doktor",
        "code": 126,
        "existing_id": 26,
        "genre": "Tibbiyot, Jangari, Romantika, Triller",
        "year": 2014,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Lee Jong-suk, Jin Se-yeon, Park Hae-jin, Kang So-ra",
        "description": "Shimoliy Koreyada daho jarroh bo'lib yetishgan va Janubiy Koreyaga qochib o'tgan Park Xun o'zining yo'qolgan sevgilisini topish uchun Janubdagi nufuzli shifoxonada faoliyat boshlaydi.",
    },
    "darbadar ruh 1 fasl": {
        "title": "Darbadar ruh 1-fasl (Alchemy of Souls)",
        "slug": "darbadar_ruh_s1",
        "code": 106,
        "existing_id": 6,
        "genre": "Fentezi, Jangari, Romantika, Tarixiy",
        "year": 2022,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Lee Jae-wook, Jung So-min, Hwang Min-hyun, Shin Seung-ho",
        "description": "Teho nomli sehrli mamlakatda ruhlarni ko'chirish sehri oqibatida qotil Nak-su zaif qiz tanasiga kirib qoladi va qudratli Chon oilasi vorisining maxfiy ustozi bo'ladi.",
    },
    "darbadar ruh 2 fasl": {
        "title": "Darbadar ruh 2-fasl: Nur va Soya (Alchemy of Souls 2)",
        "slug": "darbadar_ruh_s2",
        "code": 140,
        "existing_id": None,
        "genre": "Fentezi, Jangari, Romantika",
        "year": 2022,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Lee Jae-wook, Go Youn-jung, Hwang Min-hyun, Shin Seung-ho",
        "description": "3 yil o'tgach, o'lim yoqasidan qaytgan Jang Uk va xotirasini yo'qotgan sirli qiz Jin Bu-yon o'rtasidagi qorong'ulik va nur to'qnashuvi.",
    },
    "piramida o'yini": {
        "title": "Piramida o'yini (Pyramid Game)",
        "slug": "piramida_oyini",
        "code": 141,
        "existing_id": None,
        "genre": "Psixologik triller, Maktab, Zo'ravonlik",
        "year": 2024,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Kim Ji-yeon (Bona), Jang Da-ah, Ryu Da-in, Shin Seul-ki",
        "description": "Har oy o'quvchilar reytingiga qarab eng quyi 'F' toifadagi qizni qonuniy haqoratlash va qiynash tizimi o'rnatilgan maktabda yangi ko'chib kelgan qizning shafqatsiz tizimni sindirish rejasi.",
    },
    "pentxaus 1-fasl": {
        "title": "Pentxaus 1-fasl (The Penthouse)",
        "slug": "pentxaus_s1",
        "code": 142,
        "existing_id": None,
        "genre": "Drama, Triller, Qasos, Jinoyat",
        "year": 2020,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Lee Ji-ah, Kim So-yeon, Eugene, Um Ki-joon",
        "description": "Seul markazidagi 100 qavatli hashamatli Hera saroyida yashovchi yuqori tabaqa oilalarining boylik, obro' va farzandlarining kelajagi yo'lidagi qonli va shafqatsiz o'yinlari.",
    },
    "pentxaus 2-fasl": {
        "title": "Pentxaus 2-fasl (The Penthouse 2)",
        "slug": "pentxaus_s2",
        "code": 143,
        "existing_id": None,
        "genre": "Drama, Triller, Qasos, Jinoyat",
        "year": 2021,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Lee Ji-ah, Kim So-yeon, Eugene, Um Ki-joon",
        "description": "Qasos o'ti yanada kuchaygan ikkinchi faslda o'tmishdagi qotilliklar, xiyonatlar va yangi ittifoqlar Hera saroyini ostin-ustun qiladi.",
    },
    "pentxaus 3-fasl": {
        "title": "Pentxaus 3-fasl (The Penthouse 3)",
        "slug": "pentxaus_s3",
        "code": 144,
        "existing_id": None,
        "genre": "Drama, Triller, Qasos, Jinoyat",
        "year": 2021,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Lee Ji-ah, Kim So-yeon, Eugene, Um Ki-joon",
        "description": "Afsonaviy trillerning yakuniy hal qiluvchi fasli. Har bir qahramonning qilmishiga yarasha qasos va jazo muqarrar bo'lgan buyuk yakun.",
    },
    "zombilar qirolligi 1-fasl": {
        "title": "Zombilar qirolligi 1-fasl (Kingdom)",
        "slug": "zombilar_qirolligi_s1",
        "code": 145,
        "existing_id": None,
        "genre": "Tarixiy, Zombi, Dahshat, Triller",
        "year": 2019,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Ju Ji-hoon, Ryu Seung-ryong, Bae Doona, Kim Sung-kyu",
        "description": "Choson sulolasi davrida xalq orasida g'alati o'lat tarqaladi: o'lganlar tirilib odam go'shtiga tashlanadi. Valiahd shahzoda xalqini qutqarish uchun kurashga kirishadi.",
    },
    "zombilar qirolligi 2-fasl": {
        "title": "Zombilar qirolligi 2-fasl (Kingdom Season 2)",
        "slug": "zombilar_qirolligi_s2",
        "code": 146,
        "existing_id": None,
        "genre": "Tarixiy, Zombi, Dahshat, Triller",
        "year": 2020,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Ju Ji-hoon, Ryu Seung-ryong, Bae Doona, Kim Sung-kyu",
        "description": "Qish kelishi bilan zombilar kutilmaganda kunduzi ham harakatlana boshlaydi. Saroy ichidagi fitnalar va qonxo'r maxluqlar orasida shahzoda taxtni qutqarishga majbur.",
    },
    "zombilar qirolligi (ashin hikoyasi) 3-fasl": {
        "title": "Zombilar qirolligi: Ashin Hikoyasi (Kingdom: Ashin)",
        "slug": "zombilar_qirolligi_ashin",
        "code": 147,
        "existing_id": None,
        "genre": "Tarixiy, Zombi, Triller, Maxsus film",
        "year": 2021,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Jun Ji-hyun (Gianna Jun), Park Byung-eun, Kim Shi-ah",
        "description": "Zombilar epidemiyasini qo'zg'atgan sirli o'simlik 'Saengsacho'ning kelib chiqishi va butun oilasi qirg'in qilingan Ashin ismli shimollik qizning dahshatli qasosi.",
    },
    "jonajon uy 1-fasl": {
        "title": "Jonajon uy 1-fasl (Sweet Home)",
        "slug": "jonajon_uy_s1",
        "code": 148,
        "existing_id": None,
        "genre": "Dahshat, Fentezi, Jangari, Triller",
        "year": 2020,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Song Kang, Lee Jin-wook, Lee Si-young, Lee Do-hyun",
        "description": "Oilasidan ayrilgan tushkun yigit Cha Xyon-su ko'p qavatli uyga ko'chib o'tadi. Birdan butun insoniyat o'zlarining ichki xohish-istaklari tufayli qonxo'r maxluqlarga aylana boshlaydi.",
    },
    "jonajon uy 2-fasl": {
        "title": "Jonajon uy 2-fasl (Sweet Home Season 2)",
        "slug": "jonajon_uy_s2",
        "code": 149,
        "existing_id": None,
        "genre": "Dahshat, Fentezi, Jangari, Apokalipsis",
        "year": 2023,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Song Kang, Lee Jin-wook, Lee Si-young, Go Min-si",
        "description": "Yashil uy binosidan tashqariga chiqqan omon qolganlar butunlay maxluqlar egallagan tashqi dunyoda harbiylar va yangi tahdidlarga qarshi kurashadi.",
    },
    "yovuzlik guli": {
        "title": "Yovuzlik guli (Flower of Evil)",
        "slug": "yovuzlik_guli",
        "code": 150,
        "existing_id": None,
        "genre": "Triller, Detektiv, Melodrama, Sirli",
        "year": 2020,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Lee Joon-gi, Moon Chae-won, Jang Hee-jin, Seo Hyun-woo",
        "description": "O'zining qonli o'tmishini boshqa odam qiyofasi ortiga yashirgan namunali er va o'tmishdagi seriyali qotilliklarni tergov qilayotgan detektiv xotin o'rtasidagi shubha va muhabbat.",
    },
    "do'zax chaqiruvi": {
        "title": "Do'zax chaqiruvi (Hellbound)",
        "slug": "dozax_chaqiruvi",
        "code": 151,
        "existing_id": None,
        "genre": "Fentezi, Dahshat, Triller, Sirli",
        "year": 2021,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Yoo Ah-in, Kim Hyun-joo, Park Jeong-min, Won Jin-ah",
        "description": "Odamlarga do'zaxga mahkum etilgani haqida g'ayritabiiy xabarnomalar kela boshlaydi va belgilangan vaqtda dahshatli iblislar kelib ularni yoqib yuboradi. Jamiyat diniy fanatizm girdobiga tushadi.",
    },
    "maktabdan keyingi majburiyatlar": {
        "title": "Maktabdan keyingi majburiyatlar (Duty After School)",
        "slug": "maktabdan_keyingi_majburiyatlar",
        "code": 152,
        "existing_id": None,
        "genre": "Fantastika, Jangari, Harbiy, Triller",
        "year": 2023,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Shin Hyun-soo, Lee Soon-won, Im Se-mi, Kwon Eun-bin",
        "description": "Yer yuziga osmondan begona maxluqlar tushgach, universitetga qo'shimcha ball olish maqsadida yuqori sinf o'quvchilari qo'llariga qurol olib harbiy frontga jalb qilinadi.",
    },
    "maktabga qaytgan bezori": {
        "title": "Maktabga qaytgan bezori (High School Return of a Gangster)",
        "slug": "maktabga_qaytgan_bezori",
        "code": 153,
        "existing_id": None,
        "genre": "Fentezi, Jangari, Yoshlar, Komediya",
        "year": 2024,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Yoon Chan-young, Bong Jae-hyun, Lee Seo-jin",
        "description": "Maktabda xo'rlangan va o'z joniga qasd qilmoqchi bo'lgan 19 yoshli o'quvchi tanasiga 47 yoshli tajribali gangsterning ruhi kirib qoladi va u barcha bezorilarga dars berib qo'yadi.",
    },
    "yovuz va telba": {
        "title": "Yovuz va telba (Bad and Crazy)",
        "slug": "yovuz_va_telba",
        "code": 154,
        "existing_id": None,
        "genre": "Jangari, Komediya, Detektiv, Triller",
        "year": 2021,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Lee Dong-wook, Wi Ha-joon, Han Ji-eun, Cha Hak-yeon",
        "description": "O'z martabasi uchun har qanday adolatsizlikka ko'z yumadigan muttaham tergovchi Ryu Su-yol hayotida adolatparvar, lekin jinnivash 'K' paydo bo'ladi.",
    },
    "parallel olamlar (w: two worlds)": {
        "title": "Parallel olamlar: Ikki dunyo (W: Two Worlds)",
        "slug": "parallel_olamlar_w",
        "code": 155,
        "existing_id": None,
        "genre": "Fantastika, Romantika, Triller, Fentezi",
        "year": 2016,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Lee Jong-suk, Han Hyo-joo, Jung Yoo-jin, Lee Tae-hwan",
        "description": "Mashhur veb-komiks muallifining qizi chizilgan komiks olamiga tortilib ketadi va komiksning bosh qahramoni Kan Chul bilan uchrashadi. Real hayot va komiks dunyosi tutashadi.",
    },
    "jahldor rohib": {
        "title": "Jahldor rohib (The Fiery Priest)",
        "slug": "jahldor_rohib",
        "code": 156,
        "existing_id": None,
        "genre": "Jangari, Komediya, Kriminal, Detektiv",
        "year": 2019,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Kim Nam-gil, Kim Sung-kyun, Lee Hanee, Go Jun",
        "description": "Sobiq maxsus xizmat agenti bo'lgan asabiy katolik ruhoniy keksa ustozi o'ldirilgach, qotillarni topish uchun layoqatsiz detektiv va beadab prokuror bilan birlashadi.",
    },
    "badavlat x politsiyachi": {
        "title": "Badavlat X politsiyachi (Flex X Cop)",
        "slug": "badavlat_x_politsiyachi",
        "code": 157,
        "existing_id": None,
        "genre": "Jangari, Komediya, Kriminal, Detektiv",
        "year": 2024,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Ahn Bo-hyun, Park Ji-hyun, Kang Sang-jun, Kim Shin-bi",
        "description": "Boy oilaning erka vorisi kutilmaganda politsiyaning qotilliklar bo'limiga detektiv qilib tayinlanadi. U o'zining ulkan boyligi va aloqalaridan foydalanib eng qiyin jinoyatlarni fosh qiladi.",
    },
    "quyosh avlodlari": {
        "title": "Quyosh avlodlari (Descendants of the Sun)",
        "slug": "quyosh_avlodlari",
        "code": 158,
        "existing_id": None,
        "genre": "Romantika, Jangari, Harbiylar, Melodrama",
        "year": 2016,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Song Joong-ki, Song Hye-kyo, Jin Goo, Kim Ji-won",
        "description": "Maxsus kuchlar kapitani Yu Si-jin va jarroh shifokor Kan Mo-yon urush va tabiiy ofatlar girdobida qolgan Uruk davlatida xizmat qilib, haqiqiy burch va sevgini kashf etadi.",
    },
    "do bong sun (kuchli qiz)": {
        "title": "Do Bong Sun: Kuchli qiz (Strong Woman Do Bong-soon)",
        "slug": "do_bong_sun",
        "code": 159,
        "existing_id": None,
        "genre": "Komediya, Romantika, Fentezi, Jangari",
        "year": 2017,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Park Bo-young, Park Hyung-sik, Ji Soo, Kim Won-hae",
        "description": "Nasldan-naslga o'tuvchi g'ayritabiiy jismoniy kuchga ega bo'lgan yoqimtoy qiz Do Bon-sun o'yin kompaniyasi rahbarining shaxsiy tansoqchisi bo'lib ishga kiradi.",
    },
    "kotiba kimga nima bo'ldi": {
        "title": "Kotiba Kimga nima bo'ldi (What's Wrong with Secretary Kim)",
        "slug": "kotiba_kimga_nima_boldi",
        "code": 160,
        "existing_id": None,
        "genre": "Romantik komediya, Ofis, Melodrama",
        "year": 2018,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Park Seo-joon, Park Min-young, Lee Tae-hwan, Kang Ki-young",
        "description": "O'ta takabbur va o'ziga bino qo'ygan vitse-prezident 9 yil davomida unga mukammal xizmat qilgan mohir kotibasi kutilmaganda iste'foga chiqmoqchi bo'lganida shokka tushadi.",
    },
    "yer qiroli": {
        "title": "Yer qiroli (King the Land)",
        "slug": "yer_qiroli",
        "code": 161,
        "existing_id": None,
        "genre": "Romantik komediya, Drama",
        "year": 2023,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Lee Jun-ho, Im Yoon-ah, Go Won-hee, Kim Ga-eun",
        "description": "Soxta tabassumlardan nafratlanuvchi nufuzli mehmonxona vorisi va har doim chin dildan kulib turishi shart bo'lgan eng yaxshi xodima o'rtasidagi go'zal sevgi qissasi.",
    },
    "janob plankton": {
        "title": "Janob Plankton (Mr. Plankton)",
        "slug": "janob_plankton",
        "code": 162,
        "existing_id": None,
        "genre": "Romantik komediya, Melodrama, Sayohat",
        "year": 2024,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Woo Do-hwan, Lee Yoo-mi, Oh Jung-se, Kim Hae-sook",
        "description": "Umri oz qolganini bilgan baxtsiz yigit xe-jo o'zining biologik otasini topish uchun sobiq sevgilisini to'yi kunida o'g'irlab qochadi va unutilmas so'nggi sayohatga chiqadi.",
    },
    "25 21": {
        "title": "Yigirma besh, yigirma bir (Twenty-Five Twenty-One)",
        "slug": "yigirma_besh_yigirma_bir",
        "code": 163,
        "existing_id": None,
        "genre": "Yoshlar, Romantika, Drama, Sport",
        "year": 2022,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Kim Tae-ri, Nam Joo-hyuk, Bona (Kim Ji-yeon), Choi Hyun-wook",
        "description": "1998-yildagi iqtisodiy inqiroz davrida qilichbozlik orzusidan voz kechmagan o'jar qiz va hayoti barbod bo'lgan yosh yigitning 22 va 18 yoshda tanishib, 25 va 21 yoshda sevishgani haqida.",
    },
    "zolimning oshpazi": {
        "title": "Zolimning oshpazi (Bon Appétit, Your Majesty)",
        "slug": "zolimning_oshpazi",
        "code": 164,
        "existing_id": None,
        "genre": "Tarixiy, Fentezi, Komediya, Melodrama",
        "year": 2025,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Im Yoon-ah, Lee Chae-min, Kang Han-na, Choi Gwi-hwa",
        "description": "Zamonaviy mohir oshpaz qiz Choson davriga tushib qoladi va injiq, shafqatsiz zolim qirolning qalbini o'zining betakror oshpazlik mahorati bilan zabt etishga majbur bo'ladi.",
    },
    "oy og'ushidagi quyosh": {
        "title": "Oy og'ushidagi quyosh (Moon Embracing the Sun)",
        "slug": "oy_ogushidagi_quyosh",
        "code": 165,
        "existing_id": None,
        "genre": "Tarixiy, Romantika, Fentezi, Drama",
        "year": 2012,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Kim Soo-hyun, Han Ga-in, Jung Il-woo, Kim Min-seo",
        "description": "Choson qiroli Li Xvon va qora sehr qurboni bo'lib xotirasini yo'qotgan hamda shaman ayolga aylangan sevgilisi Vol o'rtasidagi fojiali va sirlarga to'la buyuk sevgi.",
    },
    "ierarxiya": {
        "title": "Ierarxiya (Hierarchy)",
        "slug": "ierarxiya",
        "code": 166,
        "existing_id": None,
        "genre": "Yoshlar, Triller, Maktab, Sirli",
        "year": 2024,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Roh Jeong-eui, Lee Chae-min, Kim Jae-won, Ji Hye-won",
        "description": "Janubiy Koreyaning eng boy 0.01% bolalari qonun va tartibni belgilaydigan Jusin o'rta maktabiga sirli yangi o'quvchi kelib qo'shiladi va maktabning mustahkam ierarxiyasini parchalaydi.",
    },
    "zolushka va to'rt ritsar": {
        "title": "Zolushka va to'rt ritsar (Cinderella and the Four Knights)",
        "slug": "zolushka_va_tort_ritsar",
        "code": 167,
        "existing_id": None,
        "genre": "Romantik komediya, Yoshlar, Drama",
        "year": 2016,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Park So-dam, Jung Il-woo, Ahn Jae-hyun, Lee Jung-shin",
        "description": "Kambag'al, mehnatkash qizga kutilmaganda badavlat milliarder boboning bir-biriga dushman bo'lgan uch erka nevarasini tarbiyalash uchun ulkan saroyga ko'chib o'tish taklif qilinadi.",
    },
    "100 kunlik yolg'on": {
        "title": "100 kunlik yolg'on (100 Days of Deception)",
        "slug": "yuz_kunlik_yolgon",
        "code": 168,
        "existing_id": None,
        "genre": "Tarixiy, Josuslik, Triller, Romantika",
        "year": 2026,
        "country": "Janubiy Koreya",
        "status": "Ongoing",
        "actors": "Kim Yoo-jung, Park Jin-young, Kim Hyun-joo, Lee Moo-saeng",
        "description": "1930-yillarda Amerikaga qochishni orzu qilgan mohir cho'ntakkesar qiz mustaqillik harakati topshirig'i bilan yapon ma'muriyatiga tarjimon sifatida 100 kunga yashirin kiradi.",
    },
    "30 lekin 17": {
        "title": "O'ttiz, lekin o'n yetti (Still 17 / Thirty But Seventeen)",
        "slug": "ottiz_lekin_on_yetti",
        "code": 169,
        "existing_id": None,
        "genre": "Romantik komediya, Melodrama",
        "year": 2018,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Shin Hye-sun, Yang Se-jong, Ahn Hyo-seop, Ye Ji-won",
        "description": "17 yoshida fojiali avariyaga uchrab komaga tushgan va 13 yildan so'ng 30 yoshli tanada 17 yoshli aql bilan uyg'ongan skripkachi qiz va o'tmish aybdorligi tufayli dunyodan yakkalangan yigit.",
    },
    "orzular qanotida": {
        "title": "Orzular qanotida (Dream High)",
        "slug": "orzular_qanotida",
        "code": 170,
        "existing_id": None,
        "genre": "Musiqiy, Yoshlar, Romantika, Maktab",
        "year": 2011,
        "country": "Janubiy Koreya",
        "status": "Yakunlangan",
        "actors": "Bae Suzy, Kim Soo-hyun, Taecyeon, IU, Ham Eun-jung, Wooyoung",
        "description": "Kirin san'at maktabida tahsil olayotgan va jahon K-pop yulduziga aylanishni orzu qilgan iqtidorli yoshlarning kurashi, sevgisi va orzularga intilishi.",
    }
}

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

total_deployed = 0
total_episodes_inserted = 0

print("="*60)
print("🚀 MASTER INGESTION: 44 TA DORAMA VA BARCHA QISMLARNI BAZAGA KIRGIZISH")
print("="*60)

for md_title, raw_msgs in parsed_dramas:
    # Normalize title key
    norm_key = md_title.lower().strip()
    # Find matching meta
    meta = None
    for k, v in METADATA.items():
        if k in norm_key or norm_key in k:
            meta = v
            break
    
    if not meta:
        print(f"⚠️ METADATA TOPILMADI: '{md_title}'")
        continue

    # Deduplicate and order message IDs
    dedup_msgs = []
    seen = set()
    for m in raw_msgs:
        # Special check for Notanish doktor duplicate msg 510
        if meta["slug"] == "notanish_doktor" and m == 510:
            continue
        if m not in seen:
            seen.add(m)
            dedup_msgs.append(m)

    total_eps = len(dedup_msgs)
    slug = meta["slug"]
    code = meta["code"]
    title = meta["title"]
    genre = meta["genre"]
    year = meta["year"]
    country = meta["country"]
    status = meta["status"]
    actors = meta["actors"]
    desc = meta["description"]
    poster_path = f"{POSTERS_DIR}/{slug}.jpg"

    # Verify poster file exists
    local_poster_file = os.path.join(r"E:\Agent\Drama Bot\posters", f"{slug}.jpg")
    if not os.path.exists(local_poster_file):
        print(f"❌ Poster yo'q: {local_poster_file}")

    # Check if dorama exists by existing_id or by code or by slug
    existing_id = meta.get("existing_id")
    dorama_id = None

    if existing_id:
        c.execute("SELECT id FROM doramas WHERE id = ?", (existing_id,))
        r = c.fetchone()
        if r:
            dorama_id = r[0]
            c.execute("""
                UPDATE doramas SET
                    code = ?,
                    title = ?,
                    slug = ?,
                    genre = ?,
                    year = ?,
                    description = ?,
                    poster_url = ?,
                    total_episodes = ?,
                    country = ?,
                    status = ?,
                    actors = ?
                WHERE id = ?
            """, (code, title, slug, genre, year, desc, poster_path, total_eps, country, status, actors, dorama_id))
    
    if not dorama_id:
        # Check by code
        c.execute("SELECT id FROM doramas WHERE code = ?", (code,))
        r = c.fetchone()
        if r:
            dorama_id = r[0]
            c.execute("""
                UPDATE doramas SET
                    title = ?,
                    slug = ?,
                    genre = ?,
                    year = ?,
                    description = ?,
                    poster_url = ?,
                    total_episodes = ?,
                    country = ?,
                    status = ?,
                    actors = ?
                WHERE id = ?
            """, (title, slug, genre, year, desc, poster_path, total_eps, country, status, actors, dorama_id))
        else:
            # Insert new
            c.execute("""
                INSERT INTO doramas (code, title, slug, genre, year, description, poster_url, total_episodes, country, status, actors)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (code, title, slug, genre, year, desc, poster_path, total_eps, country, status, actors))
            dorama_id = c.lastrowid

    # Now handle episodes
    # Delete old episodes for this dorama to guarantee pure, clean state
    c.execute("DELETE FROM episodes WHERE dorama_id = ?", (dorama_id,))

    # Insert all episodes sequentially
    ep_rows = []
    for ep_num, msg_id in enumerate(dedup_msgs, 1):
        # standard 400MB approximate size
        ep_rows.append((dorama_id, ep_num, msg_id, "", 400000000, "1080p"))

    c.executemany("""
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_id, file_size, quality)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ep_rows)

    total_deployed += 1
    total_episodes_inserted += total_eps
    print(f"🎬 [{dorama_id:2d}] Kod: {code:3d} | {title[:35]:35s} | {total_eps:2d} qism | Poster: OK")

conn.commit()
conn.close()

print("\n" + "="*60)
print(f"Bajarildi! Jami {total_deployed} ta dorama yangilandi/qo'shildi.")
print(f"Jami {total_episodes_inserted} ta qism muvaffaqiyatli saqlandi!")
print("="*60)
