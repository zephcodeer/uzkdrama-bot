import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

import asyncio
import aiosqlite
import html
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
import config
from emojis import ce
import database as db_module
import keyboards as kb

DB_PATH = r"E:\Agent\Drama Bot\doramas.db"

async def main():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        
        # 1. Check max id and code
        async with db.execute("SELECT MAX(id), MAX(code) FROM doramas;") as cur:
            max_id, max_code = await cur.fetchone()
        
        d_id = (max_id or 0) + 1
        code = (max_code or 0) + 1
        
        title = "Ispaniyadagi yomgʻir (The Rain in España)"
        slug = "ispanivadagi-vomgir-the-rain-in-espana"
        genre = "Romantika, Yoshlar, Drama"
        year = 2023
        country = "Filippin"
        actors = "Heaven Peralejo, Marco Gallo, Bea Binene, Gab Lagman"
        desc = "Arxitektura fakulteti talabasi Luna va bo'lajak huquqshunos Kalix o'rtasidagi yillar davomida sinovlardan o'tgan sevgi va ayriliq qissasi."
        poster_rel = "posters/ispanivadagi-vomgir-the-rain-in-espana.jpg"
        aliases = "The Rain in España, The Rain in Espana, Ispaniyadagi yomgir, Ispaniyadagi yomg'ir, Luna, Kalix, Heaven Peralejo, Marco Gallo"
        status = "Tugallangan"
        total_episodes = 10

        # Insert dorama
        await db.execute("""
            INSERT INTO doramas (
                id, code, title, slug, genre, year, description,
                poster_url, total_episodes, views, status, country,
                actors, category, aliases
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 'dorama', ?)
            ON CONFLICT(id) DO UPDATE SET
                code = excluded.code,
                title = excluded.title,
                slug = excluded.slug,
                genre = excluded.genre,
                year = excluded.year,
                description = excluded.description,
                poster_url = excluded.poster_url,
                total_episodes = excluded.total_episodes,
                status = excluded.status,
                country = excluded.country,
                actors = excluded.actors,
                aliases = excluded.aliases
        """, (
            d_id, code, title, slug, genre, year, desc,
            poster_rel, total_episodes, status, country,
            actors, aliases
        ))
        print(f"Inserted Dorama ID={d_id}, Code={code}: {title}")

        # Insert episodes 1 to 10
        storage_msgs = [
            (1, 5109),
            (2, 5110),
            (3, 5111),
            (4, 5112),
            (5, 5113),
            (6, 5114),
            (7, 5115),
            (8, 5116),
            (9, 5117),
            (10, 5118)
        ]
        
        for ep_num, msg_id in storage_msgs:
            await db.execute("""
                INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
                VALUES (?, ?, ?, '720p HD')
                ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
                    channel_message_id = excluded.channel_message_id,
                    quality = excluded.quality
            """, (d_id, ep_num, msg_id))
            
        await db.commit()
        print(f"Committed 10 episodes for Dorama ID {d_id}")

    # 2. Announce to Channel
    bot = Bot(token=config.BOT_TOKEN)
    channel_id = config.REQUIRED_CHANNEL_ID
    print(f"Announcing to channel: {channel_id}")

    caption = (
        f"{ce('bell')} <b>Yangi serial joylandi!</b> {ce('fire')}\n"
        f"<i>(Oʻzbek tilida)</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎬 « <b>{html.escape(title)}</b> »\n\n"
        f"<blockquote><b>1-fasl | 1–10 qismlar (Barcha qismlari)</b> {ce('sparkles')}\n"
        f"{ce('code')} Kino kodi: <code>{code}</code></blockquote>\n\n"
        f"{ce('point_down')} <b>Barcha qismlarni tomosha qilish uchun pastdagi tugmani bosing:</b>"
    )

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎬 1–10 qismlarni tomosha qilish",
            url=f"https://t.me/uzkdrama_app?start={code}"
        )]
    ])

    poster_full = os.path.join(r"E:\Agent\Drama Bot", poster_rel)
    try:
        post_msg = await bot.send_photo(
            chat_id=channel_id,
            photo=FSInputFile(poster_full),
            caption=caption,
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )
        print(f"Channel announcement posted! Message ID: {post_msg.message_id}")
    except Exception as e:
        print(f"Channel posting error: {e}")

    # 3. Send live confirmation card to Admin
    try:
        from bot import show_dorama_detail
        class DummyTarget:
            def __init__(self, admin_id):
                self.from_user = type('User', (), {'id': admin_id})()
                self.admin_id = admin_id
            async def answer(self, text, reply_markup=None, parse_mode=None):
                return await bot.send_message(chat_id=self.admin_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
            async def answer_photo(self, photo, caption=None, reply_markup=None, parse_mode=None):
                return await bot.send_photo(chat_id=self.admin_id, photo=photo, caption=caption, reply_markup=reply_markup, parse_mode=parse_mode)

        dummy = DummyTarget(config.ADMIN_ID)
        await show_dorama_detail(dummy, d_id, bot, user_id=config.ADMIN_ID)
        print(f"Admin confirmation card sent successfully for Code {code}!")
    except Exception as e:
        print(f"Admin confirmation error: {e}")
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
