import sys, os
sys.path.insert(0, r"E:\Agent\Drama Bot")
from aiogram.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.enums import ParseMode

thumb = "https://cdn.jsdelivr.net/gh/zephcodeer/uzkdrama-bot@main/posters/code_480.jpg"
msg_text = (
    f'<a href="{thumb}">&#8203;</a>'
    f"🎬 <b>Mukammal ish (Dead-End Job)</b>\n\n"
    f"🔑 <b>Kino kodi:</b> <code>480</code>\n"
    f"🎞 <b>Qismlar soni:</b> 6/8 qism\n"
    f"📊 <b>Holati:</b> Ongoing (Davom etmoqda)\n"
    f"🎭 <b>Janri:</b> Triller, Detektiv, Sirli\n"
    f"🌍 <b>Davlat:</b> Janubiy Koreya\n\n"
    f"<i>Qarz botqog'iga botgan yigit juda katta haq to'lanadigan vaqtinchalik ishga kirishadi...</i>\n\n"
    f"👇 <b>Tomosha qilish uchun pastdagi tugmani bosing:</b>"
)

kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎬 Tomosha qilish", url="https://t.me/uzkdrama_bot?start=480")],
    [InlineKeyboardButton(text="🔍 Boshqa doramalarni qidirish", switch_inline_query_current_chat="")]
])

item = InlineQueryResultArticle(
    id="dorama_480",
    title="Mukammal ish (Dead-End Job)",
    description="╭────────────\n╰► Kodi: 480 | Qismlar: 6/8 | Ongoing",
    thumbnail_url=thumb,
    thumbnail_width=500,
    thumbnail_height=750,
    input_message_content=InputTextMessageContent(
        message_text=msg_text,
        parse_mode=ParseMode.HTML
    ),
    reply_markup=kb
)

print("SUCCESS: InlineQueryResultArticle validated!")
print("ID:", item.id)
print("Title:", item.title)
