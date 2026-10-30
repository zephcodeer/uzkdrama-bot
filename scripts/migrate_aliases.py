import sqlite3
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = r"E:\Agent\Drama Bot"
DB_PATH = os.path.join(BASE_DIR, "doramas.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. aliases ustunini tekshirish yoki qo'shish
    c.execute("PRAGMA table_info(doramas)")
    cols = [r[1] for r in c.fetchall()]
    if "aliases" not in cols:
        print("doramas jadvaliga 'aliases' ustuni qo'shilmoqda...")
        c.execute("ALTER TABLE doramas ADD COLUMN aliases TEXT DEFAULT ''")
    else:
        print("'aliases' ustuni allaqachon mavjud.")

    # 2. Mashhur doramalarga muqobil va el sevgan nomlarni biriktirish
    popular_aliases = {
        111: {
            "title": "Aqldan ozgan ammo hammasi joyda (It's Okay to Not Be Okay)",
            "aliases": "Ruhiy kasal bo'lsa ham hechqisi yo'q, Telba bo'lsa ham mayli, Psycho But It's Okay"
        },
        103: {
            "title": "Alvon yuraklar: Koryo / Oy Oshiqlari (Moon Lovers)",
            "aliases": "Moon Lovers, Scarlet Heart Ryeo, Oy oshiqlari, Koryo oshiqlari"
        },
        130: {
            "title": "Goblin / Dokkebi (Guardian: The Lonely and Great God)",
            "aliases": "Dokkebi, Dokkaebi, Tokkebi, Guardian: The Lonely and Great God"
        },
        121: {
            "title": "Samoviy ishq (Crash Landing on You)",
            "aliases": "Crash Landing on You, Qulash, Sevgi qo'nishi"
        },
        122: {
            "title": "Vorislar (The Heirs)",
            "aliases": "The Heirs, Merosxo'rlar"
        },
        129: {
            "title": "Vinchenzo",
            "aliases": "Vincenzo, Vinchentso"
        },
        158: {
            "title": "Quyosh avlodlari (Descendants of the Sun)",
            "aliases": "Descendants of the Sun, Quyosh farzandlari"
        },
        171: {
            "title": "Daha 17 (Hali 17)",
            "aliases": "Still 17, Thirty But Seventeen, 30 lekin 17"
        },
        185: {
            "title": "Mening iblisim (My Demon)",
            "aliases": "My Demon, Mening shaytonim"
        },
        214: {
            "title": "Gyeonwoo va pari",
            "aliases": "Gyeonwoo and the Fairy, Gyonvu va pari"
        },
        245: {
            "title": "Mening qiroligim",
            "aliases": "Mr. Queen, Mister Qirolicha, Janob Qirolicha"
        },
        261: {
            "title": "Obuna bo'yicha yigit / Talab bo'yicha yigit",
            "aliases": "Boyfriend on Demand, Obuna bo'yicha yigit, Talab bo'yicha yigit"
        },
        309: {
            "title": "Itevon sinfi",
            "aliases": "Itaewon Class, Itaevon sinfi"
        },
        310: {
            "title": "Moviy dengiz afsonasi",
            "aliases": "Legend of the Blue Sea, Ko'k dengiz afsonasi"
        },
        311: {
            "title": "Kalmar o'yini 1 fasl",
            "aliases": "Squid Game 1, Kalmar oyini"
        },
        312: {
            "title": "Kalmar O'yini 2 fasl",
            "aliases": "Squid Game 2, Kalmar oyini 2"
        },
        313: {
            "title": "Farishtaning sevgisi",
            "aliases": "Angel's Last Mission: Love"
        },
        319: {
            "title": "Venzdey | 1-fasl",
            "aliases": "Wednesday 1, Uenzdey"
        },
        320: {
            "title": "Venzdey | 2-fasl",
            "aliases": "Wednesday 2, Uenzdey"
        },
        340: {
            "title": "Hovli (Avlu) 1-2 fasl",
            "aliases": "Avlu, The Yard, Ayollar qamoqxonasi"
        }
    }

    for code, info in popular_aliases.items():
        c.execute("""
            UPDATE doramas 
            SET title = ?, aliases = ?
            WHERE code = ?
        """, (info["title"], info["aliases"], code))
        print(f"[{code}] Yangilandi: {info['title']} | Aliases: {info['aliases']}")

    conn.commit()
    conn.close()
    print("\nMuqobil nomlar muvaffaqiyatli saqlandi!")

if __name__ == "__main__":
    migrate()
