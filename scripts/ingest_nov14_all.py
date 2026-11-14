import asyncio
from datetime import datetime
import os
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

from aiogram import Bot  # noqa: E402
from aiogram.enums import ParseMode  # noqa: E402
from aiogram.types import (  # noqa: E402
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import config  # noqa: E402
import database as db  # noqa: E402


async def main():
    conn = sqlite3.connect("doramas.db")
    cur = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. Add Code 504: Mening azizim (My Dearest) if not exists
    ex_504 = cur.execute(
        "SELECT id, code, title FROM doramas WHERE code = 504"
    ).fetchone()
    if not ex_504:
        cur.execute(
            """
            INSERT INTO doramas (
                id, code, title, slug, genre, year, description, poster_url,
                total_episodes, views, created_at, status, country, actors, category, aliases, series_group
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                404,
                504,
                "Mening azizim (My Dearest)",
                "mening-azizim",
                "Tarixiy, Romantika, Melodrama, Jangari",
                2023,
                "Sin imperiyasi bosqini (Byonja Xoran) davridagi shafqatsiz urush girdobida qolgan ikki qalbning fojiali, ammo cheksiz muhabbati haqidagi tarixiy epik dorama. Urush qiyinchiliklariga qaramay, Li Jan Xyon va Yu Gil Chon bir-birlariga bo‘lgan sadoqatini saqlab qolishga intiladilar.",
                "posters/code_504.jpg",
                10,
                0,
                now_str,
                "Tugallangan (Completed)",
                "Janubiy Koreya",
                "Namkoong Min (Namgung Min), Ahn Eun-jin (An In Jin), Lee Hak-joo, Lee Da-in",
                "korea",
                "Mening azizim, Mening Azizim, My Dearest, Lovers, 연인, Namkoong Min, Ahn Eun-jin, Mening azizim 1-fasl, Dearest",
                "",
            ),
        )
        print("Created dorama Code 504 (id=404)")

    # 2. Add Code 505: Tutun odam / Bug‘ gaz erkak (The Human Vapor) if not exists
    ex_505 = cur.execute(
        "SELECT id, code, title FROM doramas WHERE code = 505"
    ).fetchone()
    if not ex_505:
        cur.execute(
            """
            INSERT INTO doramas (
                id, code, title, slug, genre, year, description, poster_url,
                total_episodes, views, created_at, status, country, actors, category, aliases, series_group
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                405,
                505,
                "Tutun odam / Bug‘ gaz erkak (The Human Vapor)",
                "tutun-odam-bug-gaz-erkak",
                "Fantastika, Triller, Jinoyat, Detektiv",
                2026,
                "Sirli eksperiment natijasida o‘z tanasini tutun va gazga aylantirish qobiliyatiga ega bo‘lgan 'Bug‘ odam' va uning ortidan tushgan mohir detektiv Okamoto o‘rtasidagi shafqatsiz aqliy va jismoniy kurash haqidagi ilmiy-fantastik triller.",
                "posters/code_505.jpg",
                8,
                0,
                now_str,
                "Tugallangan (Completed)",
                "Yaponiya, Janubiy Koreya",
                "Shun Oguri, Yu Aoi, Uta, Suzu Hirose, Kento Hayashi",
                "korea",
                "Tutun odam, Bug gaz erkak, Bug' gaz erkak, Bug‘ gaz erkak, The Human Vapor, Human Vapor, Gas Ningen, ガス人間, Shun Oguri, Yu Aoi",
                "",
            ),
        )
        print("Created dorama Code 505 (id=405)")

    conn.commit()
    conn.close()

    # Ingest episodes for Code 504 (Mening azizim, eps 1..10)
    eps_504 = [
        (1, 5337, 792482910, "1080p"),
        (2, 5338, 940732812, "1080p"),
        (3, 5339, 771711176, "1080p"),
        (4, 5340, 824834186, "720p"),
        (5, 5341, 813538717, "720p"),
        (6, 5342, 809460103, "720p"),
        (7, 5343, 715785134, "720p"),
        (8, 5344, 625054805, "720p"),
        (9, 5345, 782178769, "720p"),
        (10, 5346, 734510434, "1080p"),
    ]
    for ep_num, msg_id, fsize, qual in eps_504:
        await db.add_episode(
            dorama_id=404,
            episode_number=ep_num,
            channel_message_id=msg_id,
            file_size=fsize,
            quality=qual,
        )
    print("Ingested Code 504 Eps 1..10")

    # Ingest episodes for Code 505 (Tutun odam, eps 1..8)
    eps_505 = [
        (1, 5348, 1231801727, "1080p"),
        (2, 5349, 1617874259, "1080p"),
        (3, 5350, 1377814782, "1080p"),
        (4, 5351, 1315714939, "1080p"),
        (5, 5352, 1519409803, "1080p"),
        (6, 5353, 1388609051, "1080p"),
        (7, 5354, 1218243308, "1080p"),
        (8, 5355, 1755957955, "1080p"),
    ]
    for ep_num, msg_id, fsize, qual in eps_505:
        await db.add_episode(
            dorama_id=405,
            episode_number=ep_num,
            channel_message_id=msg_id,
            file_size=fsize,
            quality=qual,
        )
    print("Ingested Code 505 Eps 1..8")

    # Ingest episode 9 for Code 101 (Doktor X)
    await db.add_episode(
        dorama_id=1,
        episode_number=9,
        channel_message_id=5356,
        file_size=816652032,
        quality="1080p",
    )
    print("Ingested Code 101 Ep 9 -> msg 5356 (1080p)")

    # Restore doramas states:
    conn = sqlite3.connect("doramas.db")
    conn.execute(
        "UPDATE doramas SET total_episodes = 10, status = 'Ongoing' WHERE code = 101"
    )
    conn.execute(
        "UPDATE doramas SET total_episodes = 10, status = 'Tugallangan (Completed)' WHERE code = 504"
    )
    conn.execute(
        "UPDATE doramas SET total_episodes = 8, status = 'Tugallangan (Completed)' WHERE code = 505"
    )
    conn.commit()

    rows = conn.execute(
        "SELECT code, title, total_episodes, status FROM doramas WHERE code IN (101, 504, 505) ORDER BY code"
    ).fetchall()
    print("Updated dorama rows:", rows)
    conn.close()

    # 4. Post Doktor X Ep 9 to Telegram Channel
    bot = Bot(token=config.BOT_TOKEN)
    d101 = await db.get_dorama_by_code(101)
    title = d101["title"]
    code = 101
    ep_num = 9
    available_eps = 9

    caption = (
        "🔔 <b>Yangi qism yuklandi!</b>\n"
        "<i>(Oʻzbek tilida)</i>\n"
        "————————————\n"
        f"« <b>{title}</b> »\n\n"
        f"<b>{ep_num}-qism</b> • ⚡️ 1080p Full HD\n"
        f"🔑 Kodi: <code>{code}</code>\n\n"
        "👇 <b>Tomosha qilish uchun pastdagi tugmani bosing:</b>"
    )

    kb_post = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🎬 1–{available_eps} qismlarni ko'rish",
                    url=f"https://t.me/uzkdrama_app?start={code}",
                )
            ]
        ]
    )

    poster_path = (
        os.path.join(config.BASE_DIR, d101["poster_url"])
        if d101.get("poster_url")
        else ""
    )
    photo_input = (
        FSInputFile(poster_path)
        if (poster_path and os.path.exists(poster_path))
        else None
    )

    print(
        f"Posting Episode {ep_num} to channel {config.REQUIRED_CHANNEL_ID}..."
    )
    if photo_input:
        sent = await bot.send_photo(
            chat_id=config.REQUIRED_CHANNEL_ID,
            photo=photo_input,
            caption=caption,
            reply_markup=kb_post,
            parse_mode=ParseMode.HTML,
        )
    else:
        sent = await bot.send_message(
            chat_id=config.REQUIRED_CHANNEL_ID,
            text=caption,
            reply_markup=kb_post,
            parse_mode=ParseMode.HTML,
        )
    print(f"Channel post sent! Message ID: {sent.message_id}")

    # Notify admin
    admin_msg = (
        f"✅ <b>«{title}» (Kodi: {code})</b> {ep_num}-qismi botga yuklandi va kanalga joylandi!\n\n"
        f"📢 <b>Kanal posti:</b> https://t.me/{config.REQUIRED_CHANNEL_USERNAME}/{sent.message_id}"
    )
    await bot.send_message(
        chat_id=7141955036,
        text=admin_msg,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    print("Admin notified successfully!")
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
