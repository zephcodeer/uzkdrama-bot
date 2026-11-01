import re, sys

bot_path = r"E:\Agent\Drama Bot\bot.py"
with open(bot_path, "rb") as f:
    content = f.read().decode("utf-8")

has_crlf = "\r\n" in content
content_lf = content.replace("\r\n", "\n")

# 1. Update BotStates
old_states = """class BotStates(StatesGroup):

    waiting_for_query = State()

    waiting_for_broadcast = State()

    waiting_for_dorama_suggestion = State()

    waiting_for_suggestion_reply = State()"""

new_states = """class BotStates(StatesGroup):

    waiting_for_query = State()

    waiting_for_broadcast = State()

    waiting_for_dorama_suggestion = State()

    waiting_for_suggestion_reply = State()

    waiting_for_suggestion_exist_code = State()"""

if old_states not in content_lf:
    print("ERROR: old_states not found!")
    sys.exit(1)

content_lf = content_lf.replace(old_states, new_states, 1)

# 2. Update process_dorama_suggestion and suggestion handlers
old_sug_section = """    # 2. Adminga zudlik bilan bildirishnoma yuborish
    admin_targets = list(set([config.ADMIN_ID, 7141955036]))
    admin_notify = (
        f"{ce('bulb')} <b>YANGI DORAMA TAKLIFI #{sug_id}!</b>\\n"
        f"━━━━━━━━━━━━━━━━━━\\n"
        f"{ce('user')} <b>Foydalanuvchi:</b> {u.first_name} (@{u.username or 'username_yoq'})\\n"
        f"{ce('id_badge')} ID: <code>{u.id}</code>\\n\\n"
        f"{ce('memo')} <b>Taklif qilingan dorama:</b>\\n"
        f"<blockquote>{suggestion_text}</blockquote>\\n"
        f"━━━━━━━━━━━━━━━━━━\\n"
        f"Quyidagi tugmalar orqali javob berishingiz mumkin:"
    )
    admin_markup = kb.suggestion_admin_kb(sug_id, u.id)
    for admin_id in admin_targets:
        try:
            await bot.send_message(admin_id, admin_notify, reply_markup=admin_markup, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.warning(f"Admin {admin_id} ga taklif xabarini yuborishda xato: {e}")"""

new_sug_section = """    # 2. Bazadan ushbu dorama bormi-yo'qligini avtomatik tekshirish!
    matches = await db.search_doramas(suggestion_text, limit=1)
    matched_code = matches[0]["code"] if matches else None
    matched_info = ""
    if matches:
        m = matches[0]
        m_eps = await db.get_episodes(m["id"])
        matched_info = f"\\n{ce('search')} <b>Bazada topildi:</b> [{m['code']}] {m['title']} ({len(m_eps)}/{m.get('total_episodes', len(m_eps))} qism)\\n"

    # 3. Adminga zudlik bilan bildirishnoma yuborish
    admin_targets = list(set([config.ADMIN_ID, 7141955036]))
    admin_notify = (
        f"{ce('bulb')} <b>YANGI DORAMA TAKLIFI #{sug_id}!</b>\\n"
        f"━━━━━━━━━━━━━━━━━━\\n"
        f"{ce('user')} <b>Foydalanuvchi:</b> {u.first_name} (@{u.username or 'username_yoq'})\\n"
        f"{ce('id_badge')} ID: <code>{u.id}</code>\\n\\n"
        f"{ce('memo')} <b>Taklif qilingan dorama:</b>\\n"
        f"<blockquote>{suggestion_text}</blockquote>\\n"
        f"{matched_info}"
        f"━━━━━━━━━━━━━━━━━━\\n"
        f"Quyidagi tugmalar orqali javob berishingiz mumkin:"
    )
    admin_markup = kb.suggestion_admin_kb(sug_id, u.id, matched_code=matched_code)
    for admin_id in admin_targets:
        try:
            await bot.send_message(admin_id, admin_notify, reply_markup=admin_markup, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.warning(f"Admin {admin_id} ga taklif xabarini yuborishda xato: {e}")"""

if old_sug_section not in content_lf:
    print("ERROR: old_sug_section not found!")
    sys.exit(1)

content_lf = content_lf.replace(old_sug_section, new_sug_section, 1)

# 3. Add send_dorama_exists_notification and exist callbacks
old_reply_section = """@router.message(BotStates.waiting_for_suggestion_reply)
async def process_suggestion_reply(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id != config.ADMIN_ID and message.from_user.id != 7141955036:
        return
    data = await state.get_data()
    user_id = data.get("reply_user_id")
    sug_id = data.get("reply_sug_id")
    reply_text = message.text or ""
    await state.clear()

    if user_id:
        try:
            await bot.send_message(
                user_id,
                f"{ce('broadcast')} <b>Dorama taklifingiz bo'yicha Admin javobi:</b>\\n"
                f"━━━━━━━━━━━━━━━━━━\\n"
                f"<blockquote>{reply_text}</blockquote>\\n\\n"
                f"<i>Maroqli tomosha tilaymiz! {ce('popcorn')}</i>",
                reply_markup=kb.back_to_menu_kb(),
                parse_mode=ParseMode.HTML
            )
            await message.answer(f"{ce('check_green')} <b>Javob foydalanuvchiga muvaffaqiyatli yetkazildi!</b>")
            if sug_id:
                await db.update_suggestion_status(sug_id, "replied", reply_text)
        except Exception as e:
            await message.answer(f"{ce('cross_red')} Foydalanuvchiga xabar yetkazib bo'lmadi: {e}")"""

new_reply_section = """async def send_dorama_exists_notification(bot: Bot, user_id: int, sug_id: int, d: dict):
    code = d.get("code") or d["id"]
    eps = await db.get_episodes(d["id"])
    raw_status = (d.get("status") or "").strip()
    is_ongoing = "ongo" in raw_status.lower()
    total_ep = d.get("total_episodes") or len(eps)

    if is_ongoing and len(eps) < total_ep:
        ep_info = f"1–{len(eps)} qismlar (davomi chiqishi bilan qo'shib boriladi)"
    elif len(eps) > 1:
        ep_info = f"1–{len(eps)} qismlar (barcha qismlar to'liq yuklangan)"
    else:
        ep_info = "To'liq film/dorama yuklangan"

    try:
        bot_info = await bot.get_me()
        bot_user = bot_info.username or "uzkdrama_app"
    except Exception:
        bot_user = "uzkdrama_app"

    user_msg = (
        f"Assalomu alaykum! <b>«{d['title']}»</b> doramasi allaqachon botimizda mavjud! 🎉\\n\\n"
        f"🔑 <b>Kino kodi:</b> <code>{code}</code>\\n"
        f"🎞 <b>Mavjud:</b> {ep_info}.\\n\\n"
        f"Botga <b>{code}</b> deb yozib yoki qidiruv orqali bemalol tomosha qilishingiz mumkin. Maroqli hordiq tilaymiz! 🎬🍿"
    )

    play_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"{ce('play')} Doramani tomosha qilish",
                url=f"https://t.me/{bot_user}?start={code}"
            )
        ]
    ])

    await bot.send_message(user_id, user_msg, reply_markup=play_kb, parse_mode=ParseMode.HTML)
    if sug_id:
        await db.update_suggestion_status(sug_id, "exists", f"Allaqachon mavjud ({code}-kod)")


@router.callback_query(F.data.startswith("sug_exist:"))
async def cb_sug_exist(call: CallbackQuery, bot: Bot):
    if call.from_user.id != config.ADMIN_ID and call.from_user.id != 7141955036:
        await safe_answer(call, "Siz admin emassiz!", show_alert=True)
        return
    parts = call.data.split(":")
    sug_id, user_id, code = int(parts[1]), int(parts[2]), int(parts[3])
    d = await db.get_dorama_by_code(code)
    if not d:
        await safe_answer(call, "Bazada bu dorama topilmadi!", show_alert=True)
        return
    try:
        await send_dorama_exists_notification(bot, user_id, sug_id, d)
        await safe_answer(call, f"Foydalanuvchiga [{code}] {d['title']} haqida xabar yuborildi!", show_alert=True)
        try:
            await call.message.edit_text(
                call.message.text + f"\\n\\n{ce('check_green')} <b>[ADMIN: ALLAQACHON MAVJUD ({code}-KOD) DEB JAVOB YUBORILDI]</b>",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Foydalanuvchiga mavjudlik xabari yuborishda xato: {e}")
        await safe_answer(call, f"Xatolik: {e}", show_alert=True)


@router.callback_query(F.data.startswith("sug_exist_ask:"))
async def cb_sug_exist_ask(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != config.ADMIN_ID and call.from_user.id != 7141955036:
        await safe_answer(call, "Siz admin emassiz!", show_alert=True)
        return
    parts = call.data.split(":")
    sug_id, user_id = int(parts[1]), int(parts[2])
    await state.set_state(BotStates.waiting_for_suggestion_exist_code)
    await state.update_data(reply_sug_id=sug_id, reply_user_id=user_id)
    await call.message.answer(
        f"{ce('number')} <b>Ushbu dorama botimizda qaysi kod ostida mavjud?</b>\\n\\n"
        f"Kino kodini yozib yuboring (masalan: <code>168</code>):\\n"
        f"<i>Bekor qilish uchun /cancel deb yozing.</i>",
        parse_mode=ParseMode.HTML
    )
    await safe_answer(call)


@router.message(BotStates.waiting_for_suggestion_exist_code)
async def process_suggestion_exist_code(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id != config.ADMIN_ID and message.from_user.id != 7141955036:
        return
    raw = (message.text or "").strip()
    if raw.lower() == "/cancel":
        await state.clear()
        await message.answer(f"{ce('cross_red')} Bekor qilindi.")
        return
    if not raw.isdigit():
        await message.answer(f"{ce('warning')} Iltimos, faqat dorama kodini (raqam) kiriting yoki /cancel qiling:")
        return

    code = int(raw)
    d = await db.get_dorama_by_code(code)
    if not d:
        await message.answer(f"{ce('cross_red')} <b>{code}</b> kodli dorama bazadan topilmadi! Qaytadan kiriting:")
        return

    data = await state.get_data()
    user_id = data.get("reply_user_id")
    sug_id = data.get("reply_sug_id")
    await state.clear()

    if user_id:
        try:
            await send_dorama_exists_notification(bot, user_id, sug_id, d)
            await message.answer(
                f"{ce('check_green')} <b>Foydalanuvchiga [{code}] «{d['title']}» doramasi mavjudligi haqida xabar yetkazildi!</b>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            await message.answer(f"{ce('cross_red')} Xabar yuborishda xatolik: {e}")


@router.message(BotStates.waiting_for_suggestion_reply)
async def process_suggestion_reply(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id != config.ADMIN_ID and message.from_user.id != 7141955036:
        return
    reply_text = (message.text or "").strip()
    if reply_text.lower() == "/cancel":
        await state.clear()
        await message.answer(f"{ce('cross_red')} Javob yozish bekor qilindi.")
        return

    data = await state.get_data()
    user_id = data.get("reply_user_id")
    sug_id = data.get("reply_sug_id")
    await state.clear()

    if user_id:
        # Agar admin faqat raqam (kino kodi) yozsa (masalan: 168):
        if reply_text.isdigit():
            code = int(reply_text)
            d = await db.get_dorama_by_code(code)
            if d:
                try:
                    await send_dorama_exists_notification(bot, user_id, sug_id, d)
                    await message.answer(
                        f"{ce('check_green')} <b>Foydalanuvchiga [{code}] «{d['title']}» doramasi mavjudligi haqida shablon xabar yetkazildi!</b>",
                        parse_mode=ParseMode.HTML
                    )
                    return
                except Exception as e:
                    await message.answer(f"{ce('cross_red')} Xatolik: {e}")
                    return

        try:
            await bot.send_message(
                user_id,
                f"{ce('broadcast')} <b>Dorama taklifingiz bo'yicha Admin javobi:</b>\\n"
                f"━━━━━━━━━━━━━━━━━━\\n"
                f"<blockquote>{reply_text}</blockquote>\\n\\n"
                f"<i>Maroqli tomosha tilaymiz! {ce('popcorn')}</i>",
                reply_markup=kb.back_to_menu_kb(),
                parse_mode=ParseMode.HTML
            )
            await message.answer(f"{ce('check_green')} <b>Javob foydalanuvchiga muvaffaqiyatli yetkazildi!</b>")
            if sug_id:
                await db.update_suggestion_status(sug_id, "replied", reply_text)
        except Exception as e:
            await message.answer(f"{ce('cross_red')} Foydalanuvchiga xabar yetkazib bo'lmadi: {e}")"""

if old_reply_section not in content_lf:
    print("ERROR: old_reply_section not found!")
    sys.exit(1)

content_lf = content_lf.replace(old_reply_section, new_reply_section, 1)

final_content = content_lf.replace("\n", "\r\n") if has_crlf else content_lf

with open(bot_path, "wb") as f:
    f.write(final_content.encode("utf-8"))

print("SUCCESS: bot.py patched with dorama exist feature!")
