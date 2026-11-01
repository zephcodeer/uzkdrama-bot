import sys
import os
sys.path.insert(0, r"E:\Agent\Drama Bot")
import asyncio
import aiosqlite
import config
from database import init_db, get_dorama_by_code, get_episodes
from emojis import ce
from aiogram import Bot
from aiogram.types import FSInputFile, CallbackQuery
from aiogram.enums import ParseMode
import keyboards as kb

DB_PATH = r"E:\Agent\Drama Bot\doramas.db"

async def ingest():
    await init_db()
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        
        # Check if already exists
        async with db.execute("SELECT id, code, title FROM doramas WHERE title = 'Bechoralar' OR slug = 'bechoralar'") as cur:
            existing = await cur.fetchone()
            
        if existing:
            dorama_id = existing[0]
            code = existing[1]
            print(f"Bechoralar already exists with ID: {dorama_id}, Code: {code}. Updating...")
            await db.execute("""
                UPDATE doramas SET
                    title = 'Bechoralar',
                    slug = 'bechoralar',
                    genre = 'Drama, Oilaviy',
                    year = 2026,
                    description = 'O''zbek milliy seriali "Bechoralar": hayot sinovlari, sabr-bardosh va taqdir yo''llarida uchragan murakkab qismatlar haqidagi ta''sirli drama.',
                    poster_url = 'posters/bechoralar.webp',
                    total_episodes = 42,
                    status = 'Davom etmoqda (42 qism)',
                    country = 'O''zbekiston',
                    actors = 'Mahalliy aktyorlar jamoasi',
                    category = 'foreign',
                    aliases = 'Bechoralar uzbek serial'
                WHERE id = ?
            """, (dorama_id,))
        else:
            # Determine next code and id
            async with db.execute("SELECT MAX(code) FROM doramas") as cur:
                row = await cur.fetchone()
                next_code = (row[0] or 0) + 1
            code = next_code
            print(f"Assigning new dorama Code: {code}")
            
            cursor = await db.execute("""
                INSERT INTO doramas (
                    title, slug, genre, year, description, poster_url,
                    total_episodes, views, code, status, country, actors,
                    category, aliases, series_group
                ) VALUES (
                    'Bechoralar', 'bechoralar', 'Drama, Oilaviy', 2026,
                    'O''zbek milliy seriali "Bechoralar": hayot sinovlari, sabr-bardosh va taqdir yo''llarida uchragan murakkab qismatlar haqidagi ta''sirli drama.',
                    'posters/bechoralar.webp', 42, 0, ?, 'Davom etmoqda (42 qism)',
                    'O''zbekiston', 'Mahalliy aktyorlar jamoasi', 'foreign', 'Bechoralar uzbek serial', ''
                )
            """, (code,))
            dorama_id = cursor.lastrowid
            print(f"Inserted Bechoralar with ID: {dorama_id}")

        # Insert / Update 42 episodes
        # Ep 1 -> msg_id 5064, ..., Ep 42 -> msg_id 5105
        episodes_added = 0
        for ep_num in range(1, 43):
            msg_id = 5063 + ep_num
            await db.execute("""
                INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
                VALUES (?, ?, ?, '720p')
                ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
                    channel_message_id = excluded.channel_message_id,
                    quality = excluded.quality
            """, (dorama_id, ep_num, msg_id))
            episodes_added += 1

        await db.commit()
        print(f"Successfully committed {episodes_added} episodes for Bechoralar (Dorama ID: {dorama_id}, Code: {code})")

    # Verify through database helpers
    d = await get_dorama_by_code(code)
    episodes = await get_episodes(d["id"])
    print(f"Verified from DB: '{d['title']}' (Code {d['code']}), Total episodes in DB: {len(episodes)}")

    # Send preview card to Admin (WITHOUT posting to public channel!)
    print("Sending live test card to Admin (No channel post!)...")
    bot = Bot(token=config.BOT_TOKEN)
    try:
        from bot import show_dorama_detail
        # Let's craft the caption and send directly with photo
        import html
        safe_title = html.escape(str(d.get("title", "")))
        safe_aliases = html.escape(str(d.get("aliases", ""))) if d.get("aliases") else ""
        safe_genre = html.escape(str(d.get("genre", "Drama")))
        safe_country = html.escape(str(d.get("country", "O'zbekiston")))
        safe_actors = html.escape(str(d.get("actors", ""))) if d.get("actors") else ""
        total_ep = d.get("total_episodes") or len(episodes)
        uploaded_ep = len(episodes)
        status_str = f"{ce('green_circle')} Davom etmoqda"
        
        code_badge = f"{ce('code')} <b>Kino kodi:</b> <code>{code}</code>\n"
        aliases_str = f"{ce('scroll')} <b>Boshqa nomlari:</b> {safe_aliases}\n" if safe_aliases else ""
        actors_str = f"{ce('masks')} <b>Bosh rollarda:</b> {safe_actors}\n" if safe_actors else ""
        country_str = f"{ce('globe')} <b>Davlat:</b> {safe_country}\n" if safe_country else ""
        
        raw_desc = (d.get("description") or "").strip()
        if len(raw_desc) > 170:
            raw_desc = raw_desc[:165] + "..."
        safe_desc = html.escape(raw_desc)

        caption = (
            f"{ce('film')} <b>{safe_title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{code_badge}"
            f"{aliases_str}"
            f"{ce('sparkles')} <b>Yili:</b> {d.get('year', 2026)}\n"
            f"{ce('popcorn')} <b>Janr:</b> {safe_genre}\n"
            f"{ce('lightning')} <b>Holati:</b> {status_str}\n"
            f"{ce('tv')} <b>Jami qismlar:</b> {total_ep} ta\n"
            f"{ce('tray')} <b>Yuklangan qismlar:</b> {uploaded_ep} ta\n"
            f"{country_str}"
            f"{actors_str}"
            f"{ce('eyes')} <b>Ko'rishlar:</b> {d.get('views', 0):,} marta\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{ce('memo')} <i>{safe_desc}</i>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{ce('scale')} <i>Eslatma: Seriallar reklamalari tarjimonlarga tegishli bo'lib, bot ma'muriyatiga aloqador emas.</i>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{ce('point_right')} <b>Kerakli qism tugmasini bosib tomosha qiling:</b>"
        )

        bot_info = await bot.get_me()
        markup = kb.dorama_detail_kb(
            dorama_id=d["id"],
            episodes=episodes,
            bot_username=bot_info.username or "",
            page=0,
            last_watched=None,
            bookmarked=False,
            subscribed=False,
            related_seasons=[]
        )

        poster_file = FSInputFile(os.path.join(r"E:\Agent\Drama Bot", d["poster_url"]))
        card_msg = await bot.send_photo(
            chat_id=config.ADMIN_ID,
            photo=poster_file,
            caption=caption,
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )
        print(f"SUCCESS! Admin received Bechoralar live card (Message ID: {card_msg.message_id})")
    except Exception as e:
        print("Error sending test card:", e)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(ingest())
