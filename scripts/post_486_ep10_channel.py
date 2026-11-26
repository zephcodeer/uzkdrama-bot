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
    poster_path = 'E:/Agent/Drama Bot/posters/code_486.jpg'
    
    caption = (
        '🔥 <b>PREMYERA YAKUNLANDI — KUTILGAN FINAL!</b>\n\n'
        '🎬 <b>Imperatritsaning ikkinchi nikohi (The Remarried Empress)</b>\n'
        '👑 <i>Qayta turmush qurgan qirolicha</i>\n'
        '🆕 <b>10-qism (FINAL) qo‘shildi!</b> (⚡️ 1080p Full HD)\n\n'
        '🇺🇿 <b>Tili:</b> O‘zbek tilida (Professional dublyaj)\n'
        '🌍 <b>Davlati:</b> Janubiy Koreya 🇰🇷\n'
        '🗓 <b>Yili:</b> 2026\n'
        '🎞 <b>Qismlar:</b> 1–10-qism to‘liq (Tugallangan ✅)\n'
        '🎭 <b>Janri:</b> Drama, Tarixiy, Romantika, Fantastika\n'
        '💎 <b>Kino kodi:</b> <code>486</code>\n\n'
        '📜 <b>Qisqacha syujet:</b>\n'
        'Sharqiy imperiya imperatritsasi Navie turmush oʻrtogʻi ajrashishni talab qilganda taslim boʻlish oʻrniga, Gʻarbiy qirollik shahzodasi Heinrey bilan ittifoq tuzadi va oʻz taxtini qaytarib olish uchun ikkinchi nikohga qadam qoʻyadi.\n\n'
        '👇 <b>Hoziroq Full HD sifatda tomosha qiling:</b>'
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 10-qism (Final)ni ko'rish", url='https://t.me/uzkdrama_app?start=486')],
        [InlineKeyboardButton(text="🍿 Barcha qismlar (1–10)", url='https://t.me/uzkdrama_app?start=486')]
    ])
    
    photo = FSInputFile(poster_path)
    msg = await bot.send_photo(
        chat_id=config.REQUIRED_CHANNEL_ID,
        photo=photo,
        caption=caption,
        reply_markup=kb,
        parse_mode=ParseMode.HTML
    )
    print(f'Channel post successful! Msg ID: {msg.message_id}')
    await bot.session.close()

if __name__ == '__main__':
    asyncio.run(post())
