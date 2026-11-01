path = r"E:\Agent\Drama Bot\bot.py"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

has_crlf = "\r\n" in content
content_lf = content.replace("\r\n", "\n")

target = """@router.message(Command("update"))
async def cmd_admin_update(message: Message, bot: Bot):
    await handle_admin_git_update(message, bot)"""

admin_cmds = """@router.message(Command("send"))
async def cmd_admin_send_dorama(message: Message, command: CommandObject, bot: Bot):
    \"\"\"
    Faqat admin uchun:
    /send <user_id> <code_yoki_nom>
    Masalan: /send 8890746889 301
    Foydalanuvchiga to'g'ridan-to'g'ri 'Allaqachon mavjud' shabloni va tomosha qilish tugmasini yuboradi.
    \"\"\"
    if message.from_user.id != config.ADMIN_ID and message.from_user.id != 7141955036:
        return
    args = (command.args or "").strip().split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            f"{ce('warning')} <b>Foydalanish:</b> <code>/send &lt;user_id&gt; &lt;kino_kodi&gt;</code>\\n"
            f"Masalan: <code>/send 8890746889 301</code>",
            parse_mode=ParseMode.HTML
        )
        return
    try:
        target_uid = int(args[0])
    except ValueError:
        await message.answer(f"{ce('cross_red')} Noto'g'ri user_id!")
        return

    code_or_query = args[1].strip()
    if code_or_query.isdigit():
        d = await db.get_dorama_by_code(int(code_or_query))
    else:
        results = await db.search_doramas(code_or_query, limit=1)
        d = results[0] if results else None

    if not d:
        await message.answer(f"{ce('cross_red')} Dorama topilmadi: {code_or_query}")
        return

    try:
        await send_dorama_exists_notification(bot, target_uid, sug_id=0, d=d)
        await message.answer(
            f"{ce('check_green')} <b>Foydalanuvchi ({target_uid}) ga [{d['code']}] «{d['title']}» haqida xabar muvaffaqiyatli yetkazildi!</b>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await message.answer(f"{ce('cross_red')} Xatolik: {e}")


@router.message(Command("msg"))
async def cmd_admin_direct_msg(message: Message, command: CommandObject, bot: Bot):
    \"\"\"
    Faqat admin uchun:
    /msg <user_id> <xabar matni>
    Foydalanuvchiga to'g'ridan-to'g'ri ixtiyoriy xabar yuboradi.
    \"\"\"
    if message.from_user.id != config.ADMIN_ID and message.from_user.id != 7141955036:
        return
    args = (command.args or "").strip().split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            f"{ce('warning')} <b>Foydalanish:</b> <code>/msg &lt;user_id&gt; &lt;matn&gt;</code>\\n"
            f"Masalan: <code>/msg 8890746889 Salom, siz so'ragan dorama...</code>",
            parse_mode=ParseMode.HTML
        )
        return
    try:
        target_uid = int(args[0])
    except ValueError:
        await message.answer(f"{ce('cross_red')} Noto'g'ri user_id!")
        return

    text_to_send = args[1].strip()
    try:
        await bot.send_message(
            target_uid,
            f"{ce('broadcast')} <b>Admin xabari:</b>\\n━━━━━━━━━━━━━━━━━━\\n"
            f"<blockquote>{text_to_send}</blockquote>\\n\\n"
            f"<i>Maroqli hordiq tilaymiz! {ce('popcorn')}</i>",
            parse_mode=ParseMode.HTML
        )
        await message.answer(f"{ce('check_green')} <b>Xabar foydalanuvchiga ({target_uid}) muvaffaqiyatli yetkazildi!</b>")
    except Exception as e:
        await message.answer(f"{ce('cross_red')} Xatolik: {e}")


@router.message(Command("update"))
async def cmd_admin_update(message: Message, bot: Bot):
    await handle_admin_git_update(message, bot)"""

if target in content_lf:
    content_lf = content_lf.replace(target, admin_cmds, 1)
    final_content = content_lf.replace("\n", "\r\n") if has_crlf else content_lf
    with open(path, "wb") as f:
        f.write(final_content.encode("utf-8"))
    print("SUCCESS: bot.py patched with /send and /msg commands!")
else:
    print("ERROR: Target not found in bot.py!")
