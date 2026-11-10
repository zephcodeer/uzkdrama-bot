import asyncio
import html
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

    # =======================================================
    # 1. G'ALATI HISOBLAGICH 2 (Code 499) - Episode 3 (msg 5306)
    # =======================================================
    print("--- 1. Processing G'alati hisoblagich 2 (Code 499) Ep 3 ---")
    cur.execute("SELECT id, code, title, poster_url FROM doramas WHERE code = 499")
    row_499 = cur.fetchone()
    if not row_499:
        sys.exit("Code 499 topilmadi!")
    d499_id, c499, t499, p499 = row_499

    cur.execute("SELECT dorama_id, episode_number FROM episodes WHERE channel_message_id = 5306 AND dorama_id != ?", (d499_id,))
    col = cur.fetchone()
    if col:
        sys.exit(f"Collision detected for 5306: {col}")

    cur.execute("""
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
        VALUES (?, 3, 5306, '1080p')
        ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
        channel_message_id = 5306, quality = '1080p'
    """, (d499_id,))
    cur.execute("SELECT COUNT(*) FROM episodes WHERE dorama_id = ?", (d499_id,))
    avail_499 = cur.fetchone()[0]
    conn.commit()
    print(f"Code 499 updated: Ep 3 -> msg 5306 (Total eps in DB: {avail_499})")

    cap_499 = (
        "🔔 <b>Yangi qism yuklandi!</b>\n"
        "<i>(Oʻzbek tilida)</i>\n"
        "————————————\n"
        f"« <b>{html.escape(t499)}</b> »\n\n"
        "<blockquote><b>3-qism</b> • ⚡️ 1080p Full HD\n"
        f"🔑 Kodi: <code>{c499}</code></blockquote>\n\n"
        "👇 <b>Tomosha qilish uchun pastdagi tugmani bosing:</b>"
    )
    kb_499 = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎬 1–{avail_499} qismlarni ko'rish", url=f"https://t.me/uzkdrama_app?start={c499}")]
    ])
    photo_499 = FSInputFile(os.path.join(config.BASE_DIR, p499)) if p499 and os.path.exists(os.path.join(config.BASE_DIR, p499)) else None
    if photo_499:
        sent_499 = await bot.send_photo(config.REQUIRED_CHANNEL_ID, photo_499, caption=cap_499, reply_markup=kb_499, parse_mode=ParseMode.HTML)
    else:
        sent_499 = await bot.send_message(config.REQUIRED_CHANNEL_ID, text=cap_499, reply_markup=kb_499, parse_mode=ParseMode.HTML)
    print(f"Code 499 channel post sent! Msg ID: {sent_499.message_id}")

    # =======================================================
    # 2. DOKTOR X , OQ MAFIA (Code 101) - Episode 8 (msg 5307)
    # =======================================================
    print("\n--- 2. Processing Doktor X (Code 101) Ep 8 ---")
    cur.execute("SELECT id, code, title, poster_url FROM doramas WHERE code = 101")
    row_101 = cur.fetchone()
    if not row_101:
        sys.exit("Code 101 topilmadi!")
    d101_id, c101, t101, p101 = row_101

    cur.execute("SELECT dorama_id, episode_number FROM episodes WHERE channel_message_id = 5307 AND dorama_id != ?", (d101_id,))
    col2 = cur.fetchone()
    if col2:
        sys.exit(f"Collision detected for 5307: {col2}")

    cur.execute("""
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
        VALUES (?, 8, 5307, '1080p')
        ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
        channel_message_id = 5307, quality = '1080p'
    """, (d101_id,))
    cur.execute("SELECT COUNT(*) FROM episodes WHERE dorama_id = ?", (d101_id,))
    avail_101 = cur.fetchone()[0]
    conn.commit()
    print(f"Code 101 updated: Ep 8 -> msg 5307 (Total eps in DB: {avail_101})")

    cap_101 = (
        "🔔 <b>Yangi qism yuklandi!</b>\n"
        "<i>(Oʻzbek tilida)</i>\n"
        "————————————\n"
        f"« <b>{html.escape(t101)}</b> »\n\n"
        "<blockquote><b>8-qism</b> • ⚡️ 1080p Full HD\n"
        f"🔑 Kodi: <code>{c101}</code></blockquote>\n\n"
        "👇 <b>Tomosha qilish uchun pastdagi tugmani bosing:</b>"
    )
    kb_101 = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎬 1–{avail_101} qismlarni ko'rish", url=f"https://t.me/uzkdrama_app?start={c101}")]
    ])
    photo_101 = FSInputFile(os.path.join(config.BASE_DIR, p101)) if p101 and os.path.exists(os.path.join(config.BASE_DIR, p101)) else None
    if photo_101:
        sent_101 = await bot.send_photo(config.REQUIRED_CHANNEL_ID, photo_101, caption=cap_101, reply_markup=kb_101, parse_mode=ParseMode.HTML)
    else:
        sent_101 = await bot.send_message(config.REQUIRED_CHANNEL_ID, text=cap_101, reply_markup=kb_101, parse_mode=ParseMode.HTML)
    print(f"Code 101 channel post sent! Msg ID: {sent_101.message_id}")

    # =======================================================
    # 3. Notify Admin
    # =======================================================
    admin_msg = (
        "✅ <b>Yangi qismlar botga yuklandi va kanalga joylandi:</b>\n\n"
        f"1. <b>«{html.escape(t499)}» (Kodi: {c499})</b> 3-qism -> https://t.me/{config.REQUIRED_CHANNEL_USERNAME}/{sent_499.message_id}\n"
        f"2. <b>«{html.escape(t101)}» (Kodi: {c101})</b> 8-qism -> https://t.me/{config.REQUIRED_CHANNEL_USERNAME}/{sent_101.message_id}\n"
    )
    await bot.send_message(7141955036, admin_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    print("Admin notified successfully!")

    conn.close()
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
