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
    # 1. BECHORALAR (Code 481) - Episode 50 (msg 5304)
    # =======================================================
    print("--- 1. Processing Bechoralar (Code 481) Ep 50 ---")
    cur.execute("SELECT id, code, title, poster_url FROM doramas WHERE code = 481")
    row_481 = cur.fetchone()
    if not row_481:
        sys.exit("Bechoralar (Code 481) topilmadi!")
    d481_id, c481, t481, p481 = row_481

    # Collision check before insert
    cur.execute("SELECT dorama_id, episode_number FROM episodes WHERE channel_message_id = 5304 AND dorama_id != ?", (d481_id,))
    col = cur.fetchone()
    if col:
        sys.exit(f"Collision detected for 5304: {col}")

    cur.execute("""
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
        VALUES (?, 50, 5304, '720p')
        ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
        channel_message_id = 5304, quality = '720p'
    """, (d481_id,))
    cur.execute("SELECT COUNT(*) FROM episodes WHERE dorama_id = ?", (d481_id,))
    avail_481 = cur.fetchone()[0]
    cur.execute("UPDATE doramas SET total_episodes = ?, status = 'Ongoing' WHERE id = ?", (max(50, avail_481), d481_id))
    conn.commit()
    print(f"Code 481 updated: Ep 50 -> msg 5304 (Total eps in DB: {avail_481})")

    cap_481 = (
        "🔔 <b>Yangi qism yuklandi!</b>\n"
        "<i>(Oʻzbek tilida)</i>\n"
        "————————————\n"
        f"« <b>{html.escape(t481)}</b> »\n\n"
        "<blockquote><b>50-qism</b> • ⚡️ 720p HD\n"
        f"🔑 Kodi: <code>{c481}</code></blockquote>\n\n"
        "👇 <b>Tomosha qilish uchun pastdagi tugmani bosing:</b>"
    )
    kb_481 = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎬 1–{avail_481} qismlarni ko'rish", url=f"https://t.me/uzkdrama_app?start={c481}")]
    ])
    photo_481 = FSInputFile(os.path.join(config.BASE_DIR, p481)) if p481 and os.path.exists(os.path.join(config.BASE_DIR, p481)) else None
    if photo_481:
        sent_481 = await bot.send_photo(config.REQUIRED_CHANNEL_ID, photo_481, caption=cap_481, reply_markup=kb_481, parse_mode=ParseMode.HTML)
    else:
        sent_481 = await bot.send_message(config.REQUIRED_CHANNEL_ID, text=cap_481, reply_markup=kb_481, parse_mode=ParseMode.HTML)
    print(f"Code 481 channel post sent! Msg ID: {sent_481.message_id}")

    # =======================================================
    # 2. MENING QO'SHNIM FRANCHESKO (Code 501) - NEW DORAMA + Ep 1 (msg 5305)
    # =======================================================
    print("\n--- 2. Processing Mening qo'shnim Franchesko (Code 501) Ep 1 ---")
    c501 = 501
    t501 = "Mening qo‘shnim Franchesko (Francesca Next Door)"
    slug501 = "mening-qoshnim-franchesko"
    genre501 = "Fentezi, Komediya, Romantika, Maktab"
    year501 = 2026
    desc501 = (
        "Ruminiyadan Janubiy Koreyadagi oddiy maktabga ko‘chib kelgan qiziqarli vampir qiz Pi Na Yong (Francheska) "
        "insonlar dunyosiga moslashishga urinadi. Uning yon partasida o‘tiradigan tirishqoq sinf sardori Chan U Ju "
        "tasodifan qizning vampir ekanligini bilib qoladi. Sirni saqlash kelishuvi hamda maktabda yashirinib yurgan "
        "yana bir sirli vampirning paydo bo‘lishi ortidan xavfli va kulgili sarguzashtlar, shuningdek ilk muhabbat tuyg‘ulari boshlanadi!"
    )
    poster501 = "posters/code_501.jpg"
    total501 = 4
    status501 = "Ongoing"
    country501 = "Janubiy Koreya"
    actors501 = "Han Soo-ah (Xan Su A), Kim Hyun-jin (Kim Xyon Jin), Lee Seung-gyu (Li Sin Gyu), Shim Hye-jin"
    cat501 = "korea"
    aliases501 = "Mening qoshnim Franchesko, Mening qo'shnim Franchesko, Mening qo‘shnim Franchesko, Francesca Next Door, 옆자리, 프란체스카, Franchesko, Han Soo-ah, Kim Hyun-jin"

    cur.execute("SELECT id FROM doramas WHERE code = ?", (c501,))
    ex_501 = cur.fetchone()
    if ex_501:
        d501_id = ex_501[0]
        cur.execute("""
            UPDATE doramas SET title=?, slug=?, genre=?, year=?, description=?, poster_url=?,
            total_episodes=?, status=?, country=?, actors=?, category=?, aliases=?
            WHERE id=?
        """, (t501, slug501, genre501, year501, desc501, poster501, total501, status501, country501, actors501, cat501, aliases501, d501_id))
    else:
        cur.execute("""
            INSERT INTO doramas (code, title, slug, genre, year, description, poster_url, total_episodes, status, country, actors, category, aliases)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (c501, t501, slug501, genre501, year501, desc501, poster501, total501, status501, country501, actors501, cat501, aliases501))
        d501_id = cur.lastrowid

    # Collision check for 5305
    cur.execute("SELECT dorama_id, episode_number FROM episodes WHERE channel_message_id = 5305 AND dorama_id != ?", (d501_id,))
    col2 = cur.fetchone()
    if col2:
        sys.exit(f"Collision detected for 5305: {col2}")

    cur.execute("""
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
        VALUES (?, 1, 5305, '720p')
        ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
        channel_message_id = 5305, quality = '720p'
    """, (d501_id,))
    conn.commit()
    print(f"Code 501 created/updated (id={d501_id}): Ep 1 -> msg 5305.")

    # Post Luxury Premiere Card for 501 to Channel
    safe_title = html.escape(t501)
    safe_desc = html.escape(desc501)
    card_cap_501 = (
        f"<blockquote>“<b>{safe_title} 🔥</b>”\n"
        f"<i>(Francesca Next Door / 옆자리, 프란체스카)</i></blockquote>\n\n"
        f"► <b>Tili:</b> Oʻzbek tilida\n"
        f"► <b>Davlati:</b> {country501} 🇰🇷\n"
        f"► <b>Yili:</b> {year501}\n"
        f"► <b>Qismlar:</b> 1-qism (Jami 4 qism, Davom etmoqda ⏳)\n"
        f"► <b>Janri:</b> {genre501}\n"
        f"► <b>Kodi:</b> <code>{c501}</code>\n\n"
        f"<blockquote expandable>🎬 <b>Qisqacha syujet:</b>\n"
        f"{safe_desc}</blockquote>\n\n"
        f"👇 <b>Tomosha qilish uchun pastdagi tugmani bosing:</b>"
    )
    kb_501 = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 1-qismni tomosha qilish", url=f"https://t.me/uzkdrama_app?start={c501}")]
    ])
    photo_501 = FSInputFile(os.path.join(config.BASE_DIR, poster501))
    sent_501 = await bot.send_photo(config.REQUIRED_CHANNEL_ID, photo_501, caption=card_cap_501, reply_markup=kb_501, parse_mode=ParseMode.HTML)
    print(f"Code 501 channel premiere post sent! Msg ID: {sent_501.message_id}")

    # =======================================================
    # 3. Notify Admin
    # =======================================================
    admin_msg = (
        "✅ <b>Yangi dorama va qism botga yuklandi hamda kanalga joylandi:</b>\n\n"
        f"1. <b>«{html.escape(t481)}» (Kodi: {c481})</b> 50-qism -> https://t.me/{config.REQUIRED_CHANNEL_USERNAME}/{sent_481.message_id}\n"
        f"2. 🆕 <b>«{safe_title}» (Kodi: {c501})</b> 1-qism (Premyera!) -> https://t.me/{config.REQUIRED_CHANNEL_USERNAME}/{sent_501.message_id}\n"
    )
    await bot.send_message(7141955036, admin_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    print("Admin notified successfully!")

    conn.close()
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
