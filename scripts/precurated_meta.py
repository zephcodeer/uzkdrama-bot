import re, sys, os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\Agent\Drama Bot')
from scripts.parse_new_dramas import parsed_dramas

EXCLUDED_MSGS = {4049, 4590, 4591, 4592, 4593, 4594, 4595, 4596, 4597, 4598, 4599, 4600}

# Known mappings for famous dramas to ensure 100% professional titles, years, genres
KNOWN_DRAMA_META = {
    "bugun barchasi sotildi": {
        "title": "Bugun barchasi sotildi (Sold Out Today)",
        "genre": "Drama, Biznes, Romantika",
        "year": 2024,
        "country": "Janubiy Koreya",
        "aliases": "Sold Out Today, Bugun barchasi sotildi",
        "desc": "Kichik biznes egalari va savdo olamida o'z o'rnini topishga urinayotgan yosh tadbirkorlarning mashaqqatli mehnati, raqobati va kutilmagan muvaffaqiyatlari haqida ta'sirli voqea."
    },
    "park xonimning nikoh shartnomasi": {
        "title": "Park xonimning nikoh shartnomasi (The Story of Park's Marriage Contract)",
        "genre": "Fantastika, Romantika, Tarixiy, Komediya",
        "year": 2023,
        "country": "Janubiy Koreya",
        "aliases": "The Story of Parks Marriage Contract, Park xonimning nikoh shartnomasi, Bae In-hyuk, Lee Se-young",
        "desc": "19-asr Choson davrida turmush o'rtog'i vafot etganidan so'ng quduqqa tashlangan Park Yeon-woo kutilmaganda 2023-yilgi zamonaviy Seulda uyg'onadi va marhum eriga quyib qo'ygandek o'xshash yigit bilan soxta nikoh tuzishga majbur bo'ladi."
    },
    "chekka qishloqdagi doktor": {
        "title": "Chekka qishloqdagi doktor (Dr. Romantic)",
        "genre": "Tibbiyot, Drama, Romantika",
        "year": 2016,
        "country": "Janubiy Koreya",
        "aliases": "Dr Romantic, Romantic Doctor Teacher Kim, Chekka qishloqdagi doktor, Ustoza Kim",
        "desc": "Mashhur mohir jarroh Bo Yong-ju kutilmaganda poytaxt tibbiyot markazidan g'oyib bo'lib, provintsiyadagi kamtarin Doldam shifoxonasida Ustoza Kim nomi bilan bemorlar hayotini qutqara boshlaydi."
    },
    "muhabbatning abadiy ifori": {
        "title": "Muhabbatning abadiy ifori (The Scent of Time)",
        "genre": "Romantika, Drama, Tarixiy",
        "year": 2023,
        "country": "Xitoy",
        "aliases": "The Scent of Time, Muhabbatning abadiy ifori, Scent of Time",
        "desc": "O'tmishda yo'l qo'ygan og'ir xatolari tufayli butun oilasini yo'qotgan yosh ayol ikkinchi imkoniyatga ega bo'lib o'tmishga qaytadi va yaqinlarini saqlab qolish uchun bor kuchini sarflaydi."
    },
    "choson nikoh agentligi": {
        "title": "Choson nikoh agentligi (Flower Crew: Joseon Marriage Agency)",
        "genre": "Tarixiy, Romantika, Komediya",
        "year": 2019,
        "country": "Janubiy Koreya",
        "aliases": "Flower Crew Joseon Marriage Agency, Choson nikoh agentligi, Kim Min-jae, Gong Seung-yeon",
        "desc": "Choson davlatining eng ko'rkam uch nafar sovchisi yosh podshohning iltimosiga binoan oddiy qashshoq qizni zodagon xonimga aylantirish bo'yicha imkonsiz topshiriqni bajarishga kirishadi."
    },
    "oddiy bir kun": {
        "title": "Oddiy bir kun (One Ordinary Day)",
        "genre": "Kriminal, Detektiv, Huquqiy, Triller",
        "year": 2021,
        "country": "Janubiy Koreya",
        "aliases": "One Ordinary Day, Oddiy bir kun, Kim Soo-hyun, Cha Seung-won",
        "desc": "Bir kechalik tasodif tufayli mudhish qotillikda asossiz ayblanib qamoqqa tashlangan begunoh kollej talabasi Kim Xyon-su va uni himoya qilishga bel bog'lagan uchinchi toifali advokatning adolat uchun kurashi."
    },
    "ilohiy gazab": {
        "title": "Ilohiy g'azab (The Divine Fury 2019)",
        "genre": "Jangari, Dahshat, Fantastika, Triller",
        "year": 2019,
        "country": "Janubiy Koreya",
        "aliases": "The Divine Fury, Ilohiy gazab, Park Seo-joon, Woo Do-hwan",
        "desc": "MMA jang chempioni Yong-hu qo'lida paydo bo'lgan sirli yara tufayli o'zida yovuz jinlarni haydash qudratini kashf etadi va ruhoniy ota An bilan birgalikda dunyoni larzaga keltirayotgan shaytoniy kuchlarga qarshi jangga kiradi."
    },
    "taksi haydovchisi": {
        "title": "Taksi haydovchisi 1-fasl (Taxi Driver)",
        "genre": "Jangari, Kriminal, Triller, Drama",
        "year": 2021,
        "country": "Janubiy Koreya",
        "aliases": "Taxi Driver, Taksi haydovchisi, Rainbow Taxi, Lee Je-hoon, Kim Eui-sung",
        "desc": "Qonun himoya qila olmagan jabrlanuvchilar uchun qasos olib beruvchi maxfiy 'Rainbow Taxi' xizmati va maxsus bo'linmaning sobiq ofitseri Kim Do-gining adolat qasosi."
    },
    "mening sevimli yolgonchim": {
        "title": "Mening sevimli yolg'onchim (My Lovely Liar)",
        "genre": "Romantika, Fantastika, Komediya, Detektiv",
        "year": 2023,
        "country": "Janubiy Koreya",
        "aliases": "My Lovely Liar, Mening sevimli yolgonchim, Kim So-hyun, Hwang Min-hyun",
        "desc": "Insonlarning yolg'on gapirayotganini eshita oladigan 'yolg'on ovchisi' Mok Sol-xi va qotillikda nohaq gumon qilinib o'z shaxsini yashirib yurgan daho bastakor Kim Do-xaning taqdiri kesishadi."
    },
    "gamgin tugilgan kun": {
        "title": "G'amgin tug'ilgan kun (Blue Birthday)",
        "genre": "Fantastika, Triller, Romantika, Yoshlar",
        "year": 2021,
        "country": "Janubiy Koreya",
        "aliases": "Blue Birthday, Gamgin tugilgan kun, Yeri, Hongseok",
        "desc": "O'zining 18 yoshli tug'ilgan kunida birinchi muhabbatini fojiali yo'qotgan Oh Ha-rin oradan 10 yil o'tib marhum yigitning fotosuratlari orqali vaqt bo'ylab o'tmishga sayohat qilish imkoniga ega bo'ladi."
    },
    "qasos": {
        "title": "Qasos (Revenge / Vengeance)",
        "genre": "Kriminal, Jangari, Triller, Drama",
        "year": 2023,
        "country": "Janubiy Koreya",
        "aliases": "Qasos, Revenge, Payback, Vengeance",
        "desc": "Adolatsizlikka uchragan qahramonning shafqatsiz kartellarga va korrupsion tizimga qarshi qasamyod qilgan shafqatsiz qasosi."
    },
    "men uchun kurash": {
        "title": "Men uchun kurash (Fight for My Way)",
        "genre": "Romantika, Komediya, Drama, Yoshlar",
        "year": 2017,
        "country": "Janubiy Koreya",
        "aliases": "Fight for My Way, Men uchun kurash, Park Seo-joon, Kim Ji-won",
        "desc": "Jamiyatda unchalik nufuzli bo'lmagan sohalarda mehnat qilayotgan to'rt nafar qadrdon do'stlarning orzulari sari olg'a intilishi va yillar davomida do'stlik ortiga yashiringan haqiqiy sevgisi."
    },
    "7 qochqin": {
        "title": "7 qochqin 1-fasl (The Escape of the Seven)",
        "genre": "Triller, Detektiv, Kriminal, Drama",
        "year": 2023,
        "country": "Janubiy Koreya",
        "aliases": "The Escape of the Seven, 7 Escape, 7 qochqin, Yetti qochqin, Penthouse rejissyori",
        "desc": "Yosh qizaloqning sirli yo'qolishiga aloqador bo'lgan yetti nafar shafqatsiz va xudbin qahramonning o'z qilmishlari uchun to'laydigan dahshatli tovonlari."
    },
    "qirolicha": {
        "title": "Qirolicha (The Empress / The Queen)",
        "genre": "Tarixiy, Drama, Siyosiy",
        "year": 2020,
        "country": "Janubiy Koreya",
        "aliases": "The Empress, The Queen, Qirolicha, Saroy qirolichasi",
        "desc": "Qirollik saroyidagi shafqatsiz fitnalar, taxt uchun kurash va kuchli irodali ayolning hokimiyat tepasiga ko'tarilishi."
    },
    "sichqon": {
        "title": "Sichqon (Mouse 2021)",
        "genre": "Psixologik triller, Detektiv, Kriminal, Sirli",
        "year": 2021,
        "country": "Janubiy Koreya",
        "aliases": "Mouse, Sichqon, Lee Seung-gi, Lee Hee-joon, Park Ju-hyun",
        "desc": "Psixopat qotillar tug'ilishidan oldin aniqlanishi mumkin bo'lgan dunyoda, adolatparvar yosh militsioner Jon Ba-rum shahar aholisini dahshatga solgan manyak qotil bilan yuzma-yuz keladi."
    },
    "ertaga": {
        "title": "Ertaga (Tomorrow 2022)",
        "genre": "Fantastika, Drama, Triller",
        "year": 2022,
        "country": "Janubiy Koreya",
        "aliases": "Tomorrow, Ertaga, Rowoon, Kim Hee-sun, Lee Soo-hyuk",
        "desc": "Ish topishga urinib yurgan yosh yigit tasodifiy halokatdan so'ng komaga tushadi va narigi dunyoning o'z joniga qasd qilmoqchi bo'lgan odamlarni qutqaruvchi maxsus farishtalar guruhiga yordamchi bo'lib ishga kiradi."
    },
    "maydagi yoshlik": {
        "title": "Maydagi yoshlik (Youth of May)",
        "genre": "Romantika, Drama, Tarixiy",
        "year": 2021,
        "country": "Janubiy Koreya",
        "aliases": "Youth of May, Maydagi yoshlik, Lee Do-hyun, Go Min-si",
        "desc": "1980-yil may oyida Gwangju shahridagi qonli tarixiy voqealar fonida bir-birini sevib qolgan iqtidorli tibbiyot talabasi va jasur hamshira qizning fojiali muhabbati."
    },
    "imkonsiz merosxor": {
        "title": "Imkonsiz merosxo'r (The Impossible Heir)",
        "genre": "Biznes, Kriminal, Triller, Drama",
        "year": 2024,
        "country": "Janubiy Koreya",
        "aliases": "The Impossible Heir, Imkonsiz merosxor, Lee Jae-wook, Lee Jun-young",
        "desc": "Janubiy Koreyaning eng yirik konglomeratini qo'lga kiritish uchun birlashgan kambag'al ammo daho yigit va konglomerat rahbarining nikohsiz tug'ilgan o'g'lining xatarli strategik rejasi."
    },
    "sen tergan raqam": {
        "title": "Sen tergan raqam (When the Phone Rings 2024)",
        "genre": "Triller, Romantika, Sirli, Drama",
        "year": 2024,
        "country": "Janubiy Koreya",
        "aliases": "When the Phone Rings, The Number You Have Dialed, Sen tergan raqam, Yoo Yeon-seok, Chae Soo-bin",
        "desc": "Siyosiy manfaatlarga ko'ra qurilgan, 3 yildan beri bir-biri bilan deyarli gaplashmaydigan er-xotin hayoti kutilmagan tahdidli qo'ng'iroq va o'g'irlab ketish hodisasi tufayli ostin-ustun bo'lib ketadi."
    },
    "darsdan tashqarida": {
        "title": "Darsdan tashqarida (Extracurricular)",
        "genre": "Kriminal, Yoshlar, Triller, Psixologik",
        "year": 2020,
        "country": "Janubiy Koreya",
        "aliases": "Extracurricular, Darsdan tashqarida, Kim Dong-hee, Park Ju-hyun",
        "desc": "Universitet kontraktini to'lash uchun yashirin jinoyat xizmatini yo'lga qo'ygan a'lochi maktab o'quvchisi Ji-suning siri fosh bo'lgach, vaziyat butunlay nazoratdan chiqib ketadi."
    },
    "parazitlar": {
        "title": "Parazitlar (Parasite 2019)",
        "genre": "Qora komediya, Triller, Drama",
        "year": 2019,
        "country": "Janubiy Koreya",
        "aliases": "Parasite, Parazitlar, Bong Joon-ho, Song Kang-ho, Choi Woo-shik",
        "desc": "Qashshoqlikda yashaydigan Kimlar oilasi badavlat Parklar xonadoniga birin-ketin firibgarlik yo'li bilan xizmatkor bo'lib kirib oladi, biroq kutilmagan sir ularni fojiali oqibatlarga olib keladi."
    },
    "shafqatsiz shahar": {
        "title": "Shafqatsiz shahar (Cruel City / Heartless City)",
        "genre": "Kriminal, Nuar, Jangari, Triller",
        "year": 2013,
        "country": "Janubiy Koreya",
        "aliases": "Cruel City, Heartless City, Shafqatsiz shahar, Jung Kyung-ho, Nam Gyu-ri",
        "desc": "Giyohvand moddalar karteliga yashirin kiritilgan politsiya xodimi va shahar kriminal olamining shafqatsiz to'qnashuvi."
    },
    "garoyib dunyo": {
        "title": "G'aroyib dunyo (Wonderful World 2024)",
        "genre": "Triller, Drama, Qasos, Psixologik",
        "year": 2024,
        "country": "Janubiy Koreya",
        "aliases": "Wonderful World, Garoyib dunyo, Cha Eun-woo, Kim Nam-joo",
        "desc": "O'z o'g'lini o'ldirgan jinoyatchi qonun oldida jazosiz qolgach, shaxsiy qasosini olgan psixologiya professori va og'ir taqdirli yosh yigitning kutilmagan sirlari."
    },
    "gullash fasli": {
        "title": "Gullash fasli (Seasons of Blossom)",
        "genre": "Yoshlar, Romantika, Drama",
        "year": 2022,
        "country": "Janubiy Koreya",
        "aliases": "Seasons of Blossom, Gullash fasli, Seo Ji-hoon, So Ju-yeon",
        "desc": "Seul maktabidagi o'smirlarning beg'ubor sevgisi, do'stligi va 6 yil oldingi fojiali yo'qotishning og'riqli xotiralari."
    },
    "taqdir iblis olib kelganda": {
        "title": "Taqdir iblis olib kelganda (Doom at Your Service)",
        "genre": "Fantastika, Romantika, Drama",
        "year": 2021,
        "country": "Janubiy Koreya",
        "aliases": "Doom at Your Service, Taqdir iblis olib kelganda, Park Bo-young, Seo In-guk",
        "desc": "Bor-yo'g'i 100 kunlik umri qolganini bilgan qiz va dunyodagi barcha narsani halokatga eltuvchi 'Myeol Mang' (Halokat ma'budi) o'rtasidagi hayot-mamot shartnomasi."
    },
    "non isi": {
        "title": "Non isi: Kim Tak Gu (King of Baking, Kim Takgu)",
        "genre": "Drama, Oilaviy, Romantika",
        "year": 2010,
        "country": "Janubiy Koreya",
        "aliases": "King of Baking Kim Takgu, Bread Love and Dreams, Non isi, Yoon Shi-yoon, Joo Won",
        "desc": "Pishiriq tayyorlash bo'yicha betakror tug'ma iste'dodga ega Kim Tak-guning mamlakatning eng mashhur novvoyiga aylanish yo'lidagi matonati va oilaviy kurashlari."
    },
    "saroy tabibi": {
        "title": "Saroy tabibi (The King's Doctor / Horse Doctor)",
        "genre": "Tarixiy, Tibbiyot, Drama",
        "year": 2012,
        "country": "Janubiy Koreya",
        "aliases": "The Kings Doctor, Horse Doctor, Saroy tabibi, Cho Seung-woo, Lee Yo-won",
        "desc": "Oddiy ot tabibi sifatida ish boshlagan past tabaqali yigitning mislsiz mehnati evaziga qirolning shaxsiy bosh tabibigacha ko'tarilishi haqida afsonaviy dorama."
    },
    "taqdir tuhfasi": {
        "title": "Taqdir tuhfasi (Fated to Love You)",
        "genre": "Romantika, Komediya, Drama",
        "year": 2014,
        "country": "Janubiy Koreya",
        "aliases": "Fated to Love You, You Are My Destiny, Taqdir tuhfasi, Jang Hyuk, Jang Na-ra",
        "desc": "Tasodifiy bitta kecha sababli kutilmaganda homilador bo'lib qolgan kamtarin kotiba va badavlat korporatsiya vorisining majburiy nikohdan haqiqiy muhabbatgacha bosib o'tgan yo'li."
    },
    "aema": {
        "title": "AEMA (Aema 2025)",
        "genre": "Drama, Komediya, Tarixiy",
        "year": 2025,
        "country": "Janubiy Koreya",
        "aliases": "Aema, Honey Lee, Jin Sun-kyu, Netflix Aema",
        "desc": "1980-yillarning boshlarida Janubiy Koreya kino olamida shov-shuv ko'targan mashhur filmni suratga olish jarayonidagi ayollar kurashi va sahna ortidagi voqealar."
    },
    "ditto": {
        "title": "Ditto (Ditto 2022)",
        "genre": "Romantika, Fantastika, Yoshlar",
        "year": 2022,
        "country": "Janubiy Koreya",
        "aliases": "Ditto, Yeo Jin-goo, Cho Yi-hyun, Kim Hye-yoon, Na In-woo",
        "desc": "1999-yilda yashovchi kollej talabasi va 2022-yilda yashovchi qiz tasodifan eski ratsiya orqali vaqtlararo bog'lanib, sevgi va do'stlik sirlari bilan bo'lishadilar."
    },
    "joze": {
        "title": "Joze (Josee 2020)",
        "genre": "Romantika, Drama",
        "year": 2020,
        "country": "Janubiy Koreya",
        "aliases": "Josee, Joze, Nam Joo-hyuk, Han Ji-min",
        "desc": "Nogironlar aravachasida o'zining xayoliy olamida yashaydigan yosh qiz Joze va uni chin yurakdan tushungan yosh talaba Yong-seokning sokin va samimiy sevgisi."
    },
    "songi 10 yil": {
        "title": "So'nggi 10 yil (The Last 10 Years)",
        "genre": "Romantika, Drama",
        "year": 2022,
        "country": "Yaponiya",
        "aliases": "The Last 10 Years, Songgi 10 yil, Nana Komatsu, Kentaro Sakaguchi",
        "desc": "Tuzalmas kamyob kasallik tufayli bor-yo'g'i 10 yillik umri qolganini bilgan 20 yoshli Matsuri endi hech qachon oshiq bo'lmaslikka qasamyod qiladi, biroq taqdir uni sinovga soladi."
    },
    "sevgi bu kecha dunyodan yoqolsa ham": {
        "title": "Sevgi bu kecha dunyodan yo'qolsa ham (Even If This Love Disappears Tonight)",
        "genre": "Romantika, Drama, Yoshlar",
        "year": 2022,
        "country": "Yaponiya",
        "aliases": "Even If This Love Disappears Tonight, Shunsuke Michieda, Riko Fukumoto",
        "desc": "Har kecha uxlab uyg'onganida xotirasi o'chib ketadigan anterograd amneziyali qiz va uning har bir kunini baxtli xotiralarga to'ldirishga va'da bergan yigitning sevgisi."
    },
    "yangi yilingiz bilan": {
        "title": "Yangi yilingiz bilan (A Year-End Medley 2021)",
        "genre": "Romantika, Komediya, Bayramona",
        "year": 2021,
        "country": "Janubiy Koreya",
        "aliases": "A Year-End Medley, Happy New Year, Yangi yilingiz bilan, Lee Dong-wook, Yoona, Kang Ha-neul",
        "desc": "Yangi yil arafasida hashamatli Emros mehmonxonasiga tashrif buyurgan turli xarakterdagi mehmonlar va xodimlarning kutilmagan uchrashuvlari hamda yangi sevgisi."
    },
    "ov vaqti": {
        "title": "Ov vaqti (Time to Hunt 2020)",
        "genre": "Jangari, Kriminal, Triller",
        "year": 2020,
        "country": "Janubiy Koreya",
        "aliases": "Time to Hunt, Ov vaqti, Lee Je-hoon, Choi Woo-shik, Park Jung-min",
        "desc": "Inqirozga yuz tutgan kelajakda qashshoqlikdan qutulish uchun yirik kazinoni tunagan to'rt nafar yosh do'stlar ortidan shafqatsiz yollanma qotil ov boshlaydi."
    },
    "kichik ormon": {
        "title": "Kichik o'rmon (Little Forest 2018)",
        "genre": "Drama, Hayotiy, Pazandachilik",
        "year": 2018,
        "country": "Janubiy Koreya",
        "aliases": "Little Forest, Kichik ormon, Kim Tae-ri, Ryu Jun-yeol, Jin Ki-joo",
        "desc": "Katta shahardagi shovqin va charchoqdan qochib o'zining qadrdon qishlog'iga qaytgan yosh qizning tabiat, toza taomlar va bolalikdagi do'stlari davrasida qalb osoyishtaligini topishi."
    },
    "ogirlangan shaxsiyat": {
        "title": "O'g'irlangan shaxsiyat (Unlocked 2023)",
        "genre": "Triller, Detektiv, Kiber-kriminal",
        "year": 2023,
        "country": "Janubiy Koreya",
        "aliases": "Unlocked, Ogirlangan shaxsiyat, Chun Woo-hee, Im Si-wan",
        "desc": "Oddiy qiz o'z smartfonini avtobusda yo'qotib qo'ygach, uni topib olgan xavfli psixopat kiber-josus uning butun shaxsiy hayotini kuzatib, boshqarishga kirishadi."
    },
    "chiqish": {
        "title": "Chiqish (Exit 2019)",
        "genre": "Jangari, Komediya, Halokat",
        "year": 2019,
        "country": "Janubiy Koreya",
        "aliases": "Exit, Chiqish, Jo Jung-suk, Yoona",
        "desc": "Butun shaharni qamrab olgan zaharli gaz bulutidan qutulish uchun qoyaga ko'tarilish bo'yicha sobiq universitet chempioni va uning dugonasi osmono'par binolar tomlari osha qochishga majbur bo'ladi."
    },
    "jimjitlik loyihasi": {
        "title": "Jimjitlik loyihasi (Project Silence 2024)",
        "genre": "Triller, Jangari, Fantastika",
        "year": 2024,
        "country": "Janubiy Koreya",
        "aliases": "Project Silence, Jimjitlik loyihasi, Lee Sun-kyun, Ju Ji-hoon",
        "desc": "Aeroportga olib boruvchi ulkan ko'prikda qalin tuman sabab yuz bergan halokatdan so'ng, harbiy laboratoriyadan qochib ketgan xavfli modifikatsiyalangan harbiy itlar omon qolganlarga hujum qila boshlaydi."
    },
    "seul poygachilari": {
        "title": "Seul poygachilari (Seoul Vibe 2022)",
        "genre": "Jangari, Komediya, Kriminal",
        "year": 2022,
        "country": "Janubiy Koreya",
        "aliases": "Seoul Vibe, Seul poygachilari, Yoo Ah-in, Go Kyung-pyo, Lee Kyu-hyung",
        "desc": "1988-yilgi Seul Olimpiadasi arafasida yosh va iqtidorli poygachilar guruhi prokuratura topshirig'i bilan yirik VIP korrupsiya fondini fosh qilish uchun xavfli operatsiyaga kirishadi."
    },
    "alam va zavq": {
        "title": "Alam va zavq (Love and Leashes 2022)",
        "genre": "Romantika, Komediya",
        "year": 2022,
        "country": "Janubiy Koreya",
        "aliases": "Love and Leashes, Alam va zavq, Seohyun, Lee Jun-young",
        "desc": "Bir ofisda ishlaydigan ikki hamkasb o'rtasida kutilmaganda pochta xatosi tufayli sirli shaxsiy qiziqish fosh bo'ladi va ular maxfiy shartnoma tuzishga kelishadilar."
    },
    "bogota yoqolganlar shahri": {
        "title": "Bogota: Yo'qolganlar shahri (Bogota: City of the Lost)",
        "genre": "Kriminal, Drama, Triller",
        "year": 2024,
        "country": "Janubiy Koreya",
        "aliases": "Bogota City of the Lost, Bogota yoqolganlar shahri, Song Joong-ki, Lee Hee-joon",
        "desc": "1990-yillarda Koreyadagi inqirozdan so'ng Kolumbiyaning Bogota shahriga ko'chib o'tgan yosh koreys yigitining mahalliy bozorlarda noldan boshlab kriminal biznes tepasiga chiqishi."
    }
}
print(f"Pre-curated known titles count: {len(KNOWN_DRAMA_META)}")
