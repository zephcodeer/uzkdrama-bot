import re

bot_path = r"E:\Agent\Drama Bot\bot.py"
with open(bot_path, "rb") as f:
    content = f.read().decode("utf-8")

has_crlf = "\r\n" in content
content_lf = content.replace("\r\n", "\n")

# 1. Update imports
old_import = "from aiogram.types import CallbackQuery, Message, FSInputFile, ErrorEvent, BotCommand, BotCommandScopeChat, MenuButtonCommands, ReplyKeyboardRemove"
new_import = (
    "from aiogram.types import (\n"
    "    CallbackQuery, Message, FSInputFile, ErrorEvent, BotCommand,\n"
    "    BotCommandScopeChat, MenuButtonCommands, ReplyKeyboardRemove,\n"
    "    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,\n"
    "    InlineKeyboardMarkup, InlineKeyboardButton\n"
    ")"
)

if old_import not in content_lf:
    print("ERROR: old_import not found!")
    sys.exit(1)

content_lf = content_lf.replace(old_import, new_import, 1)

# 2. Add inline helper and handler before `async def main():`
target = "async def main():"
if target not in content_lf:
    print("ERROR: target async def main(): not found!")
    sys.exit(1)

inline_code = '''def get_inline_thumb_url(poster_url: str | None) -> str:
    """GitHub / jsDelivr yuqori tezlikdagi CDN orqali Telegram Inline thumbnail URL tayyorlaydi."""
    if not poster_url:
        return "https://cdn.jsdelivr.net/gh/zephcodeer/uzkdrama-bot@main/posters/code_101.jpg"
    p = poster_url.strip()
    if p.startswith("http://") or p.startswith("https://"):
        return p
    clean_p = p.lstrip("/\\\\")
    return f"https://cdn.jsdelivr.net/gh/zephcodeer/uzkdrama-bot@main/{clean_p}"


@router.inline_query()
async def handle_inline_search(inline_query: InlineQuery, bot: Bot):
    """
    Telegram Inline Mode Handler:
    Foydalanuvchi ixtiyoriy chatda @uzkdrama_app <nom yoki kod> deb yozganda
    barcha 380+ ta doramani posteri, qismlar soni va kodi bilan interaktiv chiqaradi.
    """
    raw_query = (inline_query.query or "").strip()

    try:
        if raw_query:
            if len(raw_query) == 1 and not raw_query.isdigit():
                import aiosqlite
                async with aiosqlite.connect(db.DB_PATH) as conn:
                    conn.row_factory = aiosqlite.Row
                    async with conn.execute(
                        "SELECT * FROM doramas WHERE title LIKE ? ORDER BY views DESC LIMIT 30",
                        (f"{raw_query}%",)
                    ) as cur:
                        doramas = [dict(r) for r in await cur.fetchall()]
            else:
                doramas = await db.search_doramas(raw_query, limit=30)
        else:
            doramas = await db.get_latest_doramas(limit=30)
    except Exception as e:
        logger.error(f"Inline qidiruvda xatolik: {e}")
        doramas = []

    if not doramas:
        await inline_query.answer(
            results=[],
            cache_time=5,
            is_personal=True,
            switch_pm_text="🔍 Hech narsa topilmadi. Bot orqali qidiring",
            switch_pm_parameter="search_empty"
        )
        return

    try:
        bot_info = await bot.get_me()
        bot_username = bot_info.username or "uzkdrama_app"
    except Exception:
        bot_username = "uzkdrama_app"

    articles = []
    for d in doramas:
        code = d.get("code") or d["id"]
        title = d.get("title", "Nomsiz dorama")
        total_ep = d.get("total_episodes") or 1
        raw_status = (d.get("status") or "Ongoing").strip()
        is_ongoing = "ongo" in raw_status.lower()
        status_text = "Ongoing (Davom etmoqda)" if is_ongoing else "Tugallangan"
        status_badge = ce('green_circle') if is_ongoing else ce('red_circle')
        genre = d.get("genre") or "Dorama"
        country = d.get("country") or "Janubiy Koreya"
        year = d.get("year") or 2026
        thumb = get_inline_thumb_url(d.get("poster_url"))
        raw_desc = (d.get("description") or "").strip()
        short_desc = (raw_desc[:110] + "...") if len(raw_desc) > 113 else raw_desc

        # Skrinshotdagi estetik format:
        # ╭────────────
        # ╰► Qismlar soni: 8ta...
        desc_line = f"╭────────────\\n╰► Qismlar soni: {total_ep} ta ({status_text})"

        msg_text = (
            f'<a href="{thumb}">&#8203;</a>'
            f"🎬 <b>{title}</b>\\n\\n"
            f"🔑 <b>Kino kodi:</b> <code>{code}</code>\\n"
            f"🎞 <b>Qismlar soni:</b> {total_ep} qism\\n"
            f"📊 <b>Holati:</b> {status_badge} {status_text}\\n"
            f"🎭 <b>Janri:</b> {genre}\\n"
            f"🌍 <b>Davlat:</b> {country} ({year})\\n"
        )
        if short_desc:
            msg_text += f"\\n<i>{short_desc}</i>\\n"
        msg_text += f"\\n👇 <b>Tomosha qilish uchun pastdagi tugmani bosing:</b>"

        item_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{ce('play')} Doramani tomosha qilish",
                    url=f"https://t.me/{bot_username}?start={code}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔍 Boshqa dorama qidirish",
                    switch_inline_query_current_chat=""
                )
            ]
        ])

        articles.append(
            InlineQueryResultArticle(
                id=f"dorama_{code}",
                title=title,
                description=desc_line,
                thumbnail_url=thumb,
                thumbnail_width=500,
                thumbnail_height=750,
                input_message_content=InputTextMessageContent(
                    message_text=msg_text,
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=item_kb
            )
        )

    await inline_query.answer(
        results=articles,
        cache_time=10,
        is_personal=True,
        switch_pm_text="🎬 Bot menyusiga o'tish",
        switch_pm_parameter="from_inline"
    )


'''

content_lf = content_lf.replace(target, inline_code + target, 1)

final_content = content_lf.replace("\n", "\r\n") if has_crlf else content_lf

with open(bot_path, "wb") as f:
    f.write(final_content.encode("utf-8"))

print("SUCCESS: bot.py patched with Inline Query handler!")
