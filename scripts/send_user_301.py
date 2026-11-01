import sys, os, asyncio
sys.path.insert(0, r"E:\Agent\Drama Bot")
import config
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def main():
    bot = Bot(token=config.BOT_TOKEN)
    user_id = 8890746889
    code = 301
    
    text = (
        "Assalomu alaykum! Siz taklif qilgan dorama botimizda allaqachon mavjud ekan! 🎉\n\n"
        "🎬 <b>«Mening idolim mening boshlig'im (My Bias, My Boss)»</b>\n"
        "🔑 <b>Kino kodi:</b> <code>301</code>\n"
        "🎞 <b>Mavjud:</b> 1–12 qismlar (barcha qismlar to'liq yuklangan).\n\n"
        "Botga <b>301</b> deb yozib yoki pastdagi tugma orqali bemalol tomosha qilishingiz mumkin. Maroqli hordiq tilaymiz! 🎬🍿"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Doramani tomosha qilish", url=f"https://t.me/uzkdrama_app?start={code}")]
    ])
    
    try:
        msg = await bot.send_message(user_id, text, reply_markup=kb, parse_mode=ParseMode.HTML)
        print("SUCCESS: Message sent to user! Msg ID:", msg.message_id)
    except Exception as e:
        print("ERROR sending message:", e)
    finally:
        await bot.session.close()

asyncio.run(main())
