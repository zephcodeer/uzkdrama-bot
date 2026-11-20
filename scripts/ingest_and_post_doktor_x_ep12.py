import asyncio
import os
import sys
import sqlite3
import html

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

    cur.execute("SELECT id, code, title, genre, poster_url, total_episodes FROM doramas WHERE code = 101")
    row = cur.fetchone()
    if not row:
        sys.exit("Doktor X (Code 101) bazadan topilmadi!")

    d_id, code, title, genre, poster_rel, old_total = row
    ep_num = 12
    msg_id = 5869
    file_size = 885238428
    quality = "1080p"

    # 1. Update/Insert episode in doramas.db
    cur.execute("""
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_size, quality)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
            channel_message_id = excluded.channel_message_id,
            file_size = excluded.file_size,
            quality = excluded.quality
    """, (d_id, ep_num, msg_id, file_size, quality))
    print(f"Ingested episode {ep_num} -> msg_id {msg_id}, size {file_size}, quality {quality}")

    # Count total episodes
    cur.execute("SELECT COUNT(*) FROM episodes WHERE dorama_id = ?", (d_id,))
    available_eps = cur.fetchone()[0]

    cur.execute("UPDATE doramas SET total_episodes = ?, status = 'Ongoing' WHERE id = ?", (available_eps, d_id))
    conn.commit()

    cur.execute("SELECT id, code, title, total_episodes, status FROM doramas WHERE id = ?", (d_id,))
    print("Dorama state updated:", cur.fetchone())
    conn.close()

    # 2. Post to Telegram Channel
    bot = Bot(token=config.BOT_TOKEN)

    safe_title = html.escape(title)
    safe_genre = html.escape(genre or "Drama")

    caption = (
        "🔔 <b>Yangi qism yuklandi!</b>\n"
        "<i>(Oʻzbek tilida)</i>\n"
        "————————————\n"
        f"« <b>{safe_title}</b> »\n\n"
        f"🎬 <b>{ep_num}-qism</b> • ⚡️ 1080p Full HD\n"
        f"🎭 Janr: {safe_genre}\n"
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
    admin_id = 7141955036
    admin_msg = (
        f"✅ <b>«{safe_title}» (Kodi: {code})</b> {ep_num}-qismi botga yuklandi va kanalga joylandi!\n\n"
        f"📢 <b>Kanal posti:</b> https://t.me/{config.REQUIRED_CHANNEL_USERNAME}/{sent.message_id}"
    )
    try:
        await bot.send_message(
            chat_id=admin_id,
            text=admin_msg,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        print("Admin notified successfully!")
    except Exception as e:
        print("Admin notification failed:", e)

    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
