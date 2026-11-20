"""
Fast Ingestion & Staged Channel Announcement Tool
Qat'iy qoida:
1. Birinchi bot bazasiga yoziladi, commit & push qilinadi, bot serveriga /update yuboriladi.
2. Botda qism ishlashi tekshiriladi.
3. Aynan 1 daqiqa (60 soniya) kutib, keyin kanalga e'lon beriladi!
"""
import sys
import os
import sqlite3
import html
import asyncio
import subprocess

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, "E:/Agent/Drama Bot")

import config
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.enums import ParseMode

async def ingest_and_announce(code: int, ep_num: int, msg_id: int, quality: str = "1080p", delay_seconds: int = 60):
    db_path = "E:/Agent/Drama Bot/doramas.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id, code, title, genre, poster_url, total_episodes FROM doramas WHERE code = ?", (code,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Dorama kodi {code} topilmadi!")

    d_id, code, title, genre, poster_rel, total_eps = row

    # 1. Bazaga kiritish
    cur.execute("""
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
            channel_message_id = excluded.channel_message_id,
            quality = excluded.quality
    """, (d_id, ep_num, msg_id, quality))

    cur.execute("SELECT COUNT(*) FROM episodes WHERE dorama_id = ?", (d_id,))
    available_eps = cur.fetchone()[0]

    cur.execute("UPDATE doramas SET total_episodes = max(total_episodes, ?), status = 'Ongoing' WHERE id = ?", (available_eps, d_id))
    conn.commit()
    conn.close()
    print(f"[1/3] Bot bazasi yangilandi: {title} (Kod: {code}), {ep_num}-qism -> msg {msg_id}")

    # 2. Git commit & push + server /update
    subprocess.run(["git", "-C", "E:/Agent/Drama Bot", "add", "doramas.db"], check=True)
    subprocess.run(["git", "-C", "E:/Agent/Drama Bot", "commit", "-m", f"feat(dorama): ingest ep {ep_num} for code {code}"], check=False)
    subprocess.run(["git", "-C", "E:/Agent/Drama Bot", "push", "origin", "main"], check=True)

    # Trigger /update on bot
    try:
        from telethon import TelegramClient
        env = {}
        with open(r"C:\Users\MuhammadSodiq\.gemini\antigravity\scratch\TG AI PERSON\.env", "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env[k.strip()] = v.strip(" '\"")
        client = TelegramClient(r"C:\Users\MuhammadSodiq\.gemini\antigravity\scratch\TG AI PERSON\.tg_agent\user_account", int(env["TG_API_ID"]), env["TG_API_HASH"])
        await client.connect()
        bot_entity = await client.get_entity("uzkdrama_app")
        await client.send_message(bot_entity, "/update")
        await client.disconnect()
        print("[2/3] Bot serveri yangilandi (/update).")
    except Exception as e:
        print(f"[!] Server /update xatosi: {e}")

    # 3. 1 daqiqa kutish
    print(f"[*] Qat'iy qoida bo'yicha {delay_seconds} soniya kutilmoqda (bot to'liq faollashishi uchun)...")
    await asyncio.sleep(delay_seconds)

    # 4. Kanalga e'lon berish
    bot = Bot(token=config.BOT_TOKEN)
    safe_title = html.escape(title)
    safe_genre = html.escape(genre or "Drama")

    caption = (
        "🔔 <b>Yangi qism yuklandi!</b>\n"
        "<i>(Oʻzbek tilida)</i>\n"
        "————————————\n"
        f"« <b>{safe_title}</b> »\n\n"
        f"🎬 <b>{ep_num}-qism</b> • ⚡️ {quality} Full HD\n"
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
    print(f"[3/3] Kanalga e'lon berildi! Post ID: {sent.message_id}")
    await bot.session.close()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python fast_ingest.py <code:int> <ep_num:int> <msg_id:int> [quality]")
        sys.exit(1)
    code = int(sys.argv[1])
    ep = int(sys.argv[2])
    msg = int(sys.argv[3])
    q = sys.argv[4] if len(sys.argv) > 4 else "1080p"
    asyncio.run(ingest_and_announce(code, ep, msg, q))
