import asyncio, sys, os, sqlite3
sys.path.insert(0, r"E:\Agent\Drama Bot")
import config
from aiogram import Bot
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

CHANNEL_ID = "@uz_kdramalar"

codes = [
    103, # Alvon yuraklar: Koryo / Oy Oshiqlari
    104, # Biz barchamiz o'likmiz
    106, # Darbadar ruh 1-fasl
    109, # Biznes taklifi
    227, # 12 Farishta
    274, # Yovuz ruh (Revenant)
    242, # Yuragimni quvvatla (Take Charge of My Heart)
    101, # Doktor X , Oq Mafia
    168, # 100 kunlik yolg'on (100 Days of Deception)
    480  # Mukammal ish (Dead-End Job)
]

def get_country_flag(country: str) -> str:
    c = (country or "").lower()
    if "koreya" in c or "korea" in c:
        return "Janubiy Koreya 🇰🇷"
    elif "xitoy" in c or "china" in c:
        return "Xitoy 🇨🇳"
    elif "yapon" in c or "japan" in c:
        return "Yaponiya 🇯🇵"
    elif "tailand" in c or "thai" in c:
        return "Tailand 🇹🇭"
    return f"{country or 'Janubiy Koreya'} 🌏"

def format_caption(code, title, country, year, genre, status, total_ep, desc, ep_count):
    # Parse title & english/sub title
    parts = title.split("(", 1)
    main_title = parts[0].strip()
    sub_title = f"({parts[1].strip()}" if len(parts) > 1 else ""

    raw_status = (status or "").lower()
    is_ongoing = "ongo" in raw_status

    if is_ongoing:
        qism_str = f"{ep_count} qism ({total_ep or ep_count} qismdan / Davom etmoqda) ⏳"
        btn_text = f"🎬 1–{ep_count} qismgacha ko'rish"
    else:
        qism_str = f"{ep_count} qism to'liq (Yakunlangan) ✅"
        btn_text = "🎬 Barcha qismlarni ko'rish"

    flag_country = get_country_flag(country)

    caption = (
        f"<blockquote><b>“{main_title} 🔥”</b>\n"
        f"<i>{sub_title}</i></blockquote>\n\n"
        f"► <b>Tili:</b> Oʻzbek tilida\n"
        f"► <b>Davlati:</b> {flag_country}\n"
        f"► <b>Yili:</b> {year or 2026}\n"
        f"► <b>Qismlar:</b> {qism_str}\n"
        f"► <b>Janri:</b> {genre or 'Dorama'}\n"
        f"► <b>Kodi:</b> <code>{code}</code>\n\n"
    )

    clean_desc = (desc or "").strip()
    if clean_desc:
        caption += (
            f"<blockquote expandable>🎬 <b>Qisqacha syujet:</b>\n"
            f"{clean_desc}</blockquote>\n\n"
        )

    caption += "👇 <b>Tomosha qilish uchun pastdagi tugmani bosing:</b>"
    return caption, btn_text

async def main():
    bot = Bot(config.BOT_TOKEN)
    conn = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
    c = conn.cursor()

    print(f"Publishing 10 flagship doramas from scratch to {CHANNEL_ID}...")

    for code in codes:
        c.execute("""
            SELECT d.code, d.title, d.country, d.year, d.genre, d.poster_url, 
                   d.status, d.total_episodes, d.description,
                   (SELECT COUNT(*) FROM episodes e WHERE e.dorama_id = d.id) as ep_count
            FROM doramas d 
            WHERE d.code = ?
        """, (code,))
        row = c.fetchone()
        if not row:
            print(f"Code {code} not found in DB!")
            continue

        code, title, country, year, genre, poster_rel, status, total_ep, desc, ep_count = row
        caption, btn_text = format_caption(code, title, country, year, genre, status, total_ep, desc, ep_count)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=btn_text, url=f"https://t.me/uzkdrama_app?start={code}")]
        ])

        poster_path = os.path.join(r"E:\Agent\Drama Bot", poster_rel)
        try:
            if os.path.exists(poster_path):
                photo = FSInputFile(poster_path)
                msg = await bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=photo,
                    caption=caption,
                    reply_markup=kb,
                    parse_mode=ParseMode.HTML
                )
            else:
                msg = await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=caption,
                    reply_markup=kb,
                    parse_mode=ParseMode.HTML
                )
            print(f"[{code}] {title} -> SUCCESS! Post ID: {msg.message_id}")
        except Exception as e:
            print(f"[{code}] {title} -> ERROR: {e}")

        await asyncio.sleep(2.0)

    # Pin Welcome Post
    pinned_text = (
        "<blockquote>🌟 <b>UzKdrama — O'zbekistondagi eng sara va qulay dorama kanali!</b></blockquote>\n\n"
        "🎬 Barcha <b>380+ ta</b> koreys, xitoy va yapon seriallarini o'zbek tilida, yuqori sifatda rasmiy botimiz orqali tomosha qiling!\n\n"
        "<blockquote expandable>📌 <b>Qanday tomosha qilinadi?</b>\n"
        "1️⃣ Har bir post ostidagi <b>«Ko'rish»</b> tugmasini bosing.\n"
        "2️⃣ Yoki botga kirib, kino kodini yuboring (masalan: <code>480</code> yoki <code>101</code>).\n"
        "3️⃣ Istalgan dorama nomini yozib qidirishingiz ham mumkin.\n\n"
        "⚡️ Barcha seriallar dublyaj va yuqori HD sifatda joylangan!</blockquote>\n\n"
        "🤖 <b>Rasmiy botimiz:</b> @uzkdrama_app\n"
        "🍿 <i>Barchaga maroqli hordiq tilaymiz!</i>"
    )
    pinned_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍿 Botga kirish (380+ dorama)", url="https://t.me/uzkdrama_app")]
    ])
    try:
        p_msg = await bot.send_message(
            chat_id=CHANNEL_ID,
            text=pinned_text,
            reply_markup=pinned_kb,
            parse_mode=ParseMode.HTML
        )
        await bot.pin_chat_message(chat_id=CHANNEL_ID, message_id=p_msg.message_id)
        print(f"SUCCESS: Pinned Welcome post! ID: {p_msg.message_id}")
    except Exception as e:
        print("Error pinning welcome post:", e)

    conn.close()
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
