import urllib.request
import json
import urllib.parse
import os
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

POSTER_DIR = r"E:\Agent\Drama Bot\posters"
os.makedirs(POSTER_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

DORAMAS_META = [
    {
        "id": 4, "code": 104, "slug": "biz-barchamiz-olikmiz",
        "title": "Biz barchamiz o'likmiz", "omdb_title": "All of Us Are Dead",
        "year": 2022, "total_eps": 12,
        "genre": "Zombi, Ekshn, Maktab, Triller",
        "actors": "Park Ji-hu, Yoon Chan-young, Cho Yi-hyun, Lomon",
        "desc": "Hyosan o'rta maktabida zombi virusi tarqaladi. O'quvchilar qurolsiz, ovqatsiz va tashqi dunyodan uzilgan holda o'z maktablarida omon qolish uchun ayovsiz jangga kirishadilar.",
        "poster_file": "biz_barchamiz_olikmiz.jpg",
        "custom_poster_url": None,
        "msgs": list(range(104, 116))
    },
    {
        "id": 15, "code": 115, "slug": "olim-oyini",
        "title": "Oʻlim oʻyini", "omdb_title": "Death's Game",
        "year": 2023, "total_eps": 8,
        "genre": "Fantastika, Ekshn, Triller, Drama",
        "actors": "Seo In-guk, Park So-dam, Go Youn-jung, Lee Do-hyun",
        "desc": "Hayotidan to'yib o'z joniga qasd qilgan Choi Yi-jae O'lim ma'budasi tomonidan jazolanadi: u muqarrar o'limga mahkum bo'lgan 12 xil inson tanasida qayta tirilib, omon qolishga harakat qilishi kerak.",
        "poster_file": "olim_oyini.jpg",
        "custom_poster_url": None,
        "msgs": list(range(116, 124))
    },
    {
        "id": 24, "code": 124, "slug": "qotillar-dokoni-1-fasl",
        "title": "Qotillar do'koni 1-fasl", "omdb_title": "A Shop for Killers",
        "year": 2024, "total_eps": 8,
        "genre": "Ekshn, Triller, Sirli, Kriminal",
        "actors": "Lee Dong-wook, Kim Hye-jun, Seo Hyun-woo, Jo Han-sun",
        "desc": "Amakisi to'satdan vafot etgach, qizaloq uning qotillarga qurol-yarog' yetkazib beruvchi maxfiy onlayn do'koni borligini bilib qoladi va professional yollanma qotillar nishoniga aylanadi.",
        "poster_file": "qotillar_dokoni_s1.jpg",
        "custom_poster_url": None,
        "msgs": list(range(124, 132))
    },
    {
        "id": 37, "code": 137, "slug": "qotillar-dokoni-2-fasl",
        "title": "Qotillar do'koni 2-fasl", "omdb_title": "A Shop for Killers",
        "year": 2024, "total_eps": 8,
        "genre": "Ekshn, Triller, Kriminal",
        "actors": "Lee Dong-wook, Kim Hye-jun, Seo Hyun-woo",
        "desc": "Jian amakisining do'koni va uning xavfli merosini himoya qilishda davom etadi. Qotillar to'dasi yangi kuchlar bilan hujumga o'tadi.",
        "poster_file": "qotillar_dokoni_s2.jpg",
        "custom_poster_url": None,
        "msgs": [135, 134, 136, 137, 138, 139, 132, 133]
    },
    {
        "id": 27, "code": 127, "slug": "mening-ismim",
        "title": "Mening ismim", "omdb_title": "My Name",
        "year": 2021, "total_eps": 8,
        "genre": "Kriminal, Ekshn, Triller, Qasos",
        "actors": "Han So-hee, Park Hee-soon, Ahn Bo-hyun, Kim Sang-ho",
        "desc": "Otasining qotilidan qasos olishga ahd qilgan Yoon Ji-woo eng yirik narkotik to'dasi boshlig'iga ishonadi va soxta nom bilan politsiyaga maxfiy agent bo'lib ishga kiradi.",
        "poster_file": "mening_ismim.jpg",
        "custom_poster_url": None,
        "msgs": list(range(140, 148))
    },
    {
        "id": 31, "code": 131, "slug": "hushyor",
        "title": "Qasoskor / Hushyor (Vigilante)", "omdb_title": "Vigilante",
        "year": 2023, "total_eps": 8,
        "genre": "Ekshn, Triller, Kriminal, Psixologik",
        "actors": "Nam Joo-hyuk, Yoo Ji-tae, Lee Joon-hyuk, Kim So-jin",
        "desc": "Kunduzi politsiya akademiyasining namunali talabasi, kechasi esa qonundan qochib qutulgan ashaddiy jinoyatchilarni o'z qo'llari bilan jazolovchi xalq qasoskoriga aylanadi.",
        "poster_file": "hushyor.jpg",
        "custom_poster_url": None,
        "msgs": [148, 149, 150, 164, 178, 166, 163, 188]
    },
    {
        "id": 8, "code": 108, "slug": "baxt",
        "title": "Baxt", "omdb_title": "Happiness",
        "year": 2021, "total_eps": 12,
        "genre": "Zombi, Triller, Ekshn, Fantastika",
        "actors": "Han Hyo-joo, Park Hyung-sik, Jo Woo-jin",
        "desc": "Yangi qurilgan ko'p qavatli uyda qonxo'r yuqumli kasallik tarqaladi va butun bino karantinga olinadi. Aholi o'zaro ishonchsizlik va vahima ichida omon qolishga majbur bo'ladi.",
        "poster_file": "baxt.jpg",
        "custom_poster_url": None,
        "msgs": list(range(151, 163))
    },
    {
        "id": 25, "code": 125, "slug": "ozganing-qasosi",
        "title": "O'zganing qasosi", "omdb_title": "Revenge of Others",
        "year": 2022, "total_eps": 12,
        "genre": "Maktab, Triller, Qasos, Yoshlar",
        "actors": "Shin Ye-eun, Lomon, Seo Ji-hoon, Chae Sang-woo",
        "desc": "Egizak akasining g'alati o'limiga ishonmagan Ok Chan-mi haqiqatni aniqlash va qasos olish uchun akasining maktabiga ko'chib o'tadi.",
        "poster_file": "ozganing_qasosi.jpg",
        "custom_poster_url": None,
        "msgs": [167, 168, 169, 170, 171, 172, 165, 173, 174, 175, 176, 177]
    },
    {
        "id": 9, "code": 109, "slug": "biznes-taklifi",
        "title": "Biznes taklifi", "omdb_title": "Business Proposal",
        "year": 2022, "total_eps": 12,
        "genre": "Romantika, Komediya, Drama",
        "actors": "Ahn Hyo-seop, Kim Se-jeong, Kim Min-gue, Seol In-ah",
        "desc": "Dugonasi o'rniga soxta tanishuvga borgan Shin Ha-ri kutilmaganda o'zi ishlayotgan kompaniyaning talabchan bosh direktori Kang Tae-moo bilan to'qnash keladi.",
        "poster_file": "biznes_taklifi.jpg",
        "custom_poster_url": None,
        "msgs": [179, 180, 181, 182, 183, 184, 185, 186, 187, 189, 190, 191]
    },
    {
        "id": 23, "code": 123, "slug": "dozaxdan-kelgan-sudya",
        "title": "Do'zaxdan kelgan sudya", "omdb_title": "The Judge from Hell",
        "year": 2024, "total_eps": 14,
        "genre": "Fantastika, Kriminal, Romantika, Qora komediya",
        "actors": "Park Shin-hye, Kim Jae-young, Kim In-kwon, Kim Ah-young",
        "desc": "Do'zaxdan kelgan iblis go'zal sudya Kang Bit-na tanasiga kirib, gunohkor jinoyatchilarni do'zaxga ravona qilish uchun yer yuzida o'z sudini o'rnatadi.",
        "poster_file": "dozaxdan_kelgan_sudya.jpg",
        "custom_poster_url": None,
        "msgs": list(range(192, 206))
    },
    {
        "id": 29, "code": 129, "slug": "vinchenzo",
        "title": "Vinchenzo", "omdb_title": "Vincenzo",
        "year": 2021, "total_eps": 20,
        "genre": "Kriminal, Komediya, Qonun, Ekshn",
        "actors": "Song Joong-ki, Jeon Yeo-been, Ok Taec-yeon, Kwak Dong-yeon",
        "desc": "Italiya mafiyasining nufuzli maslahatchisi va konsigleresi Vincenzo Cassano Janubiy Koreyaga qaytadi va shafqatsiz korporatsiyaga qarshi mafiya usullari bilan kurashadi.",
        "poster_file": "vinchenzo.jpg",
        "custom_poster_url": None,
        "msgs": list(range(206, 226))
    },
    {
        "id": 28, "code": 128, "slug": "asl-gozallik",
        "title": "Asl go'zallik", "omdb_title": "True Beauty",
        "year": 2020, "total_eps": 16,
        "genre": "Romantika, Yoshlar, Komediya",
        "actors": "Moon Ga-young, Cha Eun-woo, Hwang In-youp, Park Yoo-na",
        "desc": "Tashqi ko'rinishi tufayli kamsitilgan Lim Ju-kyung pardoz sirlarini o'rganib go'zallik timsoliga aylanadi. Maktabning eng chiroyli ikki yigiti uning asl chehrasini bilib qoladi.",
        "poster_file": "asl_gozallik.jpg",
        "custom_poster_url": None,
        "msgs": list(range(226, 242))
    },
    {
        "id": 30, "code": 130, "slug": "goblin",
        "title": "Goblin", "omdb_title": "Guardian: The Lonely and Great God",
        "year": 2016, "total_eps": 16,
        "genre": "Fantastika, Romantika, Drama, Komediya",
        "actors": "Gong Yoo, Kim Go-eun, Lee Dong-wook, Yoo In-na, Yook Sung-jae",
        "desc": "Abadiy yashash la'natiga duchor bo'lgan 900 yoshli Goblin (Dokkebbi) o'z ko'kragidagi ko'rinmas qilichni sug'urib, unga xotirjamlik baxsh eta oladigan yagona inson — 'Goblin kelini'ni uchratadi.",
        "poster_file": "goblin.jpg",
        "custom_poster_url": None,
        "msgs": list(range(242, 258))
    },
    {
        "id": 14, "code": 114, "slug": "k2-tansoqchi",
        "title": "K2 tansoqchi", "omdb_title": "The K2",
        "year": 2016, "total_eps": 16,
        "genre": "Ekshn, Siyosiy triller, Romantika",
        "actors": "Ji Chang-wook, Im Yoon-ah, Song Yoon-ah, Jo Sung-ha",
        "desc": "Sobiq yollanma askar Kim Je-ha prezidentlikka nomzodning maxfiy oilaviy tansoqchisi bo'lib ishga kiradi va siyosiy intrigalar hamda qasos girdobiga tushadi.",
        "poster_file": "k2_tansoqchi.jpg",
        "custom_poster_url": None,
        "msgs": list(range(258, 274))
    },
    {
        "id": 16, "code": 116, "slug": "katta-sichqon",
        "title": "Katta sichqon", "omdb_title": "Big Mouth",
        "year": 2022, "total_eps": 16,
        "genre": "Kriminal, Qonun, Triller, Drama",
        "actors": "Lee Jong-suk, Im Yoon-ah, Kim Joo-hun, Ok Ja-yeon",
        "desc": "G'alaba qozonish darajasi 10% bo'lgan omadsiz advokat Park Chang-ho to'satdan dahshatli fitnaga uchrab, dunyoning eng daho firibgari 'Big Mouse' deb qamoqqa tashlanadi.",
        "poster_file": "katta_sichqon.jpg",
        "custom_poster_url": None,
        "msgs": list(range(274, 290))
    },
    {
        "id": 17, "code": 117, "slug": "toqqiz-dumli-tulki-1-fasl",
        "title": "To'qqiz dumli tulki 1-fasl", "omdb_title": "Tale of the Nine Tailed",
        "year": 2020, "total_eps": 16,
        "genre": "Fantastika, Romantika, Triller",
        "actors": "Lee Dong-wook, Jo Bo-ah, Kim Bum, Kim Yong-ji",
        "desc": "Ming yillik to'qqiz dumli afsonaviy tulki (Gumiho) Lee Yeon zamonaviy shaharda yashaydi va o'zining qayta tug'ilgan sevgilisini qidiradi.",
        "poster_file": "toqqiz_dumli_tulki_s1.jpg",
        "custom_poster_url": None,
        "msgs": list(range(290, 306))
    },
    {
        "id": 38, "code": 138, "slug": "toqqiz-dumli-tulki-2-fasl",
        "title": "To'qqiz dumli tulki 2-fasl (1938)", "omdb_title": None,
        "year": 2023, "total_eps": 12,
        "genre": "Fantastika, Ekshn, Tarixiy, Komediya",
        "actors": "Lee Dong-wook, Kim So-yeon, Kim Bum, Ryu Kyung-soo",
        "desc": "Kutilmagan hodisa tufayli Lee Yeon 1938-yilgi notinch Koreyaga tushib qoladi. U hozirgi zamonga qaytish uchun eski dushmanlari va o'sha davr xavflariga qarshi kurashadi.",
        "poster_file": "toqqiz_dumli_tulki_s2.jpg",
        "custom_poster_url": "https://upload.wikimedia.org/wikipedia/en/b/b2/Tale_of_the_Nine_Tailed_1938.png",
        "msgs": list(range(306, 318))
    }
]

print(f"Jami ro'yxatga olingan doramalar: {len(DORAMAS_META)} ta")
