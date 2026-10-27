"""
Populate doramas.db with all 33 Kdramas from user screenshots
Including full metadata: title, slug, genre, year, description, poster_url, total_episodes, code, status, country, actors
"""
import sqlite3
import os

DORAMAS_DATA = [
    {
        "code": 102,
        "title": "Oltin qoshiq",
        "slug": "oltin-qoshiq",
        "genre": "Drama, Fantastika, Psixologik",
        "year": 2022,
        "total_episodes": 16,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Yook Sung-jae, Lee Jong-won, Jung Chae-yeon, Yeonwoo",
        "description": "Kambag'al oilada tug'ilgan Li Sin Cheon sirli kampirdan sotib olgan sehrli oltin qoshiq orqali badavlat do'stining ota-onasi bilan o'z ota-onasini almashtirish imkoniyatiga ega bo'ladi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BMmM3OTcxNDMtZDNkNy00NzAzLThjODctMDdhNTFjMTE0OGY1XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 103,
        "title": "Alvon yuraklar: Koryo",
        "slug": "alvon-yuraklar-koryo",
        "genre": "Tarixiy, Romantika, Fantastika, Triller",
        "year": 2016,
        "total_episodes": 20,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Lee Joon-gi, Lee Ji-eun (IU), Kang Ha-neul, Nam Joo-hyuk, Baekhyun",
        "description": "Quyosh tutilishi paytida 21-asrdan Koryo sulolasi davriga tushib qolgan Xa Jin imperator taxti uchun kurashayotgan shahzodalar orasidagi xavfli va ehtirosli intrigalar markazida qoladi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BN2E0MDQ3OTUtMWFiYS00MDk0LWIwZmMtZGNkNjY0OWEzNjAzXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 104,
        "title": "Biz barchamiz o'likmiz",
        "slug": "biz-barchamiz-olikmiz",
        "genre": "Qo'rqinchli, Zombi, Maktab, Ekshn",
        "year": 2022,
        "total_episodes": 12,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Park Ji-hu, Yoon Chan-young, Cho Yi-hyun, Lomon",
        "description": "Hyosan o'rta maktabida sirli zombi virusi tarqaladi. Tashqi dunyodan uzilib qolgan o'quvchilar hayotda qolish uchun bor kuchlari bilan kurashishga majbur bo'ladilar.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BMmU1OTdhYzgtNzEyMy00OTNjLWE3NGEtNTM4YmEyYWIwMzkxXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 105,
        "title": "Yovuzlarning yovuzi",
        "slug": "yovuzlarning-yovuzi",
        "genre": "Jinoyat, Triller, Ekshn, Detektiv",
        "year": 2023,
        "total_episodes": 12,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Ji Chang-wook, Wi Ha-joon, Im Se-mi, BIBI",
        "description": "1990-yillarda Janubiy Koreya, Xitoy va Yaponiya o'rtasidagi ulkan kartelni fosh qilish uchun politsiyachi Park Jun Mo Seuldagi qonli to'daga maxfiy agent bo'lib kirib boradi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BMjA5MWZlOTQtOTQ5Yi00ODIzLTlhYzYtMmVlNWU5ODFlNWViXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 106,
        "title": "Darbadar ruh",
        "slug": "darbadar-ruh",
        "genre": "Fantastika, Jangari, Romantika, Sehr",
        "year": 2022,
        "total_episodes": 30,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Lee Jae-wook, Jung So-min, Go Youn-jung, Hwang Min-hyun",
        "description": "Daeho mamlakatida odamlarning ruhlarini almashtira oladigan sehrli qobiliyat fojialarga sabab bo'ladi. Mashhur jangchi Nak-su ruhi zaif ko'r qiz Mu-deok tanasiga kirib qoladi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BN2EwYjBhZGYtMWE2Yy00ZTc4LTg4YmQtZjg0NWNjMTgwOWI3XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 107,
        "title": "Pinokkio",
        "slug": "pinokkio",
        "genre": "Drama, Romantika, Jurnalistika",
        "year": 2014,
        "total_episodes": 20,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Lee Jong-suk, Park Shin-hye, Kim Young-kwang, Lee Yu-bi",
        "description": "Yolg'on gapirganda hiqichoq tutib qoladigan 'Pinokkio sindromi'ga chalingan qiz va soxta yangiliklar qurboni bo'lgan yigit haqiqatni yoritish uchun muxbirlik olamiga kiradilar.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BYzA2ZDZkOTktNjc4NS00MTkzLThjZjctYTc2YjQ0YzFiOTZkXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 108,
        "title": "Baxt",
        "slug": "baxt",
        "genre": "Post-apokalipsis, Triller, Ekshn, Detektiv",
        "year": 2021,
        "total_episodes": 12,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Han Hyo-joo, Park Hyung-sik, Jo Woo-jin",
        "description": "Yangi yuqumli kasallik paydo bo'lib, odamlar yirtqichlarga aylanadi. Katta ko'p qavatli bino to'liq karantinga olinadi va omon qolish jangi boshlanadi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BZmRhMjBhZjUtOTFjYi00MGNhLWE5ZmMtZTU1YmRhZjBiZmRkXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 109,
        "title": "Biznes taklifi",
        "slug": "biznes-taklifi",
        "genre": "Komediya, Romantika, Biznes",
        "year": 2022,
        "total_episodes": 12,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Ahn Hyo-seop, Kim Se-jeong, Kim Min-gue, Seol In-ah",
        "description": "Shin Ha-ri dugonasining o'rniga soxta uchrashuvga boradi va kutilmaganda uchrashuvga o'zining kompaniyasi bosh direktori Kang Tae-moo chiqqanini ko'radi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BNjg0OTFkMDQtNTI0My00YTc1LTk4MDQtNmUzYjc3NTgzMTVkXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 110,
        "title": "Do'zaxdagi notanishlar",
        "slug": "dozaxdagi-notanishlar",
        "genre": "Psixologik triller, Qo'rqinchli, Sirli",
        "year": 2019,
        "total_episodes": 10,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Im Si-wan, Lee Dong-wook, Cha Rae-hyung, Lee Jung-eun",
        "description": "Seulga kelgan yosh yozuvchi arzon yotoqxonaga joylashadi. Lekin bu yotoqxonadagi qo'shnilar birin-ketin o'zlarining vahshiy va sirli qiyofalarini namoyon qila boshlaydilar.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BNTIxNDEzZDEtNDkyYi00ZjJhLWI2YjgtYzk5M2IxZDFiNDIxXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 111,
        "title": "Aqldan ozgan ammo hammasi joyda",
        "slug": "aqldan-ozgan-ammo-hammasi-joyda",
        "genre": "Psixologik drama, Romantika, Melodrama",
        "year": 2020,
        "total_episodes": 16,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Kim Soo-hyun, Seo Yea-ji, Oh Jung-se, Park Gyu-young",
        "description": "Shifoxona xodimi Moon Gang-tae va antisotsial fe'l-atvorli mashhur kitob muallifi Ko Moon-young bir-birlarining ruhiy jarohatlarini davolaydilar.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BNTNhYjQyZDktZjQzMC00OTAzLTg1ZDgtYTkxMjBkZjE4NDc4XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 112,
        "title": "Bezori yigitlar",
        "slug": "bezori-yigitlar",
        "genre": "Ekshn, Yoshlar, Maktab, Triller",
        "year": 2022,
        "total_episodes": 8,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Park Ji-hoon, Choi Hyun-wook, Hong Kyung, Shin Seung-ho",
        "description": "A'lochi o'quvchi Yeon Si-eun jismonan baquvvat bo'lmasa-da, tezkor aqli, psixologiya va atrof-muhit fizikasidan foydalanib maktab bezorilariga qarshi shafqatsiz kurash ochadi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BNTNmNmFhNjktYmM3NC00ODFlLTg5MDUtMGY4Yzg3YjE2YmZhXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 113,
        "title": "Doona",
        "slug": "doona",
        "genre": "Romantika, Yoshlar, Melodrama",
        "year": 2023,
        "total_episodes": 9,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Bae Suzy, Yang Se-jong, Ha Young, Park Se-wan",
        "description": "Mashhur qo'shiqchilik faoliyatini kutilmaganda tark etgan go'zal qiz Li Du-na talabalar yotoqxonasiga ko'chib o'tadi va oddiy talaba Li Von-jun bilan tanishadi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BYzA2MmI0M2EtNWU5Ni00ZTQyLTg4NWMtOGFjNjc3NDBmNmU2XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 114,
        "title": "K2 tansoqchi",
        "slug": "k2-tansoqchi",
        "genre": "Jangari, Triller, Siyosiy intriga, Romantika",
        "year": 2016,
        "total_episodes": 16,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Ji Chang-wook, Song Yoon-ah, Im Yoon-ah, Jo Sung-ha",
        "description": "O'z yurti tomonidan xiyonatga uchragan sobiq maxsus bo'linma askari Kim Je-ha nufuzli siyosatchining oilasi tomonidan maxfiy tansoqchi qilib yollanadi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BMTEwOGEwNGUtMjYyYy00MTBlLWJjNmUtMTgzM2JkNzRkNGI5XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 115,
        "title": "Ajal o'yini",
        "slug": "ajal-oyini",
        "genre": "Fantastika, Triller, Drama, Reinkarnatsiya",
        "year": 2023,
        "total_episodes": 8,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Seo In-guk, Park So-dam, Lee Do-hyun, Go Youn-jung, Kim Ji-hoon",
        "description": "O'z hayotidan voz kechgan Choi Yi-jae o'limni mensimagani uchun jazo sifatida 12 ta turli odamning so'nggi nafasidagi tanasida qayta tirilib, dahshatli sinovlardan o'tadi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BN2JmMWYzMzctNDAwMS00MGE4LWE1ZjgtOTY4MjkyOTAyNWU4XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 116,
        "title": "Katta sichqon",
        "slug": "katta-sichqon",
        "genre": "Yuridik triller, Qotillik, Jinoyat",
        "year": 2022,
        "total_episodes": 16,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Lee Jong-suk, Im Yoon-ah, Kim Joo-hun, Kwak Dong-yeon",
        "description": "Omadsiz advokat Park Chang-ho sirli jinoyatga aralashib qolib, bir kechada dunyodagi eng qudratli daho qallob 'Katta Sichqon' deb qamoqqa tashlanadi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BNmM2YzE4N2EtNDM2My00OWE4LTlmY2EtMzVlMzA5MTFhMDMzXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 117,
        "title": "To'qqiz dumli tulki",
        "slug": "toqqiz-dumli-tulki",
        "genre": "Fantastika, Romantika, Ekshn, Mifologiya",
        "year": 2020,
        "total_episodes": 16,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Lee Dong-wook, Jo Bo-ah, Kim Bum, Kim Yong-ji",
        "description": "Odamlar orasida yashovchi ming yillik sehrli tulki Li Yon shahar afsonalarini o'rganuvchi jasur teledastur prodyuseri Nam Ji-a bilan to'qnash keladi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BMTE0YmUxYjQtOTY4NS00MTc3LTg3ZDMtNWYxOTY3NTViYzBkXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 118,
        "title": "Ovchi itlar 1-fasl",
        "slug": "ovchi-itlar-1-fasl",
        "genre": "Ekshn, Kriminal drama, Boks",
        "year": 2023,
        "total_episodes": 8,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Woo Do-hwan, Lee Sang-yi, Huh Joon-ho, Park Sung-woong",
        "description": "Ikki yosh iqtidorli bokschi qarz tuzog'iga tushgan odamlarni talaydigan shafqatsiz sudxo'rlar imperiyasini yo'q qilish uchun birlashadilar.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BZWYwMWRiZWMtYzg4Ni00ZmM5LTlhNWItNzNjMjIzZDA4NDc5XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 119,
        "title": "Orol",
        "slug": "orol",
        "genre": "Fantastika, Ekshn, Ekzortsizm, Qorong'u afsona",
        "year": 2022,
        "total_episodes": 12,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Kim Nam-gil, Lee Da-hee, Cha Eun-woo, Sung Joon",
        "description": "Jeju orolida dunyoni yo'q qilishga intilayotgan yovuz iblislar uyg'onadi. O'lmas jangchi Van va yosh ruhoniy Yohan dunyoni qutqarish uchun jangga kiradilar.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BMDE1M2NlMTgtMWQ3MC00ZjAyLWI5ZjAtM2YxMWRlZjhmNGVhXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 120,
        "title": "Qish sonatasi",
        "slug": "qish-sonatasi",
        "genre": "Klassik Melodrama, Romantika",
        "year": 2002,
        "total_episodes": 20,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Bae Yong-joon, Choi Ji-woo, Park Yong-ha, Park Sol-mi",
        "description": "Avtohalokat tufayli xotirasini yo'qotgan yosh yigit va uning ilk sevgisi o'rtasidagi o'n yillik ayriliq va qalbni larzaga soluvchi go'zal muhabbat qissasi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BYzA2NTcxMjUtMTI4ZS00YWMxLThmOGEtM2E2NmFhMWI5OTZhXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 121,
        "title": "Samoviy ishq",
        "slug": "samoviy-ishq",
        "genre": "Romantika, Komediya, Harbiylar, Drama",
        "year": 2019,
        "total_episodes": 16,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Hyun Bin, Son Ye-jin, Seo Ji-hye, Kim Jung-hyun",
        "description": "Janubiy Koreyalik boy merosxo'r qiz bo'ron tufayli Shimoliy Koreyaga qulab tushadi va u yerda uni himoya qilishga qaror qilgan Shimoliy Koreya zobiti bilan uchrashadi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BMjA5ZGU3MDUtZTM2Ny00Zjc1LTk1Y2YtODNmOWRhMmNhZDI0XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 122,
        "title": "Vorislar",
        "slug": "vorislar",
        "genre": "Romantika, Drama, Elita maktabi",
        "year": 2013,
        "total_episodes": 20,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Lee Min-ho, Park Shin-hye, Kim Woo-bin, Kim Ji-won, Kang Ha-neul",
        "description": "Janubiy Koreyaning eng boy 1% elita oilalari farzandlari o'qiydigan maktabda boy merosxo'r Kim Tan oddiy xizmatkorning qizi Cha Eun-sangni sevib qoladi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BOGJjMTMwODQtMjc1ZS00MTQxLTljOGQtNDYyY2IzNDQzMDhmXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 123,
        "title": "Do'zaxdan kelgan sudya",
        "slug": "dozaxdan-kelgan-sudya",
        "genre": "Fantastika, Sud, Qasos, Jinoyat",
        "year": 2024,
        "total_episodes": 14,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Park Shin-hye, Kim Jae-young, Kim In-kwon, Kim A-young",
        "description": "Sirli iblis sudya Kang Bit-na tanasiga kirib oladi. Uning vazifasi — tavba qilmagan va qonuniy jazodan qochib yurgan jinoyatchilarni do'zaxga ravona qilishdir.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BNmU2N2MzODQtYmViOS00YTcxLWFiY2QtNThkYTBiMGIzYzE5XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 124,
        "title": "Qotillar do'koni",
        "slug": "qotillar-dokoni",
        "genre": "Ekshn, Jangari, Triller, Sirli",
        "year": 2024,
        "total_episodes": 8,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Lee Dong-wook, Kim Hye-jun, Seo Hyun-woo, Jo Han-sun",
        "description": "Amakisi vafot etgach, qiz uning professional merganlar uchun mo'ljallangan maxfiy qurol-yarog' do'koni qoldirganini bilib qoladi va qonli hujumlar ostida qoladi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BMGY1MDgxYjMtOGE2Mi00YmU5LTlkNTctYTE1NGEyYWRhMDliXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 125,
        "title": "O'zganing qasosi",
        "slug": "ozganing-qasosi",
        "genre": "Yoshlar, Triller, Maktab detektivi, Qasos",
        "year": 2022,
        "total_episodes": 12,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Shin Ye-eun, Lomon, Seo Ji-hoon, Chae Sang-woo",
        "description": "Egizak akasining sirli o'limiga ishonmagan sportchi qiz Chan-mi uning maktabiga o'qishga o'tadi va haqiqiy qotilni topish uchun xavfli qasos yo'liga kiradi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BN2U5MGFkNTctZDAyMC00Njg4LWI0YmItMGFiYTcyODQ4NmI5XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 126,
        "title": "Notanish doktor",
        "slug": "notanish-doktor",
        "genre": "Tibbiyot, Siyosiy triller, Romantika",
        "year": 2014,
        "total_episodes": 20,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Lee Jong-suk, Jin Se-yeon, Park Hae-jin, Kang So-ra",
        "description": "Bolaligida Shimoliy Koreyaga olib ketilgan daho jarroh Park Hoon Janubiy Koreyaga qochib o'tadi va Shimolda qolib ketgan sevgilisini qidiradi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BNWY1OTExZjMtMjgyNC00NzM2LTljMzgtZDMwOTg1MjY0MTgwXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 127,
        "title": "Mening ismim",
        "slug": "mening-ismim",
        "genre": "Qonli triller, Jangari, Politsiya, Qasos",
        "year": 2021,
        "total_episodes": 8,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Han So-hee, Park Hee-soon, Ahn Bo-hyun, Kim Sang-ho",
        "description": "Otasining qotilidan o'ch olish uchun Yoon Ji-woo jinoiy kartel boshlig'iga xizmat qiladi va uning buyrug'i bilan politsiya safiga maxfiy josus bo'lib kiradi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BNzM2M2M4YjYtYWI1ZS00Y2E3LTg1ZWYtYzA4MmQzYWRjMjM3XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 128,
        "title": "Asl go'zallik",
        "slug": "asl-gozallik",
        "genre": "Komediya, Romantika, Maktab, Make-up",
        "year": 2020,
        "total_episodes": 16,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Moon Ga-young, Cha Eun-woo, Hwang In-youp, Park Yoo-na",
        "description": "Tashqi ko'rinishi tufayli kamsitilgan Lim Ju-kyung pardoz qilish san'atini mukammal o'rganib, yangi maktabda barchani hayratga solgan go'zal 'ma'buda'ga aylanadi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BZWQ4YzA4ZjAtMjYwMi00ZDEzLWIxMjQtOTdhMmMwMTRkMmY3XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 129,
        "title": "Vinchenzo",
        "slug": "vinchenzo",
        "genre": "Qora komediya, Jinoyat, Yuridik, Ekshn",
        "year": 2021,
        "total_episodes": 20,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Song Joong-ki, Jeon Yeo-been, Ok Taec-yeon, Kim Yeo-jin",
        "description": "Italiya mafiyasining advokati bo'lgan koreys Vincenzo Cassano Seulga qaytib, shafqatsiz yirik korporatsiyaga qarshi mafiya usullari bilan kurashadi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BNTI4YjJmMTItMTlhNC00YjVjLThjMTUtMTBhYThmNDZlMGYwXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 130,
        "title": "Goblin",
        "slug": "goblin",
        "genre": "Fantastika, Melodrama, Mifologiya, Sevgi",
        "year": 2016,
        "total_episodes": 16,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Gong Yoo, Kim Go-eun, Lee Dong-wook, Yoo In-na, Yook Sung-jae",
        "description": "900 yildan beri o'lim izlab yurgan o'lmas jangchi Kim Shin (Dokkaebi) faqat uning ko'ksidagi sehrli qilichni sug'urib ola oladigan 'Dokkaebi kelini' bilan uchrashadi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BZmQzMWEyZDEtNzZhYS00NGNlLWE1MTktMmIxZWNjNWU0M2Y0XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 131,
        "title": "Hushyor",
        "slug": "hushyor",
        "genre": "Kriminal jangari, Qasos, Adolat, Triller",
        "year": 2023,
        "total_episodes": 8,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Nam Joo-hyuk, Yoo Ji-tae, Lee Joon-hyuk, Kim So-jin",
        "description": "Kunduzi politsiya akademiyasi a'lochisi Kim Ji-yong tunda yengil jazo olgan jinoyatchilarni o'z qo'llari bilan jazolaydigan shafqatsiz qasoskor 'Vigilante'ga aylanadi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BYzA4ZDQ4NzQtMmQ2Ni00Y2E3LTg1OGYtZTNkYjFiZGE0M2EzXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 132,
        "title": "Yorqin tarvuz",
        "slug": "yorqin-tarvuz",
        "genre": "Yoshlar, Musiqa, Vaqt sayohati, Romantika",
        "year": 2023,
        "total_episodes": 16,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Ryeoun, Choi Hyun-wook, Seol In-ah, Shin Eun-soo",
        "description": "Kar-soqov oilada tug'ilgan musiqaga iqtidorli o'smir g'alati musiqa do'koni orqali 1995-yilga tushib qoladi va u yerda o'zining yosh otasi bilan rok guruhi tuzadi.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BMjY5Mzk0YTAtMjRjNi00MzRhLWE3NzUtNTJjNDk5OWE2N2NmXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 133,
        "title": "Tun kirganda",
        "slug": "tun-kirganda",
        "genre": "Psixologik triller, Omon qolish, Maktab Mafiya oyini",
        "year": 2023,
        "total_episodes": 12,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Lee Jae-in, Kim Woo-seok, Choi Ye-bin, Cha Woo-min",
        "description": "O'quvchilar ekskursiyada sirli joyga tushib qolishadi va telefonlarida 'Mafiya o'yini' boshlanadi. Har bir ovoz berishda o'quvchilar o'z hayotlari bilan to'laydilar.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BYTIzMDdlYTYtZDNhYi00M2EzLWFlYTMtOGEyMzdmZTRkMzRjXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    },
    {
        "code": 134,
        "title": "Inqirozdagi doktorlar",
        "slug": "inqirozdagi-doktorlar",
        "genre": "Tibbiy romantika, Komediya, Drama",
        "year": 2024,
        "total_episodes": 16,
        "status": "Tugallangan",
        "country": "Janubiy Koreya",
        "actors": "Park Hyung-sik, Park Shin-hye, Yoon Park, Kong Seong-ha",
        "description": "Maktab davrida bir-biri bilan birinchilik uchun raqobatlashgan ikki daho shifokor o'z hayotlarining eng og'ir inqiroz davrida yana to'qnash kelib, bir-birlariga tayanch bo'ladilar.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BODg1ODcyMjYtOGMyZS00NzcyLTg0N2MtYTI0Mzg0Nzg5MzU4XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    }
]

def populate():
    db_path = r"E:\Agent\Drama Bot\doramas.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    inserted = 0
    updated = 0

    for d in DORAMAS_DATA:
        # Check if already exists by code or title
        cursor.execute("SELECT id FROM doramas WHERE code = ? OR title = ?", (d["code"], d["title"]))
        row = cursor.fetchone()
        if row:
            d_id = row[0]
            cursor.execute("""
                UPDATE doramas SET
                    title = ?, slug = ?, genre = ?, year = ?,
                    description = ?, poster_url = ?, total_episodes = ?,
                    code = ?, status = ?, country = ?, actors = ?
                WHERE id = ?
            """, (
                d["title"], d["slug"], d["genre"], d["year"],
                d["description"], d["poster_url"], d["total_episodes"],
                d["code"], d["status"], d["country"], d["actors"],
                d_id
            ))
            updated += 1
            print(f"[UPDATED] {d['code']} - {d['title']}")
        else:
            cursor.execute("""
                INSERT INTO doramas (
                    title, slug, genre, year, description,
                    poster_url, total_episodes, views, code,
                    status, country, actors
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
            """, (
                d["title"], d["slug"], d["genre"], d["year"],
                d["description"], d["poster_url"], d["total_episodes"],
                d["code"], d["status"], d["country"], d["actors"]
            ))
            inserted += 1
            print(f"[INSERTED] {d['code']} - {d['title']}")

    conn.commit()
    conn.close()
    print(f"\n[DONE] Jami doramalar: {inserted} ta yangi kiritildi, {updated} ta yangilandi.")

if __name__ == "__main__":
    populate()
