import asyncio
import sys
import os

sys.path.insert(0, 'E:/Agent/Drama Bot')
import config
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.enums import ParseMode

async def post():
    bot = Bot(token=config.BOT_TOKEN)
    poster_path = 'E:/Agent/Drama Bot/posters/code_666.jpg'
    
    caption = (
        '🔥 <b>PREMYERA — YANGI VERTIKAL MINI-DORAMA!</b>\n\n'
        '🎬 <b>Artifaktlar Hukmdori</b>\n'
        '📱 <i>Vertikal Micro-Drama / Duanju</i>\n'
        '🆕 <b>1–10-qismlar to‘liq yuklandi!</b> (⚡️ 720p HD)\n\n'
        '🇺🇿 <b>Tili:</b> O‘zbek tilida (Dublyaj)\n'
        '🌍 <b>Davlati:</b> Xitoy 🇨🇳\n'
        '🗓 <b>Yili:</b> 2026\n'
        '🎞 <b>Qismlar:</b> 1–10-qism to‘liq (Tugallangan ✅)\n'
        '🎭 <b>Janri:</b> Vertikal Micro-Drama, Fantastika, Jangari, Sehr-jodu\n'
        '💎 <b>Kino kodi:</b> <code>666</code>\n\n'
        '📜 <b>Qisqacha syujet:</b>\n'
        'Zamonaviy shahar va qadimiy afsonaviy olam chorrahasida qudratli artifaktlar kuchi uygʻonadi. '
        'Qahramon yashirin artifaktlar sirlarini ochib, beqiyos jangovar qudratga erishadi va dunyo muvozanatini saqlab qolish uchun jangga kirishadi.\n\n'
        '👇 <b>Hoziroq tomosha qiling:</b>'
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 1-qismni tomosha qilish", url='https://t.me/uzkdrama_app?start=666')],
        [InlineKeyboardButton(text="🍿 Barcha qismlar (1–10)", url='https://t.me/uzkdrama_app?start=666')]
    ])
    
    photo = FSInputFile(poster_path)
    msg = await bot.send_photo(
        chat_id=config.REQUIRED_CHANNEL_ID,
        photo=photo,
        caption=caption,
        reply_markup=kb,
        parse_mode=ParseMode.HTML
    )
    print(f"Channel post successful! Msg ID: {msg.message_id}")
    await bot.session.close()

if __name__ == '__main__':
    asyncio.run(post())
