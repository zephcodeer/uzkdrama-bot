import asyncio
import os
import sys
import sqlite3
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, "E:/Agent/Drama Bot")

import config
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.enums import ParseMode

async def main():
    db_path = "E:/Agent/Drama Bot/doramas.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    bot = Bot(token=config.BOT_TOKEN)

    # ==========================================
    # 1. ILK BAHOR / ERTA BAHOR (Code 484) - Ep 24 Final
    # ==========================================
    print("--- 1. Processing Code 484 (Erta bahor / Ilk bahor) ---")
    cur.execute("SELECT id, code, title, poster_url, aliases FROM doramas WHERE code = 484")
    row_484 = cur.fetchone()
    d484_id, c484, t484, p484, a484 = row_484
    
    # Update aliases if needed
    if "Ilk bahor" not in (a484 or ""):
        new_a484 = (a484 or "") + ", Ilk bahor, Ilk Baxor"
        cur.execute("UPDATE doramas SET aliases = ? WHERE id = ?", (new_a484, d484_id))

    cur.execute("""
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
        VALUES (?, 24, 5268, '1080p')
        ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
        channel_message_id = 5268, quality = '1080p'
    """, (d484_id,))
    cur.execute("UPDATE doramas SET total_episodes = 24, status = 'Tugallangan' WHERE id = ?", (d484_id,))
    conn.commit()
    print("Code 484 updated in DB: Ep 24 mapped to 5268 (Final).")

    # Post 484 to Channel
    cap_484 = (
        "🔔 <b>Yangi qism yuklandi!</b>\n"
        "<i>(Oʻzbek tilida)</i>\n"
        "————————————\n"
        f"« <b>{t484}</b> »\n\n"
        "<b>24-qism (Final)</b> • ⚡️ 1080p Full HD\n"
        f"🔑 Kodi: <code>{c484}</code>\n\n"
        "👇 <b>Tomosha qilish uchun pastdagi tugmani bosing:</b>"
    )
    kb_484 = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 1–24 qismlarni ko'rish", url=f"https://t.me/uzkdrama_app?start={c484}")]
    ])
    photo_484 = FSInputFile(os.path.join(config.BASE_DIR, p484)) if p484 and os.path.exists(os.path.join(config.BASE_DIR, p484)) else None
    if photo_484:
        sent_484 = await bot.send_photo(config.REQUIRED_CHANNEL_ID, photo_484, caption=cap_484, reply_markup=kb_484, parse_mode=ParseMode.HTML)
    else:
        sent_484 = await bot.send_message(config.REQUIRED_CHANNEL_ID, text=cap_484, reply_markup=kb_484, parse_mode=ParseMode.HTML)
    print(f"Code 484 channel post sent! Msg ID: {sent_484.message_id}")

    # ==========================================
    # 2. SENDAN O'ZGA BIR MUHABBAT (Code 241) - Ep 8
    # ==========================================
    print("\n--- 2. Processing Code 241 (Sendan o‘zga bir muhabbat) ---")
    cur.execute("SELECT id, code, title, poster_url FROM doramas WHERE code = 241")
    row_241 = cur.fetchone()
    d241_id, c241, t241, p241 = row_241

    cur.execute("""
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
        VALUES (?, 8, 5270, '720p')
        ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
        channel_message_id = 5270, quality = '720p'
    """, (d241_id,))
    cur.execute("SELECT COUNT(*) FROM episodes WHERE dorama_id = ?", (d241_id,))
    avail_241 = cur.fetchone()[0]
    conn.commit()
    print("Code 241 updated in DB: Ep 8 mapped to 5270.")

    # Post 241 to Channel
    cap_241 = (
        "🔔 <b>Yangi qism yuklandi!</b>\n"
        "<i>(Oʻzbek tilida)</i>\n"
        "————————————\n"
        f"« <b>{t241}</b> »\n\n"
        "<b>8-qism</b> • ⚡️ 720p HD\n"
        f"🔑 Kodi: <code>{c241}</code>\n\n"
        "👇 <b>Tomosha qilish uchun pastdagi tugmani bosing:</b>"
    )
    kb_241 = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎬 1–{avail_241} qismlarni ko'rish", url=f"https://t.me/uzkdrama_app?start={c241}")]
    ])
    photo_241 = FSInputFile(os.path.join(config.BASE_DIR, p241)) if p241 and os.path.exists(os.path.join(config.BASE_DIR, p241)) else None
    if photo_241:
        sent_241 = await bot.send_photo(config.REQUIRED_CHANNEL_ID, photo_241, caption=cap_241, reply_markup=kb_241, parse_mode=ParseMode.HTML)
    else:
        sent_241 = await bot.send_message(config.REQUIRED_CHANNEL_ID, text=cap_241, reply_markup=kb_241, parse_mode=ParseMode.HTML)
    print(f"Code 241 channel post sent! Msg ID: {sent_241.message_id}")

    # ==========================================
    # 3. SENGA BO'LGAN MUHABBAT (Code 500) - 1..32 Final
    # ==========================================
    print("\n--- 3. Processing Code 500 (Senga bo'lgan muhabbat) ---")
    cur.execute("SELECT id, code, poster_url, aliases FROM doramas WHERE code = 500")
    row_500 = cur.fetchone()
    d500_id, c500, p500, a500 = row_500
    
    new_title_500 = "Senga bo'lgan muhabbat (Love for You)"
    new_aliases_500 = "Senga bo'lgan muhabbat, Senga bolgan muhabbat, " + (a500 or "")
    
    cur.execute("""
        UPDATE doramas
        SET title = ?, aliases = ?, total_episodes = 32, status = 'Tugallangan'
        WHERE id = ?
    """, (new_title_500, new_aliases_500, d500_id))

    # Re-map episodes 1 to 32 to 5271..5302
    cur.execute("DELETE FROM episodes WHERE dorama_id = ?", (d500_id,))
    for ep in range(1, 33):
        msg_id = 5270 + ep  # 1 -> 5271, 32 -> 5302
        cur.execute("""
            INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
            VALUES (?, ?, ?, '1080p')
        """, (d500_id, ep, msg_id))
    conn.commit()
    print("Code 500 updated in DB: Episodes 1..32 mapped to 5271..5302 (Final).")

    # Post 500 to Channel
    cap_500 = (
        "🌟 <b>PREMYERA: Barcha qismlar yuklandi!</b>\n"
        "<i>(Oʻzbek tilida)</i>\n"
        "————————————\n"
        f"« <b>{new_title_500}</b> »\n\n"
        "<b>1–32-qismlar (Barcha qismlar final)</b> • ⚡️ 1080p Full HD\n"
        f"🔑 Kodi: <code>{c500}</code>\n\n"
        "👇 <b>Tomosha qilish uchun pastdagi tugmani bosing:</b>"
    )
    kb_500 = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 1–32 qismlarni ko'rish", url=f"https://t.me/uzkdrama_app?start={c500}")]
    ])
    photo_500 = FSInputFile(os.path.join(config.BASE_DIR, p500)) if p500 and os.path.exists(os.path.join(config.BASE_DIR, p500)) else None
    if photo_500:
        sent_500 = await bot.send_photo(config.REQUIRED_CHANNEL_ID, photo_500, caption=cap_500, reply_markup=kb_500, parse_mode=ParseMode.HTML)
    else:
        sent_500 = await bot.send_message(config.REQUIRED_CHANNEL_ID, text=cap_500, reply_markup=kb_500, parse_mode=ParseMode.HTML)
    print(f"Code 500 channel post sent! Msg ID: {sent_500.message_id}")

    # ==========================================
    # 4. Notify Admin
    # ==========================================
    admin_summary = (
        "✅ <b>Yangi qismlar muvaffaqiyatli qabul qilindi va kanalga joylandi:</b>\n\n"
        f"1. <b>«{t484}»</b> 24-qism (Final) -> https://t.me/{config.REQUIRED_CHANNEL_USERNAME}/{sent_484.message_id}\n"
        f"2. <b>«{t241}»</b> 8-qism -> https://t.me/{config.REQUIRED_CHANNEL_USERNAME}/{sent_241.message_id}\n"
        f"3. <b>«{new_title_500}»</b> 1–32-qismlar (Final) -> https://t.me/{config.REQUIRED_CHANNEL_USERNAME}/{sent_500.message_id}\n"
    )
    await bot.send_message(7141955036, admin_summary, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    print("Admin notified successfully!")

    conn.close()
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
