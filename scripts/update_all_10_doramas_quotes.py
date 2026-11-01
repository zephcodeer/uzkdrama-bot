import asyncio, sys, os, sqlite3
sys.path.insert(0, r"E:\Agent\Drama Bot")
import config
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

CHANNEL_ID = "@uz_kdramalar"

# Message ID to dorama code mapping from previous session:
POST_MAP = {
    3: 103,  # Alvon yuraklar
    4: 104,  # Biz barchamiz o'likmiz
    5: 106,  # Darbadar ruh
    6: 109,  # Biznes taklifi
    7: 227,  # 12 Farishta
    8: 274,  # Yovuz ruh
    9: 242,  # Yuragimni quvvatla
    10: 101, # Doktor X
    11: 168, # 100 kunlik yolg'on
    12: 480  # Mukammal ish
}

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

    print("Updating all 10 messages with rich Telegram Quotes...")

    for msg_id, code in POST_MAP.items():
        c.execute("""
            SELECT d.code, d.title, d.country, d.year, d.genre, d.status, d.total_episodes, d.description,
                   (SELECT COUNT(*) FROM episodes e WHERE e.dorama_id = d.id) as ep_count
            FROM doramas d WHERE d.code = ?
        """, (code,))
        row = c.fetchone()
        if not row:
            print(f"Skipping {code}, not found")
            continue

        code, title, country, year, genre, status, total_ep, desc, ep_count = row
        caption, btn_text = format_caption(code, title, country, year, genre, status, total_ep, desc, ep_count)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=btn_text, url=f"https://t.me/uzkdrama_app?start={code}")]
        ])

        try:
            await bot.edit_message_caption(
                chat_id=CHANNEL_ID,
                message_id=msg_id,
                caption=caption,
                reply_markup=kb,
                parse_mode=ParseMode.HTML
            )
            print(f"Message {msg_id} [Code {code}] -> SUCCESS")
        except Exception as e:
            print(f"Message {msg_id} [Code {code}] -> ERROR: {e}")

        await asyncio.sleep(1.0)

    # Also update Pinned Message 13 with blockquote
    pinned_quote_text = (
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
        await bot.edit_message_text(
            chat_id=CHANNEL_ID,
            message_id=13,
            text=pinned_quote_text,
            reply_markup=pinned_kb,
            parse_mode=ParseMode.HTML
        )
        print("Message 13 (Pinned Welcome) -> SUCCESS")
    except Exception as e:
        print("Message 13 -> ERROR:", e)

    conn.close()
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
