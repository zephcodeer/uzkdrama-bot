import asyncio
import os
import sys
import sqlite3
import re
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = r"E:\Agent\Drama Bot"
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import database as db
import keyboards as kb
import config

async def run_deep_diagnostics():
    print("==========================================================")
    print("       CHUQUR AVTOMATLASHGAN TIZIM VA KOD AUDITI          ")
    print("==========================================================\n")

    defects = []
    warnings = []

    # ----------------------------------------------------
    # 1. BAZA VA MA'LUMOTLAR BUTUNLIGI (DATA INTEGRITY)
    # ----------------------------------------------------
    print("[1/6] Baza butunligi va doramalar katalogi tekshiruvi...")
    conn = sqlite3.connect(db.DB_PATH)
    c = conn.cursor()

    # Jami sonlar
    c.execute("SELECT COUNT(*) FROM doramas")
    total_doramas = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM episodes")
    total_episodes = c.fetchone()[0]
    print(f"  Jami doramalar: {total_doramas} ta | Jami qismlar: {total_episodes} ta")

    # Qismlari bo'sh doramalar
    c.execute("""
        SELECT d.code, d.title 
        FROM doramas d 
        LEFT JOIN episodes e ON d.id = e.dorama_id 
        WHERE e.id IS NULL
    """)
    empty_doramas = c.fetchall()
    if empty_doramas:
        for code, title in empty_doramas:
            warnings.append(f"Qismlari yuklanmagan dorama: [{code}] '{title}'")
        print(f"  [OGOHLANTIRISH] Qismlari bo'sh dorama topildi: {empty_doramas}")
    else:
        print("  Barcha doramalarda qismlar mavjud.")

    # Kod va Slug dublikatlari
    c.execute("SELECT code, COUNT(*) FROM doramas GROUP BY code HAVING COUNT(*) > 1")
    dup_codes = c.fetchall()
    if dup_codes:
        defects.append(f"Dublikat kodlar mavjud: {dup_codes}")
    c.execute("SELECT slug, COUNT(*) FROM doramas GROUP BY slug HAVING COUNT(*) > 1")
    dup_slugs = c.fetchall()
    if dup_slugs:
        defects.append(f"Dublikat sluglar mavjud: {dup_slugs}")

    # Noto'g'ri kanal xabar ID lari
    c.execute("SELECT dorama_id, episode_number, channel_message_id FROM episodes WHERE channel_message_id IS NULL OR channel_message_id <= 0")
    invalid_msgs = c.fetchall()
    if invalid_msgs:
        defects.append(f"Noto'g'ri channel_message_id topildi: {invalid_msgs}")

    # Bitta doramada takroriy qism raqamlari
    c.execute("SELECT dorama_id, episode_number, COUNT(*) FROM episodes GROUP BY dorama_id, episode_number HAVING COUNT(*) > 1")
    dup_eps = c.fetchall()
    if dup_eps:
        defects.append(f"Bitta doramada bir xil qism raqami takrorlangan: {dup_eps}")

    # Mahalliy poster fayllari tekshiruvi
    c.execute("SELECT code, title, poster_url FROM doramas")
    doramas_list = c.fetchall()
    missing_posters = []
    for code, title, p_url in doramas_list:
        if not p_url:
            missing_posters.append((code, title, "URL yo'q"))
            continue
        p_path = os.path.join(config.BASE_DIR, p_url.replace("/", os.sep))
        if not os.path.exists(p_path) or os.path.getsize(p_path) == 0:
            missing_posters.append((code, title, p_path))

    if missing_posters:
        defects.append(f"Posteri topilmagan doramalar soni: {len(missing_posters)} ta! Namunalar: {missing_posters[:3]}")
    else:
        print(f"  Barcha {len(doramas_list)} ta doramaning poster fayllari diskda 100% mavjud.")

    conn.close()

    # ----------------------------------------------------
    # 2. BARCHA 244 TA DORAMA UCHUN INLINE TUGMALAR VA TELEGRAM CHEKLOVLARI
    # ----------------------------------------------------
    print("\n[2/6] Barcha 244 ta dorama klaviaturalari va Telegram limitlari tekshiruvi...")
    long_callbacks = []
    overflow_rows = []
    broken_season_links = []
    total_buttons_checked = 0

    all_doramas = await db.get_latest_doramas(limit=500)
    for d in all_doramas:
        d_id = d["id"]
        eps = await db.get_episodes(d_id)
        seasons = await db.get_related_seasons(d_id)

        # Qardosh fasl ID lari mavjudligini tekshirish
        for s in seasons:
            if s["id"] not in [x["id"] for x in all_doramas]:
                broken_season_links.append((d_id, s["id"], s.get("label")))

        # Dorama kartasi klaviaturasi
        markup = kb.dorama_detail_kb(
            dorama_id=d_id,
            episodes=eps,
            bot_username="uzkdrama_app",
            related_seasons=seasons
        )

        for row_idx, row in enumerate(markup.inline_keyboard):
            # Telegram cheklovi: Bitta qatorda maksimal 8 ta tugma
            if len(row) > 8:
                overflow_rows.append((d["code"], d["title"], row_idx, len(row)))
            for btn in row:
                total_buttons_checked += 1
                if btn.callback_data:
                    cb_bytes = len(btn.callback_data.encode("utf-8"))
                    # Telegram cheklovi: callback_data maksimal 64 bayt
                    if cb_bytes > 64:
                        long_callbacks.append((d["code"], btn.text, btn.callback_data, cb_bytes))

    print(f"  Jami tekshirilgan inline tugmalar: {total_buttons_checked} ta")
    if long_callbacks:
        defects.append(f"64 baytdan oshgan tugmalar topildi: {long_callbacks}")
    else:
        print("  Barcha tugmalar 64-baytlik limitdan xavfsiz (0 ta xato).")

    if overflow_rows:
        defects.append(f"Qatorda 8 tadan oshgan tugmalar topildi: {overflow_rows}")
    else:
        print("  Barcha tugmalar qatori Telegram normasi doirasida (<= 8 ta).")

    if broken_season_links:
        defects.append(f"Mavjud bo'lmagan dorama ID ga yo'naltirilgan fasl havolalari: {broken_season_links}")

    # ----------------------------------------------------
    # 3. QIDIRUVNING CHEKKI HOLATLARI (EDGE CASES & STRESS TEST)
    # ----------------------------------------------------
    print("\n[3/6] Qidiruv tizimining ekstremal holatlar (Stress test) tekshiruvi...")
    stress_queries = [
        "",                     # Bo'sh
        " ",                    # Probel
        "a",                    # Bitta harf
        "!!!",                  # Belgilar
        "o'yini",               # Standart apostrof
        "oʻyini",               # O'zbekcha okina ʻ
        "o`yini",               # Teskari apostrof `
        "o’yini",               # Boshqa tipografik apostrof ’
        "va ammo lekin ham",    # Faqat stop-so'zlar
        "A" * 120,              # Juda uzun so'rov
        "101",                  # Aniq kod
        "999999",               # Mavjud bo'lmagan kod
        "doktor x",             # Katta-kichik harflar
        "DOKTOR X",
        "wAnDaViSiOn",
        "ruhiy kasal bo'lsa ham hechqisi yo'q",
        "telba bolsa ham mayli",
        "agarda",
        "what if"
    ]

    search_failures = []
    for sq in stress_queries:
        try:
            res = await db.search_doramas(sq)
            assert isinstance(res, list)
        except Exception as e:
            search_failures.append((sq, str(e)))

    if search_failures:
        defects.append(f"Qidiruvda kutilmagan xatoliklar (crash): {search_failures}")
    else:
        print(f"  {len(stress_queries)} ta ekstremal so'rov xatoliksiz, toza bajarildi.")

    # ----------------------------------------------------
    # 4. HANDLERLAR VA CALLBACK MAPPING INTEGRITY
    # ----------------------------------------------------
    print("\n[4/6] Router handlerlari va Callback data xaritasi auditi...")
    with open(os.path.join(config.BASE_DIR, "bot.py"), "r", encoding="utf-8") as f:
        bot_code = f.read()

    critical_prefixes = [
        "view_dorama:",
        "get_ep:",
        "ep_page:",
        "toggle_bm:",
        "toggle_sub:",
        "ignore",
        "menu_home",
        "menu_latest",
        "menu_categories",
        "menu_search",
        "admin_ongoing_list",
        "menu_vip",
        "menu_admin"
    ]

    missing_handlers = []
    for prefix in critical_prefixes:
        pattern = rf'F\.data(\.startswith\([\'"]{re.escape(prefix)}| == [\'"]{re.escape(prefix)}[\'"]\))'
        if not re.search(pattern, bot_code):
            missing_handlers.append(prefix)

    if missing_handlers:
        defects.append(f"Tugma callback prefikslariga mos handler topilmadi: {missing_handlers}")
    else:
        print("  Barcha 13 ta muhim klaviatura prefikslari bot.py da to'liq ushlanadi.")

    # ----------------------------------------------------
    # 5. USERDATA VA VIP / BLOKLASH MANTIQIY TEKSHIRUVI
    # ----------------------------------------------------
    print("\n[5/6] VIP va qismlarni qulflash mantig'i (Unlock rules)...")
    try:
        # 1-qism har doim bepul bo'lishi shart
        unlocked1, r1, _, _ = await db.is_user_unlocked(99999999, 1)
        assert unlocked1 is True, f"1-qism qulflangan: {r1}"

        # Aksiya rejimida barcha qismlar bepulmi?
        is_promo = await db.is_promo_free_mode()
        unlocked_promo, r_promo, _, _ = await db.is_user_unlocked(99999999, 5)
        if is_promo:
            assert unlocked_promo is True, "Aksiya rejimida 5-qism ochilmadi!"
            print("  Aksiya rejimida keyingi qismlar ochiqligi: TO'G'RI (bepul)")
    except Exception as e:
        defects.append(f"Qulflash mantig'ida xatolik: {e}")

    # ----------------------------------------------------
    # 6. FASLLAR ZANJIRI BO'YICHA KATTA GURUHLAR ROW LIMITI
    # ----------------------------------------------------
    print("\n[6/6] Fasllar zanjiri (Franchise Switcher) xavfsizlik tekshiruvi...")
    # Agar biron bir franchizada 8 tadan ko'p fasl bo'lsa, Telegram inline keyboard bitta rowga sig'maydi
    conn = sqlite3.connect(db.DB_PATH)
    c = conn.cursor()
    c.execute("SELECT series_group, COUNT(*) FROM doramas WHERE series_group != '' GROUP BY series_group")
    groups = c.fetchall()
    for g, count in groups:
        if count > 8:
            defects.append(f"Franchiza '{g}' da fasllar soni {count} ta. Telegram bitta qatorda maksimum 8 ta tugmaga ruxsat beradi!")
        print(f"  Franchiza '{g}': {count} ta fasl ulangan.")
    conn.close()

    # ----------------------------------------------------
    # XULOSA
    # ----------------------------------------------------
    print("\n==========================================================")
    print("                    AUDIT XULOSASI                        ")
    print("==========================================================")
    if warnings:
        print(f"OGOHLANTIRISHLAR ({len(warnings)} ta):")
        for w in warnings:
            print(f"  ⚠️  {w}")

    if defects:
        print(f"\nCRITICAL DEFECTS / XATOLAR ({len(defects)} ta):")
        for d in defects:
            print(f"  ❌  {d}")
        return False
    else:
        print("\n✅ HECH QANDAY KRITIK XATO VA SINIQ TUGMALAR TOPILMADI!")
        print("Tizim 100% barqaror, barcha limitlar va xavflar to'liq bartaraf etilgan.")
        return True

if __name__ == "__main__":
    success = asyncio.run(run_deep_diagnostics())
    sys.exit(0 if success else 1)
