import sys
import os
sys.path.insert(0, r"E:\Agent\Drama Bot")
import asyncio
import aiosqlite
import html
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
import config
from emojis import ce

DB_PATH = r"E:\Agent\Drama Bot\doramas.db"

async def main():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")

        # 1. Fetch Dorama 241
        async with db.execute("SELECT id, code, title, aliases, total_episodes, poster_url FROM doramas WHERE code = 241;") as cur:
            d = await cur.fetchone()
        
        if not d:
            print("Dorama 241 not found!")
            return
        
        d_id, code, title, aliases, total_episodes, poster_url = d

        # 2. Add aliases if needed
        aliases_list = [a.strip() for a in (aliases or "").split(",") if a.strip()]
        for extra in ["Sendan o'zga muhabbat", "Sendan ozga muhabbat", "A Love Other Than You"]:
            if extra not in aliases_list:
                aliases_list.append(extra)
        new_aliases = ", ".join(aliases_list)

        # 3. Insert Episode 8 (msg_id: 5062) and Episode 9 (msg_id: 5063)
        for ep_num, msg_id in [(8, 5062), (9, 5063)]:
            await db.execute("""
                INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
                VALUES (?, ?, ?, '720p')
                ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
                    channel_message_id = excluded.channel_message_id,
                    quality = excluded.quality
            """, (d_id, ep_num, msg_id))

        # Update status and aliases
        status = "Davom etmoqda (9/14 qism)"
        await db.execute("""
            UPDATE doramas SET
                status = ?,
                aliases = ?
            WHERE id = ?
        """, (status, new_aliases, d_id))

        await db.commit()
        print(f"Committed episodes 8 and 9 for Code {code}")

    # 4. Announce to Channel
    bot = Bot(token=config.BOT_TOKEN)
    channel_id = config.REQUIRED_CHANNEL_ID
    print(f"Posting announcement to channel: {channel_id}")

    caption = (
        f"{ce('bell')} <b>Yangi qismlar yuklandi!</b> {ce('fire')}\n"
        f"<i>(Oʻzbek tilida)</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎬 « <b>{html.escape(title)}</b> »\n\n"
        f"<blockquote><b>1-fasl | 8-9 qismlar</b> {ce('sparkles')}\n"
        f"{ce('code')} Kino kodi: <code>{code}</code></blockquote>\n\n"
        f"{ce('point_down')} <b>Barcha qismlarni tomosha qilish uchun pastdagi tugmani bosing:</b>"
    )

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🎬 1–9 qismlarni tomosha qilish",
            url=f"https://t.me/uzkdrama_app?start={code}"
        )]
    ])

    poster_full = os.path.join(r"E:\Agent\Drama Bot", poster_url)
    try:
        if os.path.exists(poster_full):
            post_msg = await bot.send_photo(
                chat_id=channel_id,
                photo=FSInputFile(poster_full),
                caption=caption,
                reply_markup=markup,
                parse_mode=ParseMode.HTML
            )
            print(f"Channel announcement posted! Message ID: {post_msg.message_id}")
        else:
            post_msg = await bot.send_message(
                chat_id=channel_id,
                text=caption,
                reply_markup=markup,
                parse_mode=ParseMode.HTML
            )
            print(f"Channel announcement posted (text)! Message ID: {post_msg.message_id}")
    except Exception as e:
        print(f"Notice: Channel posting error: {e}")

    # 5. Also send confirmation card to Admin
    try:
        import keyboards as kb
        import database as dbase
        episodes = await dbase.get_episodes(d_id)
        bot_info = await bot.get_me()
        admin_kb = kb.dorama_detail_kb(
            dorama_id=d_id,
            episodes=episodes,
            bot_username=bot_info.username or "uzkdrama_app",
            page=0
        )
        if os.path.exists(poster_full):
            admin_msg = await bot.send_photo(
                chat_id=config.ADMIN_ID,
                photo=FSInputFile(poster_full),
                caption=f"✅ <b>Sendan o'zga bir muhabbat</b> (8-9 qismlar) muvaffaqiyatli qo'shildi!\n\n{caption}",
                reply_markup=admin_kb,
                parse_mode=ParseMode.HTML
            )
            print(f"Admin confirmation sent! Message ID: {admin_msg.message_id}")
    except Exception as e:
        print(f"Notice: Admin test card error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
