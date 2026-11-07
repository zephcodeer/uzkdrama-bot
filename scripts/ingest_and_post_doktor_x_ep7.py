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

    cur.execute("SELECT id, code, title, poster_url FROM doramas WHERE code = 101")
    row = cur.fetchone()
    if not row:
        sys.exit("Doktor X (Code 101) bazadan topilmadi!")

    d_id, code, title, poster_rel = row
    ep_num = 7
    msg_id = 5265
    quality = "1080p"

    # 1. Update/Insert episode in doramas.db
    cur.execute("SELECT id FROM episodes WHERE dorama_id = ? AND episode_number = ?", (d_id, ep_num))
    existing = cur.fetchone()
    if existing:
        cur.execute("UPDATE episodes SET channel_message_id = ?, quality = ? WHERE id = ?", (msg_id, quality, existing[0]))
        print(f"Updated ep {ep_num} -> msg {msg_id}")
    else:
        cur.execute("INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality) VALUES (?, ?, ?, ?)", (d_id, ep_num, msg_id, quality))
        print(f"Inserted ep {ep_num} -> msg {msg_id}")

    cur.execute("SELECT COUNT(*) FROM episodes WHERE dorama_id = ?", (d_id,))
    available_eps = cur.fetchone()[0]
    
    cur.execute("UPDATE doramas SET total_episodes = 10, status = 'Ongoing' WHERE id = ?", (d_id,))
    conn.commit()

    cur.execute("SELECT id, code, title, total_episodes, status FROM doramas WHERE id = ?", (d_id,))
    print("Dorama state:", cur.fetchone())
    conn.close()

    # 2. Post to Telegram Channel
    bot = Bot(token=config.BOT_TOKEN)

    caption = (
        "🔔 <b>Yangi qism yuklandi!</b>\n"
        "<i>(Oʻzbek tilida)</i>\n"
        "————————————\n"
        f"« <b>{title}</b> »\n\n"
        f"<b>{ep_num}-qism</b> • ⚡️ 1080p Full HD\n"
        f"🔑 Kodi: <code>{code}</code>\n\n"
        "👇 <b>Tomosha qilish uchun pastdagi tugmani bosing:</b>"
    )

    kb_post = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🎬 1–{available_eps} qismlarni ko'rish",
            url=f"https://t.me/uzkdrama_app?start={code}"
        )]
    ])

    poster_path = os.path.join(config.BASE_DIR, poster_rel) if poster_rel else ""
    photo_input = FSInputFile(poster_path) if (poster_path and os.path.exists(poster_path)) else None

    print(f"Posting Episode {ep_num} to channel {config.REQUIRED_CHANNEL_ID}...")
    if photo_input:
        sent = await bot.send_photo(
            chat_id=config.REQUIRED_CHANNEL_ID,
            photo=photo_input,
            caption=caption,
            reply_markup=kb_post,
            parse_mode=ParseMode.HTML
        )
    else:
        sent = await bot.send_message(
            chat_id=config.REQUIRED_CHANNEL_ID,
            text=caption,
            reply_markup=kb_post,
            parse_mode=ParseMode.HTML
        )
    print(f"Channel post sent! Message ID: {sent.message_id}")

    # 3. Notify Admin directly
    admin_msg = (
        f"✅ <b>«{title}» (Kodi: {code})</b> {ep_num}-qismi botga yuklandi va kanalga joylandi!\n\n"
        f"📢 <b>Kanal posti:</b> https://t.me/{config.REQUIRED_CHANNEL_USERNAME}/{sent.message_id}"
    )
    await bot.send_message(
        chat_id=7141955036,
        text=admin_msg,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )
    print("Admin notified successfully!")
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
