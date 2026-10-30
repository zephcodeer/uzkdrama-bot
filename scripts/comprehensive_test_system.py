import asyncio
import os
import sys
import sqlite3
import re
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import database as db
import keyboards as kb
import config

TEST_TG_ID = 999888777
REF_TG_ID = 888777666

async def run_audit():
    print("==================================================")
    print(" DORAMA BOT TO'LIQ AUDIT VA DIAGNOSTIKA TESTLARI")
    print("==================================================\n")
    
    results = {}
    
    # ----------------------------------------------------
    # TEST 1: MA'LUMOTLAR BAZASI STRUKTURASI VA AJRALISHI
    # ----------------------------------------------------
    print("[TEST 1] Baza arxitekturasi va WAL rejimi tekshiruvi...")
    try:
        await db.init_db()
        
        # Tekshiruv doramas.db
        with sqlite3.connect(db.DB_PATH) as conn:
            c = conn.cursor()
            c.execute("PRAGMA journal_mode;")
            d_wal = c.fetchone()[0]
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            d_tables = [r[0] for r in c.fetchall()]
            c.execute("SELECT COUNT(*) FROM doramas")
            total_doramas = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM episodes")
            total_episodes = c.fetchone()[0]
            
        # Tekshiruv userdata.db
        with sqlite3.connect(db.USER_DB_PATH) as uconn:
            uc = uconn.cursor()
            uc.execute("PRAGMA journal_mode;")
            u_wal = uc.fetchone()[0]
            uc.execute("SELECT name FROM sqlite_master WHERE type='table'")
            u_tables = [r[0] for r in uc.fetchall()]
            
        print(f"  doramas.db: {total_doramas} ta dorama, {total_episodes} ta qism | WAL: {d_wal}")
        print(f"  userdata.db jadvallari: {', '.join(u_tables)} | WAL: {u_wal}")
        
        assert "doramas" in d_tables and "episodes" in d_tables
        assert "users" in u_tables and "bookmarks" in u_tables and "dorama_subscribers" in u_tables
        results["1_database_structure"] = "PASS"
    except Exception as e:
        print(f"  XATO [TEST 1]: {e}")
        results["1_database_structure"] = f"FAIL: {e}"

    # ----------------------------------------------------
    # TEST 2: FOYDALANUVCHI RO'YXATDAN O'TISH VA REFERRAL
    # ----------------------------------------------------
    print("\n[TEST 2] Foydalanuvchi registratsiyasi va referral tizimi...")
    try:
        # Yangi referrer qo'shamiz
        is_new_ref, _ = await db.register_user(REF_TG_ID, "test_ref", "Test Ref", False)
        # Yangi foydalanuvchini referral orqali qo'shamiz
        is_new, ref_id = await db.register_user(TEST_TG_ID, "test_user", "Test User", False, referrer_id=REF_TG_ID)
        
        user = await db.get_user(TEST_TG_ID)
        referrer = await db.get_user(REF_TG_ID)
        
        print(f"  User qo'shildi: tg_id={user['tg_id']}, invited_by={user['invited_by']}")
        print(f"  Referrer referrals_count: {referrer['referrals_count']}")
        
        assert user['tg_id'] == TEST_TG_ID
        assert user['invited_by'] == REF_TG_ID
        assert referrer['referrals_count'] >= 1
        results["2_user_and_referral"] = "PASS"
    except Exception as e:
        print(f"  XATO [TEST 2]: {e}")
        results["2_user_and_referral"] = f"FAIL: {e}"

    # ----------------------------------------------------
    # TEST 3: KO'RISHLAR SONI (KIRICHLAR / VIEWS INCREMENT)
    # ----------------------------------------------------
    print("\n[TEST 3] Ko'rishlar hisoblagichi (Views increment)...")
    try:
        dorama = await db.get_dorama_by_code(101) # Doktor X
        old_views = dorama["views"]
        
        # Ko'rishlar sonini 1 ga oshirish
        await db.increment_views(dorama["id"])
        
        updated_dorama = await db.get_dorama_by_code(101)
        new_views = updated_dorama["views"]
        print(f"  Kino [101] '{dorama['title']}': old_views={old_views} -> new_views={new_views}")
        
        assert new_views == old_views + 1
        
        # Test ma'lumotini qaytarib qo'yamiz (tozalik uchun)
        with sqlite3.connect(db.DB_PATH) as conn:
            conn.execute("UPDATE doramas SET views = ? WHERE id = ?", (old_views, dorama["id"]))
            conn.commit()
            
        results["3_views_increment"] = "PASS"
    except Exception as e:
        print(f"  XATO [TEST 3]: {e}")
        results["3_views_increment"] = f"FAIL: {e}"

    # ----------------------------------------------------
    # TEST 4: TARIX VA SAQLANGANLAR (HISTORY & BOOKMARKS)
    # ----------------------------------------------------
    print("\n[TEST 4] Tarix (History) va Saqlanganlar (Bookmarks)...")
    try:
        # Bookmark qo'shish va tekshirish
        bm_added = await db.toggle_bookmark(TEST_TG_ID, 1)
        is_bm = await db.is_bookmarked(TEST_TG_ID, 1)
        user_bms = await db.get_user_bookmarks(TEST_TG_ID)
        print(f"  Bookmark toggle: {bm_added}, is_bookmarked: {is_bm}, jami saqlanganlar: {len(user_bms)}")
        assert is_bm is True
        assert any(b['id'] == 1 for b in user_bms)
        
        # Tarixga saqlash
        await db.save_last_watched(TEST_TG_ID, 1, 3) # 1-dorama 3-qism
        last_ep = await db.get_last_watched(TEST_TG_ID, 1)
        print(f"  Tarix saqlandi: dorama_id=1, oxirgi qism={last_ep}")
        assert last_ep == 3
        
        # Bookmark olib tashlash
        bm_removed = await db.toggle_bookmark(TEST_TG_ID, 1)
        is_bm_after = await db.is_bookmarked(TEST_TG_ID, 1)
        assert is_bm_after is False
        print(f"  Bookmark olib tashlandi: is_bookmarked={is_bm_after}")
        
        results["4_history_and_bookmarks"] = "PASS"
    except Exception as e:
        print(f"  XATO [TEST 4]: {e}")
        results["4_history_and_bookmarks"] = f"FAIL: {e}"

    # ----------------------------------------------------
    # TEST 5: OBUNA VA NOTIFICATION (BILDIRISHNOMALAR)
    # ----------------------------------------------------
    print("\n[TEST 5] Dorama yangi qismlariga obuna va xabarnomalar...")
    try:
        # Obuna bo'lish
        sub_added = await db.toggle_subscription(TEST_TG_ID, 71) # Daha 17
        is_sub = await db.is_subscribed(TEST_TG_ID, 71)
        subscribers = await db.get_dorama_subscribers(71)
        print(f"  Obuna holati: {is_sub}, Daha 17 obunachilari soni: {len(subscribers)}")
        assert is_sub is True
        assert TEST_TG_ID in subscribers
        
        # Obunani bekor qilish
        unsub = await db.toggle_subscription(TEST_TG_ID, 71)
        is_sub_after = await db.is_subscribed(TEST_TG_ID, 71)
        print(f"  Obuna bekor qilindi, hozirgi holat: {is_sub_after}")
        assert is_sub_after is False
        
        results["5_notifications_and_subs"] = "PASS"
    except Exception as e:
        print(f"  XATO [TEST 5]: {e}")
        results["5_notifications_and_subs"] = f"FAIL: {e}"

    # ----------------------------------------------------
    # TEST 6: AKSIYA REJIMI VA VIP TEKSHIRUVI (PROMO / VIP)
    # ----------------------------------------------------
    print("\n[TEST 6] Aksiya rejimi va VIP cheklovlar...")
    try:
        promo_active = await db.is_promo_free_mode()
        stats = await db.get_stats()
        user_count = stats.get("total_users", 0)
        print(f"  Hozirgi foydalanuvchilar soni: {user_count} ta")
        print(f"  Aksiya rejimi holati: {'YONIQ (Barcha qismlar bepul)' if promo_active else 'O\'CHIQLIK (VIP talab etiladi)'}")
        
        # Test: Oddiy holatda 1-qism ochiq
        unlocked_ep1, reason1, _, _ = await db.is_user_unlocked(TEST_TG_ID, 1)
        print(f"  1-qism ochiqligi (oddiy user): {unlocked_ep1} ({reason1})")
        assert unlocked_ep1 is True
        
        # VIP berish testi
        await db.grant_vip(TEST_TG_ID, days=30)
        user_vip = await db.get_user(TEST_TG_ID)
        assert user_vip['is_vip'] == 1
        print(f"  VIP berildi: is_vip={user_vip['is_vip']}, vip_until={user_vip['vip_until']}")
        
        # Qaytarib oddiy qilish
        with sqlite3.connect(db.USER_DB_PATH) as uconn:
            uconn.execute("UPDATE users SET is_vip = 0, vip_until = NULL WHERE tg_id = ?", (TEST_TG_ID,))
            uconn.commit()
            
        results["6_promo_and_vip"] = "PASS"
    except Exception as e:
        print(f"  XATO [TEST 6]: {e}")
        results["6_promo_and_vip"] = f"FAIL: {e}"

    # ----------------------------------------------------
    # TEST 7: QIDIRUV TIZIMI VA NOISE/STOP-WORDS FILTRI
    # ----------------------------------------------------
    print("\n[TEST 7] Qidiruv mexanizmi va shovqin filtri...")
    try:
        # 1. 'oy oshiqlar' faqat 103 ni chiqarishi kerak (165 chiqmasligi shart)
        res_oy = await db.search_doramas("oy oshiqlar")
        assert len(res_oy) == 1 and res_oy[0]["code"] == 103, f"Xato: {res_oy}"
        print("  'oy oshiqlar' -> Faqat [103] Alvon yuraklar (to'g'ri)")
        
        # 2. 'alvon' faqat 103 ni chiqarishi kerak
        res_alvon = await db.search_doramas("alvon")
        assert any(r["code"] == 103 for r in res_alvon)
        print("  'alvon' -> [103] (to'g'ri)")
        
        # 3. 'obuna boyicha yigit' va 'talab boyicha yigit'
        res_obuna = await db.search_doramas("obuna boyicha yigit")
        assert any(r["code"] == 261 for r in res_obuna)
        res_talab = await db.search_doramas("talab boyicha")
        assert any(r["code"] == 261 for r in res_talab)
        print("  'obuna boyicha yigit' va 'talab boyicha' -> [261] (to'g'ri)")
        
        # 4. 'mening qiroligim' -> [245]
        res_qirol = await db.search_doramas("mening qiroligim")
        assert any(r["code"] == 245 for r in res_qirol)
        print("  'mening qiroligim' -> [245] (to'g'ri)")
        
        # 5. Yangi qo'shilganlar: 'itevon', 'daha 17', 'venzdey'
        res_itevon = await db.search_doramas("itevon")
        assert any(r["code"] == 309 for r in res_itevon)
        res_daha = await db.search_doramas("daha 17")
        assert any(r["code"] == 171 for r in res_daha)
        res_venzdey = await db.search_doramas("venzdey")
        assert any(r["code"] in (319, 320) for r in res_venzdey)
        print("  Yangi doramalar qidiruvi -> [309], [171], [319, 320] (to'g'ri)")
        
        results["7_search_engine"] = "PASS"
    except Exception as e:
        print(f"  XATO [TEST 7]: {e}")
        results["7_search_engine"] = f"FAIL: {e}"

    # ----------------------------------------------------
    # TEST 8: QISMLAR VA XABAR HAVOLALARI (EPISODES DATA)
    # ----------------------------------------------------
    print("\n[TEST 8] Qismlar va Telegram kanal xabar ID lari...")
    try:
        # Daha 17 yangi 43 va 44-qismlarini tekshirish
        ep43 = await db.get_episode(71, 43)
        ep44 = await db.get_episode(71, 44)
        print(f"  Daha 17 ep 43: channel_message_id={ep43['channel_message_id']}")
        print(f"  Daha 17 ep 44: channel_message_id={ep44['channel_message_id']}")
        assert ep43['channel_message_id'] == 3206
        assert ep44['channel_message_id'] == 3207
        
        # Umumiy qismlar soni tekshiruvi (238 ta dorama to'liq yuklangan, 1 ta kutishda)
        with sqlite3.connect(db.DB_PATH) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT d.code, d.title 
                FROM doramas d 
                LEFT JOIN episodes e ON d.id = e.dorama_id 
                WHERE e.id IS NULL
            """)
            empty_doramas = c.fetchall()
            print(f"  Qismi hali yuklanmagan (kutilayotgan) dorama: {empty_doramas}")
            # Faqat 121 (Samoviy ishq) kanalga yuklanmagan
            assert len(empty_doramas) == 1 and empty_doramas[0][0] == 121
            
        results["8_episodes_data"] = "PASS"
    except Exception as e:
        print(f"  XATO [TEST 8]: {e}")
        results["8_episodes_data"] = f"FAIL: {e}"

    # ----------------------------------------------------
    # TEST 9: POSTER FAYLLARI MAVJUDLIGI (LOCAL POSTERS)
    # ----------------------------------------------------
    print("\n[TEST 9] Dorama posterlari va fayllar tekshiruvi...")
    try:
        with sqlite3.connect(db.DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT code, title, poster_url FROM doramas")
            rows = c.fetchall()
            
        missing_posters = []
        for code, title, poster_url in rows:
            if not poster_url:
                missing_posters.append((code, title, "URL bo'sh"))
                continue
            local_path = os.path.join(config.BASE_DIR, poster_url.replace("/", os.sep))
            if not os.path.exists(local_path):
                missing_posters.append((code, title, local_path))
                
        print(f"  Jami tekshirilgan posterlar: {len(rows)} ta | Yetishmayotganlar: {len(missing_posters)}")
        assert len(missing_posters) == 0, f"Yetishmayotgan posterlar: {missing_posters}"
        results["9_posters_integrity"] = "PASS"
    except Exception as e:
        print(f"  XATO [TEST 9]: {e}")
        results["9_posters_integrity"] = f"FAIL: {e}"

    # ----------------------------------------------------
    # TEST 10: TUGMALAR VA CALLBACK DATA CHEKLOVI (<= 64 BYTES)
    # ----------------------------------------------------
    print("\n[TEST 10] Inline tugmalar va Telegram callback_data limiti (<= 64 bytes)...")
    try:
        sample_doramas = await db.get_latest_doramas(limit=5)
        sample_eps = await db.get_episodes(1)
        kbs = [
            kb.main_menu_kb(),
            kb.back_to_menu_kb(),
            kb.vip_plans_kb(),
            kb.vip_payment_method_kb("1_month"),
            kb.admin_panel_kb(),
            kb.doramas_list_kb(sample_doramas, prefix="search", page=0, has_next=True),
            kb.dorama_detail_kb(1, episodes=sample_eps, bot_username="uzkdrama_app"),
            kb.episode_player_kb(1, current_ep=1, has_next=True, bookmarked=False),
            kb.ongoing_doramas_kb(sample_doramas),
            kb.categories_hub_kb()
        ]
        
        long_callbacks = []
        total_buttons = 0
        for ikb in kbs:
            for row in ikb.inline_keyboard:
                for btn in row:
                    total_buttons += 1
                    if btn.callback_data:
                        cb_bytes = len(btn.callback_data.encode("utf-8"))
                        if cb_bytes > 64:
                            long_callbacks.append((btn.text, btn.callback_data, cb_bytes))
                            
        print(f"  Jami tekshirilgan inline tugmalar: {total_buttons} ta")
        print(f"  64 baytdan oshgan xavfli tugmalar: {len(long_callbacks)} ta")
        assert len(long_callbacks) == 0, f"Uzun callback_data topildi: {long_callbacks}"
        results["10_keyboard_callback_bytes"] = "PASS"
    except Exception as e:
        print(f"  XATO [TEST 10]: {e}")
        results["10_keyboard_callback_bytes"] = f"FAIL: {e}"

    # ----------------------------------------------------
    # TEST 11: TELEGRAM BOT VA STORAGE KANAL STATUSI
    # ----------------------------------------------------
    print("\n[TEST 11] Telegram Bot va Storage Kanal tekshiruvi...")
    try:
        from aiogram import Bot
        bot = Bot(token=config.BOT_TOKEN)
        me = await bot.get_me()
        print(f"  Bot ulanishi: @{me.username} (ID: {me.id}, Ism: {me.first_name})")
        
        # Storage kanal ID si to'g'ri o'rnatilganmi
        print(f"  Maxfiy kanal ID: {config.STORAGE_CHANNEL_ID}")
        assert config.STORAGE_CHANNEL_ID != 0
        
        # Test xabari: Daha 17 ep 43 (3206) kanaldan o'qilishi
        msg_copy = await bot.copy_message(
            chat_id=config.ADMIN_ID, 
            from_chat_id=config.STORAGE_CHANNEL_ID, 
            message_id=3206
        )
        print(f"  Kanal xabari [3206] muvaffaqiyatli o'qildi va admin chatga yetkazildi (Copy ID: {msg_copy.message_id})")
        await bot.delete_message(chat_id=config.ADMIN_ID, message_id=msg_copy.message_id)
        print(f"  Sinov xabari admin chatdan toza o'chirildi.")
        
        await bot.session.close()
        results["11_telegram_api_channel"] = "PASS"
    except Exception as e:
        print(f"  XATO [TEST 11]: {e}")
        results["11_telegram_api_channel"] = f"FAIL: {e}"

    # Tozalash: Test foydalanuvchilarini userdata.db dan tozalash
    with sqlite3.connect(db.USER_DB_PATH) as uconn:
        uconn.execute("DELETE FROM users WHERE tg_id IN (?, ?)", (TEST_TG_ID, REF_TG_ID))
        uconn.execute("DELETE FROM bookmarks WHERE user_id = ?", (TEST_TG_ID,))
        uconn.execute("DELETE FROM user_history WHERE user_id = ?", (TEST_TG_ID,))
        uconn.execute("DELETE FROM dorama_subscribers WHERE user_id = ?", (TEST_TG_ID,))
        uconn.commit()

    print("\n==================================================")
    print(" AUDIT NATIJALARI XULOSASI:")
    print("==================================================")
    all_passed = True
    for test_name, status in results.items():
        pass_icon = "[OK]" if "PASS" in status else "[FAILED]"
        if "PASS" not in status:
            all_passed = False
        print(f"  {pass_icon} {test_name}: {status}")
    print("==================================================")
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(run_audit())
    sys.exit(0 if success else 1)
