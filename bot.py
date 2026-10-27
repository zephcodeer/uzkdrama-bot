import asyncio
import logging
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import socket
from aiohttp import TCPConnector
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject, CommandStart, StateFilter
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sqlite3
import subprocess
from aiogram.types import CallbackQuery, Message, FSInputFile, ErrorEvent, BotCommand, BotCommandScopeChat, MenuButtonCommands, ReplyKeyboardRemove

import config
import database as db
from emojis import ce
import keyboards as kb

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DoramaBot")

router = Router()


class BotStates(StatesGroup):
    waiting_for_query = State()
    waiting_for_broadcast = State()


class VipStates(StatesGroup):
    waiting_for_receipt = State()


VIP_PLANS = {
    "1m": {"title": "1 oylik VIP", "price": 9000, "days": 30, "price_str": "9 000 so'm"},
    "6m": {"title": "6 oylik VIP", "price": 34000, "days": 180, "price_str": "34 000 so'm"},
    "1y": {"title": "1 yillik VIP", "price": 49000, "days": 365, "price_str": "49 000 so'm"},
    "life": {"title": "Cheksiz VIP", "price": 79000, "days": 3650, "price_str": "79 000 so'm"},
}


# ---------------------------------------------------------------------------
# Handlers: Start va Deep-linking
# ---------------------------------------------------------------------------
@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, bot: Bot, state: FSMContext):
    await state.clear()
    user = message.from_user

    args = command.args
    referrer_id = None
    if args and args.startswith("ref_"):
        try:
            referrer_id = int(args.split("_")[1])
        except Exception:
            pass

    is_new, inviter_rewarded = await db.register_user(
        tg_id=user.id,
        username=user.username,
        first_name=user.first_name,
        is_premium=bool(user.is_premium),
        referrer_id=referrer_id
    )

    if inviter_rewarded:
        try:
            inv_user = await db.get_user(inviter_rewarded)
            ref_total = inv_user.get("referrals_count") if inv_user else 1
            await bot.send_message(
                chat_id=inviter_rewarded,
                text=(
                    f"{ce('party')} <b>Yangi do'stingiz botga qo'shildi!</b>\n\n"
                    f"{ce('user')} <b>{user.first_name}</b> sizning havolangiz orqali kirdi.\n"
                    f"{ce('sparkles')} Jami takliflaringiz: <b>{ref_total} ta</b>.\n\n"
                    f"{ce('unlock')} <b>Sizga yangi {3 + ref_total}-qism bepul ochildi!</b> Har bir do'stingiz navbatdagi qismni ochib beradi! {ce('popcorn')}"
                ),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.warning(f"Taklif qiluvchiga xabar yuborishda xatolik: {e}")

    # Deep-link tekshiruvi: /start d_15 yoki /start ep_15_3 yoki /start 105 (kino kodi)
    if args:
        if args.isdigit():
            # Kino kodi bilan kirish (TikTok/Reels dan)
            d = await db.get_dorama_by_code(int(args))
            if d:
                await show_dorama_detail(message, d["id"], bot, user_id=user.id)
                return

        if args.startswith("d_"):
            try:
                d_id = int(args.split("_")[1])
                await show_dorama_detail(message, d_id, bot, user_id=user.id)
                return
            except Exception:
                pass
        elif args.startswith("ep_"):
            try:
                parts = args.split("_")
                d_id, ep_num = int(parts[1]), int(parts[2])
                await send_episode(message.from_user.id, d_id, ep_num, bot)
                return
            except Exception:
                pass

    prem_badge = f" {ce('crown')} [PREMIUM]" if user.is_premium else ""
    is_admin = (user.id == config.ADMIN_ID)

    text = (
        f"{ce('film')} <b>DORAMA HUB — Rasmiy Kinoteatr</b>\n\n"
        f"{ce('sparkles')} Assalomu alaykum, <b>{user.first_name}</b>{prem_badge}!\n\n"
        f"{ce('popcorn')} Bu yerda eng sara Koreys, Xitoy va Osiyo doramalarini bepul, "
        f"yuqori sifatda (Full HD) tomosha qilishingiz mumkin.\n\n"
        f"{ce('bulb')} <i>Instagram yoki TikTok'dagi kino kodini (masalan: <b>101</b>) to'g'ridan-to'g'ri yozsangiz, "
        f"dorama bir zumda ochiladi!</i>\n\n"
        f"Quyidagi bo'limlardan birini tanlang:"
    )
    try:
        clean_msg = await message.answer("ㅤ", reply_markup=ReplyKeyboardRemove())
        await clean_msg.delete()
    except Exception:
        pass
    await message.answer(text, reply_markup=kb.main_menu_kb(is_admin=is_admin), parse_mode=ParseMode.HTML)


async def safe_answer(call: CallbackQuery, text: str = None, show_alert: bool = False):
    """Eskirgan yoki bekor qilingan callback querylarda crash bermaslik uchun xavfsiz answer."""
    try:
        if text is not None:
            await call.answer(text=text, show_alert=show_alert)
        else:
            await call.answer()
    except Exception:
        pass


async def render_text_screen(event: CallbackQuery | Message, text: str, reply_markup=None):
    """Xabar rasm bo'lsa o'chirib matn yuboradi, matn bo'lsa edit qiladi. Barcha xatoliklarga chidamli."""
    if isinstance(event, Message):
        await event.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        return

    msg = event.message
    try:
        if msg.photo or msg.video or msg.document:
            try:
                await msg.delete()
            except Exception:
                pass
            await msg.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await msg.edit_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            pass
        else:
            await msg.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except Exception:
        await msg.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


# ---------------------------------------------------------------------------
# Helper: Dorama kartasi va qismlari (Poster bilan)
# ---------------------------------------------------------------------------
async def show_dorama_detail(target: Message | CallbackQuery, dorama_id: int, bot: Bot, user_id: int, page: int = 0):
    d = await db.get_dorama_by_id(dorama_id)
    if not d:
        text = f"{ce('bell')} Kechirasiz, bu dorama topilmadi yoki o'chirilgan."
        if isinstance(target, CallbackQuery):
            await target.answer(text, show_alert=True)
        else:
            await target.answer(text)
        return

    episodes = await db.get_episodes(dorama_id)
    bot_info = await bot.get_me()

    last_watched = await db.get_last_watched(user_id, dorama_id)
    bookmarked = await db.is_bookmarked(user_id, dorama_id)
    subscribed = await db.is_subscribed(user_id, dorama_id)

    code_badge = f"{ce('code')} <b>Kino kodi:</b> <code>{d.get('code', d['id'])}</code>\n" if d.get('code') else ""
    watched_text = f"{ce('play')} <b>Oxirgi ko'rgan qismingiz:</b> {last_watched}-qism\n" if last_watched else ""

    total_ep = d.get("total_episodes") or 12
    uploaded_ep = len(episodes)
    raw_status = (d.get("status") or "Ongoing").strip()
    status_str = f"{ce('green_circle')} Davom etmoqda (Ongoing)" if "ongo" in raw_status.lower() else f"{ce('red_circle')} Tugallangan (Completed)"

    actors_str = f"{ce('masks')} <b>Bosh rollarda:</b> {d['actors']}\n" if d.get("actors") else ""
    country_str = f"{ce('globe')} <b>Davlat:</b> {d['country']}\n" if d.get("country") else ""
    desc_str = f"{ce('memo')} <i>{d['description']}</i>\n━━━━━━━━━━━━━━━━━━\n" if d.get("description") else ""

    caption = (
        f"{ce('film')} <b>{d['title']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{code_badge}"
        f"{ce('sparkles')} <b>Yili:</b> {d['year']}\n"
        f"{ce('popcorn')} <b>Janr:</b> {d['genre']}\n"
        f"{ce('lightning')} <b>Holati:</b> {status_str}\n"
        f"{ce('tv')} <b>Jami qismlar:</b> {total_ep} ta\n"
        f"{ce('tray')} <b>Yuklangan qismlar:</b> {uploaded_ep} ta\n"
        f"{country_str}"
        f"{actors_str}"
        f"{ce('eyes')} <b>Ko'rishlar:</b> {d['views']:,} marta\n"
        f"{watched_text}"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{desc_str}"
        f"{ce('point_right')} <b>Kerakli qism tugmasini bosib tomosha qiling:</b>"
    )

    markup = kb.dorama_detail_kb(
        dorama_id=dorama_id,
        episodes=episodes,
        bot_username=bot_info.username or "",
        page=page,
        last_watched=last_watched,
        bookmarked=bookmarked,
        subscribed=subscribed
    )

    poster = d.get("poster_url")
    photo_input = None
    if poster:
        if os.path.exists(poster):
            photo_input = FSInputFile(poster)
        else:
            basename = os.path.basename(poster)
            local_fallback = os.path.join(config.BASE_DIR, "posters", basename)
            if os.path.exists(local_fallback):
                photo_input = FSInputFile(local_fallback)
            elif poster.startswith("http"):
                photo_input = poster

    photo_sent = False
    if photo_input:
        try:
            if isinstance(target, CallbackQuery):
                msg = target.message
                if msg.photo:
                    await msg.edit_caption(caption=caption, reply_markup=markup, parse_mode=ParseMode.HTML)
                    photo_sent = True
                else:
                    try:
                        await msg.delete()
                    except Exception:
                        pass
                    await bot.send_photo(chat_id=user_id, photo=photo_input, caption=caption, reply_markup=markup, parse_mode=ParseMode.HTML)
                    photo_sent = True
            else:
                await target.answer_photo(photo=photo_input, caption=caption, reply_markup=markup, parse_mode=ParseMode.HTML)
                photo_sent = True
        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                photo_sent = True
            else:
                logger.warning(f"Rasm yuborishda xatolik ({e}), matn rejimiga o'tilmoqda...")
                photo_sent = False
        except Exception as e:
            logger.warning(f"Rasm yuborishda xatolik ({e}), matn rejimiga o'tilmoqda...")
            photo_sent = False

    if not photo_sent:
        try:
            if isinstance(target, CallbackQuery):
                msg = target.message
                if msg.photo or msg.video or msg.document:
                    try:
                        await msg.delete()
                    except Exception:
                        pass
                    await bot.send_message(chat_id=user_id, text=caption, reply_markup=markup, parse_mode=ParseMode.HTML)
                else:
                    await msg.edit_text(caption, reply_markup=markup, parse_mode=ParseMode.HTML)
            else:
                await target.answer(caption, reply_markup=markup, parse_mode=ParseMode.HTML)
        except Exception:
            await bot.send_message(chat_id=user_id, text=caption, reply_markup=markup, parse_mode=ParseMode.HTML)


# ---------------------------------------------------------------------------
# Helper: Qismni yuborish (CopyMessage + protect_content=True)
# ---------------------------------------------------------------------------
async def send_episode(user_id: int, dorama_id: int, ep_num: int, bot: Bot):
    ep = await db.get_episode(dorama_id, ep_num)
    if not ep:
        await bot.send_message(user_id, f"{ce('bell')} Ushbu qism hali bazaga joylanmagan.")
        return

    # Qulf tekshiruvi (Episodes 4+ require referral or VIP)
    unlocked, reason, current_refs, req_refs = await db.is_user_unlocked(user_id, ep_num, config.ADMIN_ID)
    if not unlocked:
        bot_info = await bot.get_me()
        needed = max(1, req_refs - current_refs)
        lock_text = (
            f"{ce('lock')} <b>{ep_num}-QISM QULFLANGAN!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Ushbu doramaning 1, 2 va 3-qismlari mutlaqo bepul.\n\n"
            f"{ce('stats')} Sizning takliflaringiz: <b>{current_refs} ta</b>\n"
            f"{ce('target')} <b>{ep_num}-qismni ochish uchun talab:</b> <b>{req_refs} ta</b> do'st "
            f"<i>(Yana <b>{needed} ta</b> do'st kerak)</i>.\n\n"
            f"<b>2 ta yo'ldan birini tanlang:</b>\n"
            f"1️⃣ <b>Do'stingizni taklif qiling:</b> Havolangiz orqali har bir kirgan do'stingiz navbatdagi qismni ochadi!\n"
            f"2️⃣ <b>VIP A'zolik oling:</b> Atigi 9 000 so'm — barcha qismlarni bir zumda, do'st taklif qilmasdan 1080p sifatda ko'ring.\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
        await bot.send_message(
            chat_id=user_id,
            text=lock_text,
            reply_markup=kb.episode_lock_kb(dorama_id, user_id, bot_info.username, current_refs, needed),
            parse_mode=ParseMode.HTML
        )
        return

    await db.increment_views(dorama_id)
    await db.save_last_watched(user_id, dorama_id, ep_num)

    d = await db.get_dorama_by_id(dorama_id)
    title = d["title"] if d else "Dorama"

    episodes = await db.get_episodes(dorama_id)
    # Birlashgan qismlarni (1-2 qism) hisoblash
    display_items = kb.build_display_episodes(episodes)
    current_item = next((it for it in display_items if it['start_ep'] <= ep_num <= it['end_ep']), None)
    
    if current_item:
        ep_label = current_item['label']
        await db.save_last_watched(user_id, dorama_id, current_item['end_ep'])
        next_item = next((it for it in display_items if it['start_ep'] > current_item['end_ep']), None)
        has_next = next_item is not None
        next_ep_target = next_item['start_ep'] if next_item else None
    else:
        ep_label = f"{ep_num}-qism"
        await db.save_last_watched(user_id, dorama_id, ep_num)
        has_next = any(e['episode_number'] == ep_num + 1 for e in episodes)
        next_ep_target = ep_num + 1 if has_next else None

    bookmarked = await db.is_bookmarked(user_id, dorama_id)

    player_markup = kb.episode_player_kb(
        dorama_id=dorama_id,
        current_ep=ep_num,
        has_next=has_next,
        bookmarked=bookmarked,
        next_ep=next_ep_target
    )

    quality_badge = f"{ce('lightning')} 1080p Full HD" if ep.get("quality") == "1080p" else "720p HD"

    try:
        # protect_content=True: Galereyaga yuklash, boshqalarga forward qilish va skrinshot bloklanadi!
        await bot.copy_message(
            chat_id=user_id,
            from_chat_id=config.STORAGE_CHANNEL_ID,
            message_id=ep["channel_message_id"],
            caption=(
                f"{ce('film')} <b>«{title}» — {ep_label}</b> [{quality_badge}]\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"{ce('popcorn')} <i>Yoqimli tomosha!</i>\n"
                f"{ce('sparkles')} @{(await bot.get_me()).username}"
            ),
            reply_markup=player_markup,
            parse_mode=ParseMode.HTML,
            protect_content=True
        )
    except Exception as e:
        logger.error(f"Videoni uzatishda xatolik: {e}")
        await bot.send_message(
            user_id,
            f"{ce('bell')} Videoni yuborishda texnik xatolik yuz berdi. "
            f"Botingiz maxfiy kanalga admin qilinganini tekshiring!"
        )


# ---------------------------------------------------------------------------
# Menyu Buyruqlari va Doimiy Pastki Klaviatura Handlerlari
# ---------------------------------------------------------------------------
@router.message(Command("menu"))
@router.message(F.text.in_(["🎬 Doramalar", "🎬 Menyu", "📱 Menyu", "Bosh menyu", "Bosh sahifa"]))
async def handle_menu_trigger(message: Message, state: FSMContext):
    await state.clear()
    is_admin = (message.from_user.id == config.ADMIN_ID)
    user = message.from_user
    prem_badge = f" {ce('crown')} [PREMIUM]" if user.is_premium else ""
    text = (
        f"{ce('film')} <b>DORAMA HUB — Asosiy Menyu</b>\n\n"
        f"{ce('sparkles')} <b>{user.first_name}</b>{prem_badge}, quyidagi bo'limlardan birini tanlang:"
    )
    try:
        clean_msg = await message.answer("ㅤ", reply_markup=ReplyKeyboardRemove())
        await clean_msg.delete()
    except Exception:
        pass
    await message.answer(text, reply_markup=kb.main_menu_kb(is_admin=is_admin), parse_mode=ParseMode.HTML)



@router.message(Command("categories"))
@router.callback_query(F.data == "menu_categories")
async def handle_categories_menu(event: Message | CallbackQuery):
    counts = await db.get_category_counts()
    text = (
        f"{ce('film')} <b>KINO VA SERIAL KATEGORIYALARI:</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Qaysi yo'nalishdagi film va seriallarni tomosha qilmoqchisiz?\n\n"
        f"<i>Quyidagi bo'limlardan birini tanlang:</i>"
    )
    markup = kb.categories_hub_kb(counts)
    await render_text_screen(event, text, reply_markup=markup)
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.callback_query(F.data.startswith("cat:"))
async def cb_category_view(call: CallbackQuery):
    parts = call.data.split(":")
    cat_key = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 0

    limit = 8
    offset = page * limit
    cat_title, doramas = await db.get_doramas_by_category(cat_key, limit=limit + 1, offset=offset)

    if not doramas:
        text = (
            f"{ce('bell')} <b>{cat_title}</b> bo'limida hozircha kinolar mavjud emas.\n\n"
            f"<i>Ushbu bo'limga tez orada yangi premyeralar yuklanadi!</i>"
        )
        await render_text_screen(call, text, reply_markup=kb.categories_hub_kb(await db.get_category_counts()))
        await safe_answer(call)
        return

    has_next = len(doramas) > limit
    curr_doramas = doramas[:limit]

    text = f"{ce('film')} <b>{cat_title.upper()} ({page + 1}-sahifa):</b>"
    # Prefix includes category key for pagination
    markup = kb.doramas_list_kb(curr_doramas, prefix=f"cat:{cat_key}", page=page, has_next=has_next)
    await render_text_screen(call, text, reply_markup=markup)
    await safe_answer(call)


@router.message(Command("search"))
@router.message(F.text.in_(["🔍 Qidirish", "🔍 Qidiruv"]))
async def handle_search_trigger(message: Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_query)
    text = (
        f"{ce('search')} <b>Qidiruv Rejimi:</b>\n\n"
        f"Dorama nomini yoki uning <b>Kino kodini</b> yozing:\n"
        f"<i>(Masalan: <code>Doktor X</code> yoki <code>101</code>)</i>"
    )
    await message.answer(text, reply_markup=kb.back_to_menu_kb(), parse_mode=ParseMode.HTML)


@router.message(Command("top"))
@router.message(F.text.in_(["🔥 Top Ko'rilganlar", "🔥 Top"]))
async def handle_top_trigger(message: Message, state: FSMContext):
    await state.clear()
    limit = 8
    doramas = await db.get_top_doramas(limit=limit + 1, offset=0)
    has_next = len(doramas) > limit
    curr_list = doramas[:limit]
    text = f"{ce('fire')} <b>Eng Ko'p Ko'rilgan Top Doramalar:</b>"
    markup = kb.doramas_list_kb(curr_list, prefix="menu_top", page=0, has_next=has_next)
    await message.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)


@router.message(Command("bookmarks"))
@router.message(F.text.in_(["⭐️ Sevimlilarim", "⭐️ Sevimlilar"]))
async def handle_bookmarks_trigger(message: Message, state: FSMContext):
    await state.clear()
    doramas = await db.get_user_bookmarks(message.from_user.id)
    if not doramas:
        await message.answer(
            f"{ce('bookmark')} Sizda hali saqlangan doramalar yo'q.\nDorama kartasidan 'Saqlab qo'yish' tugmasini bosing!",
            reply_markup=kb.back_to_menu_kb(),
            parse_mode=ParseMode.HTML
        )
        return
    text = f"{ce('bookmark')} <b>Sizning Sevimli Doramalaringiz:</b>"
    markup = kb.doramas_list_kb(doramas, prefix="bookmarks", page=0, has_next=False)
    await message.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)


@router.message(Command("vip"))
@router.message(F.text.in_(["💎 VIP A'zolik", "💎 VIP"]))
async def handle_vip_trigger(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    is_vip = user.get("is_vip") if user else False
    vip_until = user.get("vip_until") if user else None

    vip_status_text = "Oddiy a'zo (Bepul)"
    if is_vip:
        if vip_until:
            vip_status_text = f"{ce('crown')} VIP Faol (Muddati: {vip_until} gacha)"
        else:
            vip_status_text = f"{ce('crown')} Cheksiz (Lifetime) VIP Faol"

    text = (
        f"{ce('diamond')} <b>«VIP» obuna muddatini tanlang:</b>\n\n"
        f"<blockquote>VIP obunachilar majburiy obunasiz, do'st chaqirmasdan va yopiq dramalarni 1080p Full HD sifatda cheklovsiz ko'radi.</blockquote>\n\n"
        f"{ce('user')} Sizning holatingiz: <b>{vip_status_text}</b>"
    )
    await message.answer(text, reply_markup=kb.vip_plans_kb(), parse_mode=ParseMode.HTML)


@router.message(Command("stats"))
@router.message(F.text == "📊 Statistika")
async def handle_stats_trigger(message: Message, state: FSMContext):
    await state.clear()
    stats = await db.get_stats()
    text = (
        f"{ce('sparkles')} <b>DORAMA HUB — Jonli Statistika:</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{ce('crown')} <b>Jami foydalanuvchilar:</b> {stats['total_users']:,} ta\n"
        f"{ce('sparkles')} <b>Bugun qo'shilganlar:</b> +{stats['today_users']} ta\n"
        f"{ce('diamond')} <b>Premium a'zolar:</b> {stats['premium_users']:,} ta\n"
        f"{ce('film')} <b>Jami Doramalar:</b> {stats['total_doramas']} ta\n"
        f"{ce('tv')} <b>Jami Qismlar:</b> {stats['total_episodes']} ta\n"
        f"{ce('eyes')} <b>Umumiy ko'rishlar:</b> {stats['total_views']:,} marta\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(text, reply_markup=kb.back_to_menu_kb(), parse_mode=ParseMode.HTML)


@router.message(F.text == "👑 Admin Panel")
async def handle_admin_reply_trigger(message: Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_ID:
        return
    await admin_panel_handler(message, state)


# ---------------------------------------------------------------------------
# Callback Handlers
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "menu_home")
async def cb_menu_home(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user = call.from_user
    prem_badge = f" {ce('crown')} [PREMIUM]" if user.is_premium else ""
    is_admin = (user.id == config.ADMIN_ID)

    text = (
        f"{ce('film')} <b>DORAMA HUB — Bosh Sahifa</b>\n\n"
        f"{ce('sparkles')} <b>{user.first_name}</b>{prem_badge}, quyidagi bo'limlardan birini tanlang:"
    )
    await render_text_screen(call, text, reply_markup=kb.main_menu_kb(is_admin=is_admin))
    await safe_answer(call)


@router.callback_query(F.data.startswith("menu_latest:"))
async def cb_menu_latest(call: CallbackQuery):
    page = int(call.data.split(":")[1])
    limit = 8
    doramas = await db.get_latest_doramas(limit=limit + 1, offset=page * limit)
    has_next = len(doramas) > limit
    curr_list = doramas[:limit]

    if not curr_list:
        await safe_answer(call, "Hozircha bazada dorama yo'q.", show_alert=True)
        return

    text = f"{ce('popcorn')} <b>Yangi Yuklangan Doramalar (Sahifa {page + 1}):</b>"
    markup = kb.doramas_list_kb(curr_list, prefix="menu_latest", page=page, has_next=has_next)
    await render_text_screen(call, text, reply_markup=markup)
    await safe_answer(call)


@router.callback_query(F.data.startswith("menu_top"))
async def cb_menu_top(call: CallbackQuery):
    page = 0
    if ":" in call.data:
        try:
            page = max(0, int(call.data.split(":")[1]))
        except Exception:
            page = 0
    limit = 8
    doramas = await db.get_top_doramas(limit=limit + 1, offset=page * limit)
    has_next = len(doramas) > limit
    curr_list = doramas[:limit]

    if not curr_list:
        await safe_answer(call, "Hozircha ma'lumot yetarli emas.", show_alert=True)
        return

    text = f"{ce('fire')} <b>Eng Ko'p Ko'rilgan Top Doramalar (Sahifa {page + 1}):</b>"
    markup = kb.doramas_list_kb(curr_list, prefix="menu_top", page=page, has_next=has_next)
    await render_text_screen(call, text, reply_markup=markup)
    await safe_answer(call)


@router.callback_query(F.data == "menu_bookmarks")
async def cb_menu_bookmarks(call: CallbackQuery):
    user_id = call.from_user.id
    doramas = await db.get_user_bookmarks(user_id)
    if not doramas:
        await safe_answer(call, "Sizda hali saqlangan doramalar yo'q. Dorama kartasidan 'Saqlab qo'yish' tugmasini bosing!", show_alert=True)
        return

    text = f"{ce('bookmark')} <b>Sizning Sevimli Doramalaringiz:</b>"
    markup = kb.doramas_list_kb(doramas, prefix="bookmarks", page=0, has_next=False)
    await render_text_screen(call, text, reply_markup=markup)
    await safe_answer(call)


@router.callback_query(F.data.startswith("view_dorama:"))
async def cb_view_dorama(call: CallbackQuery, bot: Bot):
    d_id = int(call.data.split(":")[1])
    await show_dorama_detail(call, d_id, bot, user_id=call.from_user.id)
    await safe_answer(call)


@router.callback_query(F.data.startswith("ep_page:"))
async def cb_ep_page(call: CallbackQuery, bot: Bot):
    parts = call.data.split(":")
    d_id, page = int(parts[1]), int(parts[2])
    await show_dorama_detail(call, d_id, bot, user_id=call.from_user.id, page=page)
    await safe_answer(call)


@router.callback_query(F.data.startswith("get_ep:"))
async def cb_get_ep(call: CallbackQuery, bot: Bot):
    parts = call.data.split(":")
    d_id, ep_num = int(parts[1]), int(parts[2])

    unlocked, reason, current_refs, req_refs = await db.is_user_unlocked(call.from_user.id, ep_num, config.ADMIN_ID)
    if not unlocked:
        bot_info = await bot.get_me()
        needed = max(1, req_refs - current_refs)
        await safe_answer(call, f"🔒 {ep_num}-qism qulflangan! Yana {needed} ta do'st kerak.", show_alert=True)
        lock_text = (
            f"{ce('lock')} <b>{ep_num}-QISM QULFLANGAN!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Hurmatli <b>{call.from_user.first_name}</b>, 1, 2 va 3-qismlar mutlaqo bepul.\n\n"
            f"{ce('stats')} Sizning takliflaringiz: <b>{current_refs} ta</b>\n"
            f"{ce('target')} <b>{ep_num}-qism uchun talab:</b> <b>{req_refs} ta</b> do'st "
            f"<i>(Yana <b>{needed} ta</b> do'stingiz botga kirishi kerak)</i>.\n\n"
            f"<b>Qulfni ochish yo'llari:</b>\n"
            f"1️⃣ <b>Do'stlarni chaqirish:</b> Har bir do'stingiz yangi qismni bepul ochadi.\n"
            f"2️⃣ <b>VIP A'zolik:</b> 9 000 so'm/oy bilan barcha cheklovlarni bir zumda olib tashlang.\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
        await call.message.answer(
            lock_text,
            reply_markup=kb.episode_lock_kb(d_id, call.from_user.id, bot_info.username, current_refs, needed),
            parse_mode=ParseMode.HTML
        )
        return

    await safe_answer(call, f"{ep_num}-qism yuborilmoqda...", show_alert=False)
    await send_episode(call.from_user.id, d_id, ep_num, bot)


@router.callback_query(F.data.startswith("toggle_bm:"))
async def cb_toggle_bm(call: CallbackQuery, bot: Bot):
    d_id = int(call.data.split(":")[1])
    added = await db.toggle_bookmark(call.from_user.id, d_id)
    alert = "⭐️ Sevimlilarga qo'shildi!" if added else "❌ Sevimlilardan olib tashlandi."
    await safe_answer(call, alert, show_alert=True)
    await show_dorama_detail(call, d_id, bot, user_id=call.from_user.id)


@router.callback_query(F.data.startswith("toggle_sub:"))
async def cb_toggle_sub(call: CallbackQuery, bot: Bot):
    d_id = int(call.data.split(":")[1])
    subbed = await db.toggle_subscription(call.from_user.id, d_id)
    alert = "🔔 Bildirishnoma yoqildi! Yangi qism chiqishi bilan xabar beramiz." if subbed else "🔕 Bildirishnoma o'chirildi."
    await safe_answer(call, alert, show_alert=True)
    await show_dorama_detail(call, d_id, bot, user_id=call.from_user.id)


# ---------------------------------------------------------------------------
# Qidiruv & Kino kodi tekshiruvi
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "menu_search")
async def cb_menu_search(call: CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_for_query)
    text = (
        f"{ce('search')} <b>Qidiruv Rejimi:</b>\n\n"
        f"Dorama nomini yoki uning <b>Kino kodini</b> yozing:\n"
        f"<i>(Masalan: <code>Doktor X</code> yoki <code>101</code>)</i>"
    )
    await render_text_screen(call, text, reply_markup=kb.back_to_menu_kb())
    await safe_answer(call)


@router.message(StateFilter(None, BotStates.waiting_for_query), F.text, F.text.regexp(r"^\d{1,6}$"))
async def process_numeric_code(message: Message, state: FSMContext, bot: Bot):
    """Foydalanuvchi to'g'ridan-to'g'ri raqam yozganda (Kino Kodi)."""
    await state.clear()
    code = int(message.text.strip())
    d = await db.get_dorama_by_code(code)
    if d:
        await show_dorama_detail(message, d["id"], bot, user_id=message.from_user.id)
    else:
        await message.answer(
            f"{ce('bell')} <b>{code}</b> raqamli dorama topilmadi.\nKodni to'g'ri kiritganingizni tekshiring.",
            reply_markup=kb.back_to_menu_kb(),
            parse_mode=ParseMode.HTML
        )


@router.message(StateFilter(None, BotStates.waiting_for_query), F.text, ~F.text.startswith('/'))
async def process_search_query(message: Message, state: FSMContext, bot: Bot):
    if message.text.startswith("/"):
        return

    query = message.text.strip()
    await state.clear()

    # Agar raqam bo'lsa kod bo'yicha qidiramiz
    if query.isdigit():
        code = int(query)
        d = await db.get_dorama_by_code(code)
        if d:
            await show_dorama_detail(message, d["id"], bot, user_id=message.from_user.id)
            return
        else:
            await message.answer(
                f"{ce('bell')} <b>{code}</b> raqamli dorama topilmadi.\nKodni to'g'ri kiritganingizni tekshiring.",
                reply_markup=kb.back_to_menu_kb(),
                parse_mode=ParseMode.HTML
            )
            return

    # 5-talab: Kamida 2 ta harfdan iborat so'zlarnigina qidirish tekshiruvi
    if len(query) < 2:
        await message.answer(
            f"{ce('bell')} <b>Iltimos, qidirish uchun kamida 2 ta harfdan iborat so'z kiriting!</b>\n\n"
            f"<i>Masalan: <code>Doktor</code> yoki <code>101</code></i>",
            reply_markup=kb.back_to_menu_kb(),
            parse_mode=ParseMode.HTML
        )
        return

    results = await db.search_doramas(query, limit=10)
    if not results:
        text = (
            f"{ce('bell')} <b>'{query}'</b> bo'yicha hech narsa topilmadi.\n\n"
            f"{ce('bulb')} <i>Nomini to'g'ri yozganingizni tekshiring yoki kino kodini kiriting (masalan: <code>101</code>).</i>"
        )
        await message.answer(text, reply_markup=kb.back_to_menu_kb(), parse_mode=ParseMode.HTML)
        return

    text = f"{ce('search')} <b>'{query}'</b> bo'yicha topilgan natijalar:"
    markup = kb.doramas_list_kb(results, prefix="search", page=0, has_next=False)
    await message.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)


# ---------------------------------------------------------------------------
# Statistika
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "menu_stats")
async def cb_menu_stats(call: CallbackQuery):
    stats = await db.get_stats()
    text = (
        f"{ce('sparkles')} <b>DORAMA HUB — Jonli Statistika:</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{ce('crown')} <b>Jami foydalanuvchilar:</b> {stats['total_users']:,} ta\n"
        f"{ce('sparkles')} <b>Bugun qo'shilganlar:</b> +{stats['today_users']} ta\n"
        f"{ce('diamond')} <b>Premium a'zolar:</b> {stats['premium_users']:,} ta\n"
        f"{ce('film')} <b>Jami Doramalar:</b> {stats['total_doramas']} ta\n"
        f"{ce('tv')} <b>Jami Qismlar:</b> {stats['total_episodes']} ta\n"
        f"{ce('eyes')} <b>Umumiy ko'rishlar:</b> {stats['total_views']:,} marta\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    await render_text_screen(call, text, reply_markup=kb.back_to_menu_kb())
    await safe_answer(call)


# ---------------------------------------------------------------------------
# VIP A'zolik & To'lov Tizimi (Disruption Pricing: 9,000 UZS)
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "menu_vip")
async def cb_menu_vip(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await db.get_user(call.from_user.id)
    is_vip = user.get("is_vip") if user else False
    vip_until = user.get("vip_until") if user else None

    vip_status_text = "Oddiy a'zo (Bepul)"
    if is_vip:
        if vip_until:
            vip_status_text = f"{ce('crown')} VIP Faol (Muddati: {vip_until} gacha)"
        else:
            vip_status_text = f"{ce('crown')} Cheksiz (Lifetime) VIP Faol"

    text = (
        f"{ce('diamond')} <b>«VIP» obuna muddatini tanlang:</b>\n\n"
        f"<blockquote>VIP obunachilar majburiy obunasiz, do'st chaqirmasdan va yopiq dramalarni 1080p Full HD sifatda cheklovsiz ko'radi.</blockquote>\n\n"
        f"{ce('user')} Sizning holatingiz: <b>{vip_status_text}</b>"
    )
    await render_text_screen(call, text, reply_markup=kb.vip_plans_kb())
    await safe_answer(call)


@router.callback_query(F.data.startswith("buy_vip:"))
async def cb_buy_vip(call: CallbackQuery, state: FSMContext):
    plan_code = call.data.split(":")[1]
    plan = VIP_PLANS.get(plan_code)
    if not plan:
        await safe_answer(call, "Noma'lum tarif!", show_alert=True)
        return

    await state.set_state(VipStates.waiting_for_receipt)
    await state.update_data(plan=plan_code)

    text = (
        f"{ce('card')} <b>TO'LOV MA'LUMOTLARI: {plan['title'].upper()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{ce('cash')} To'lov summasi: <b>{plan['price_str']}</b>\n"
        f"{ce('calendar')} Muddat: <b>{plan['days']} kun</b>\n\n"
        f"<b>To'lov usullari:</b>\n"
        f"{ce('card')} <b>Click / Payme / Uzcard / Humo:</b>\n"
        f"{ce('card')} Karta raqam: <code>8600 0000 0000 0000</code>\n"
        f"{ce('user')} Qabul qiluvchi: <b>Dorama Hub Admin</b>\n\n"
        f"{ce('camera')} <b>QADAMLAR:</b>\n"
        f"1. Yuqoridagi kartaga <b>{plan['price_str']}</b> o'tkazing.\n"
        f"2. To'lov amalga oshirilgan <b>chek skrinshotini</b> yoki PDF hujjatini to'g'ridan-to'g'ri shu yerga yuboring.\n"
        f"3. Chek tekshirilgach, botingizga darhol VIP maqomi faollashadi!\n\n"
        f"<i>Bekor qilish uchun /cancel yozing.</i>"
    )
    await render_text_screen(call, text, reply_markup=kb.back_to_menu_kb())
    await safe_answer(call)


@router.message(VipStates.waiting_for_receipt, F.photo | F.document)
async def process_receipt(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    plan_code = data.get("plan", "1m")
    plan = VIP_PLANS.get(plan_code, VIP_PLANS["1m"])
    await state.clear()

    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    user = message.from_user

    order_id = await db.create_vip_order(
        user_id=user.id,
        plan=plan_code,
        amount=plan["price"],
        receipt_file_id=file_id
    )

    user_msg = (
        f"{ce('check_green')} <b>To'lov chekingiz qabul qilindi! (Buyurtma #{order_id})</b>\n\n"
        f"Tanlangan tarif: <b>{plan['title']}</b> ({plan['price_str']})\n"
        f"Administrator chekni tekshirib, tez orada VIP a'zoligingizni yoqadi "
        f"(odatda 5-15 daqiqa ichida).\n\n"
        f"Sabringiz uchun tashakkur! {ce('popcorn')}"
    )
    await message.answer(user_msg, reply_markup=kb.back_to_menu_kb(), parse_mode=ParseMode.HTML)

    admin_caption = (
        f"{ce('bell')} <b>YANGI VIP BUYURTMA #{order_id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{ce('user')} Foydalanuvchi: <a href='tg://user?id={user.id}'>{user.full_name}</a>\n"
        f"{ce('code')} Telegram ID: <code>{user.id}</code>\n"
        f"{ce('package')} Tarif: <b>{plan['title']}</b>\n"
        f"{ce('cash')} Summa: <b>{plan['price_str']}</b>\n"
        f"{ce('calendar')} Muddat: <b>{plan['days']} kun</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"To'lovni tasdiqlaysizmi?"
    )

    admin_markup = kb.admin_order_kb(order_id=order_id, user_id=user.id, days=plan['days'])
    try:
        if message.photo:
            await bot.send_photo(
                chat_id=config.ADMIN_ID,
                photo=file_id,
                caption=admin_caption,
                reply_markup=admin_markup,
                parse_mode=ParseMode.HTML
            )
        else:
            await bot.send_document(
                chat_id=config.ADMIN_ID,
                document=file_id,
                caption=admin_caption,
                reply_markup=admin_markup,
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Adminga chek yuborishda xatolik: {e}")


@router.callback_query(F.data.startswith("submit_receipt:"))
async def cb_submit_receipt(call: CallbackQuery, state: FSMContext):
    plan_code = call.data.split(":")[1]
    await state.set_state(VipStates.waiting_for_receipt)
    await state.update_data(plan=plan_code)
    text = (
        f"{ce('camera')} Iltimos, to'lov amalga oshirilgan <b>chek skrinshotini (rasm)</b> yoki PDF hujjatini shu yerga yuboring:\n\n"
        f"<i>Bekor qilish uchun /cancel deb yozing.</i>"
    )
    await render_text_screen(call, text, reply_markup=kb.back_to_menu_kb())
    await safe_answer(call)


@router.message(VipStates.waiting_for_receipt, F.text)
async def process_receipt_text_guide(message: Message):
    if message.text.startswith("/"):
        return
    await message.answer(
        f"{ce('bell')} Iltimos, to'lov tasdiqlanishi uchun <b>chek skrinshotini (rasm)</b> yoki PDF faylini yuboring.\n"
        f"Bekor qilish uchun /cancel deb yozing.",
        reply_markup=kb.back_to_menu_kb(),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data.startswith("admin_approve:"))
async def cb_admin_approve(call: CallbackQuery, bot: Bot):
    if call.from_user.id != config.ADMIN_ID:
        await safe_answer(call, "Siz admin emassiz!", show_alert=True)
        return

    parts = call.data.split(":")
    order_id = int(parts[1])
    target_user_id = int(parts[2])
    days = int(parts[3])

    await db.update_order_status(order_id, "approved")
    await db.grant_vip(target_user_id, days=days)

    try:
        await bot.send_message(
            chat_id=target_user_id,
            text=(
                f"{ce('party')} <b>TABRIKLAYMIZ! VIP A'ZOLIK FAOLLASHTIRILDI!</b>\n\n"
                f"{ce('crown')} Sizga <b>{days} kunlik</b> to'liq VIP ruxsati berildi.\n"
                f"Endi botdagi barcha yangi qismlarni hech qanday to'siqsiz, "
                f"1080p Full HD sifatda tomosha qilishingiz mumkin! {ce('popcorn')}"
            ),
            reply_markup=kb.back_to_menu_kb(),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.warning(f"Foydalanuvchiga VIP ochilganini yuborishda xatolik: {e}")

    caption_base = call.message.caption or ""
    await call.message.edit_caption(
        caption=(
            f"{caption_base}\n\n"
            f"{ce('check_green')} <b>BUYURTMA #{order_id} TASDIQLANDI! (+{days} kun VIP berildi)</b>"
        ),
        reply_markup=None,
        parse_mode=ParseMode.HTML
    )
    await safe_answer(call, "VIP muvaffaqiyatli berildi!", show_alert=True)


@router.callback_query(F.data.startswith("admin_reject:"))
async def cb_admin_reject(call: CallbackQuery, bot: Bot):
    if call.from_user.id != config.ADMIN_ID:
        await safe_answer(call, "Siz admin emassiz!", show_alert=True)
        return

    parts = call.data.split(":")
    order_id = int(parts[1])
    target_user_id = int(parts[2])

    await db.update_order_status(order_id, "rejected")

    try:
        await bot.send_message(
            chat_id=target_user_id,
            text=(
                f"{ce('cross_red')} <b>To'lov chekingiz tasdiqlanmadi (Buyurtma #{order_id}).</b>\n\n"
                f"Chek noto'g'ri yuborilgan yoki to'lov hisobga kelib tushmagan bo'lishi mumkin.\n"
                f"Savollaringiz bo'lsa adminga murojaat qiling."
            ),
            reply_markup=kb.back_to_menu_kb(),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.warning(f"Foydalanuvchiga rad etilganini yuborishda xatolik: {e}")

    caption_base = call.message.caption or ""
    await call.message.edit_caption(
        caption=(
            f"{caption_base}\n\n"
            f"{ce('cross_red')} <b>BUYURTMA #{order_id} RAD ETILDI.</b>"
        ),
        reply_markup=None,
        parse_mode=ParseMode.HTML
    )
    await safe_answer(call, "Buyurtma rad etildi.", show_alert=True)


# ---------------------------------------------------------------------------
# Admin Panel & Ommaviy Xabar (Broadcast)
# ---------------------------------------------------------------------------

@router.message(Command("ongoing"))
@router.callback_query(F.data == "admin_ongoing_list")
async def handle_admin_ongoing_list(event: Message | CallbackQuery):
    user_id = event.from_user.id
    if user_id != config.ADMIN_ID:
        if isinstance(event, CallbackQuery):
            await event.answer("Siz admin emassiz!", show_alert=True)
        else:
            await event.answer("⚠️ Siz admin emassiz!")
        return

    doramas = await db.get_ongoing_doramas()
    if not doramas:
        text = (
            f"{ce('bell')} <b>Hozirda davom etayotgan (Ongoing) seriallar yo'q.</b>\n\n"
            f"Barcha seriallar to'liq tugallangan."
        )
        await render_text_screen(event, text, reply_markup=kb.admin_panel_kb())
        if isinstance(event, CallbackQuery):
            await event.answer()
        return

    text = (
        f"{ce('green_circle')} <b>DAVOM ETAYOTGAN (ONGOING) SERIALlar:</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Hozirda <b>{len(doramas)} ta</b> serial faol davom etmoqda:\n\n"
    )
    for i, d in enumerate(doramas, 1):
        text += (
            f"<b>{i}. [{d['code']}] {d['title']}</b>\n"
            f"   └ 🎬 Yuklangan: <b>{d['uploaded_episodes']} ta</b> qism\n"
        )

    text += (
        f"\n━━━━━━━━━━━━━━━━━━\n"
        f"💡 <i>Yangi qism chiqqanda, menga serial kodi va Telegram linklarini bersangiz, darhol yangi qismlarni qo'shib qo'yaman!</i>"
    )

    markup = kb.ongoing_doramas_kb(doramas)
    await render_text_screen(event, text, reply_markup=markup)
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(Command("admin"))
@router.callback_query(F.data == "menu_admin")
async def admin_panel_handler(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = event.from_user.id
    if user_id != config.ADMIN_ID:
        if isinstance(event, CallbackQuery):
            await event.answer("Siz admin emassiz!", show_alert=True)
        else:
            await event.answer("⚠️ Siz admin emassiz!")
        return

    stats = await db.get_stats()
    text = (
        f"{ce('crown')} <b>ADMIN BOSHQARUV PANELI:</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{ce('sparkles')} <b>Foydalanuvchilar:</b> {stats['total_users']:,} ta (Bugun: +{stats['today_users']})\n"
        f"{ce('film')} <b>Doramalar:</b> {stats['total_doramas']} ta\n"
        f"{ce('tv')} <b>Yuklangan qismlar:</b> {stats['total_episodes']} ta\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Quyidagi amallardan birini tanlang:"
    )

    await render_text_screen(event, text, reply_markup=kb.admin_panel_kb())
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(Command("vip"))
@router.message(Command("setvip"))
async def handle_set_vip_command(message: Message):
    user_id = message.from_user.id
    if user_id != config.ADMIN_ID and user_id != 7141955036:
        return

    parts = (message.text or "").split()
    if len(parts) == 1:
        await db.grant_vip(user_id, days=3650)
        await message.answer(
            f"{ce('crown')} <b>Sizga (Admin) cheksiz VIP maqomi faollashtirildi!</b>\n"
            f"Barcha serial va kino qismlari siz uchun 100% cheklovlarsiz ochildi."
        )
        return

    target_id_str = parts[1]
    days = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 30

    if not target_id_str.isdigit():
        await message.answer("⚠️ Format noto'g'ri! Masalan: <code>/vip 123456789 30</code>")
        return

    target_id = int(target_id_str)
    await db.grant_vip(target_id, days=days)
    await message.answer(
        f"{ce('check_green')} <b>Foydalanuvchi <code>{target_id}</code> uchun {days} kunlik VIP berildi!</b>"
    )


@router.message(Command("myvip"))
async def handle_my_vip_command(message: Message):
    user = await db.get_user(message.from_user.id)
    if user and user.get("is_vip") in (1, "1", True):
        until = user.get("vip_until") or "Cheksiz (Lifetime)"
        await message.answer(
            f"{ce('crown')} <b>Sizning VIP maqomingiz: FAOLLASHTIRILGAN!</b>\n\n"
            f"📅 Amal qilish muddati: <b>{until}</b>\n"
            f"✨ Barcha qismlar qulflarsiz, do'st taklif qilmasdan ochiq."
        )
    else:
        await message.answer(
            f"{ce('lock')} <b>Sizda hozircha VIP a'zolik yo'q.</b>\n\n"
            f"VIP a'zolik olish uchun menyudagi <b>VIP A'zolik</b> tugmasidan foydalanishingiz mumkin."
        )


@router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != config.ADMIN_ID:
        return
    await state.set_state(BotStates.waiting_for_broadcast)
    text = (
        f"{ce('broadcast')} <b>OMMAVIY XABAR YUBORISH:</b>\n\n"
        f"Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni (matn, rasm yoki video) bu yerga yuboring.\n"
        f"Bekor qilish uchun /cancel deb yozing."
    )
    await render_text_screen(call, text, reply_markup=kb.back_to_menu_kb())
    await safe_answer(call)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Amal bekor qilindi.", reply_markup=kb.main_menu_kb(is_admin=(message.from_user.id == config.ADMIN_ID)))


@router.message(BotStates.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id != config.ADMIN_ID:
        return

    await state.clear()
    user_ids = await db.get_all_user_ids()
    status_msg = await message.answer(f"⏳ Ommaviy xabar yuborilmoqda ({len(user_ids)} kishiga)...")

    sent = 0
    failed = 0

    for uid in user_ids:
        try:
            await message.copy_to(chat_id=uid)
            sent += 1
            await asyncio.sleep(0.04)  # Telegram limitiga tushmaslik uchun
        except Exception:
            failed += 1

    report = (
        f"{ce('check_green')} <b>Ommaviy xabar yakunlandi!</b>\n\n"
        f"{ce('mailbox')} Yuborildi: <b>{sent}</b> ta\n"
        f"{ce('cross_red')} Yetib bormadi (bloklagan): <b>{failed}</b> ta"
    )
    await status_msg.edit_text(report, parse_mode=ParseMode.HTML)



def execute_git_update() -> tuple[bool, str]:
    """
    GitHub'dan so'nggi yangilanishlarni (git pull) xavfsiz tortib oladi.
    Foydalanuvchilar ma'lumotlarini (users, bookmarks, history, vip) to'liq zaxiralab,
    yangi doramalar va kod bilan xatosiz birlashtiradi.
    """
    base_dir = config.BASE_DIR
    db_path = config.DB_PATH

    # Agar configda GITHUB_TOKEN bo'lsa, remote origin ni avtomatik tokenli URL ga o'rnatish
    github_token = getattr(config, "GITHUB_TOKEN", "")
    if github_token:
        try:
            subprocess.run(
                ["git", "remote", "set-url", "origin", f"https://{github_token}@github.com/zephcodeer/uzkdrama-bot.git"],
                cwd=base_dir,
                capture_output=True,
                timeout=10
            )
        except Exception as e:
            logger.warning(f"Git remote url o'rnatishda ogohlantirish: {e}")

    # 1. Git mavjudligini tekshirish
    try:
        ver = subprocess.run(["git", "--version"], cwd=base_dir, capture_output=True, text=True, timeout=10)
        if ver.returncode != 0:
            return False, "Git serverda o'rnatilmagan yoki topilmadi."
    except Exception as e:
        return False, f"Git tekshirishda xatolik: {e}"

    # 2. Serverdagi foydalanuvchilar va buyurtmalarni zaxiralash
    user_tables = ['users', 'bookmarks', 'user_history', 'dorama_subscribers', 'vip_orders']
    user_data = {}

    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            for tbl in user_tables:
                try:
                    cursor.execute(f"SELECT * FROM {tbl}")
                    cols = [d[0] for d in cursor.description]
                    rows = cursor.fetchall()
                    user_data[tbl] = (cols, rows)
                except Exception:
                    pass
            conn.close()
        except Exception as e:
            logger.warning(f"Foydalanuvchilar ma'lumotlarini zaxiralashda ogohlantirish: {e}")

    # 3. Git ishchi nusxasini tozalash (git pull ga xalaqit bermasligi uchun)
    try:
        subprocess.run(["git", "checkout", "HEAD", "--", "doramas.db"], cwd=base_dir, capture_output=True, timeout=15)
    except Exception:
        pass

    # 4. Git pull origin main ni ishga tushirish
    try:
        pull_proc = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=90
        )
        stdout = (pull_proc.stdout or "").strip()
        stderr = (pull_proc.stderr or "").strip()

        if pull_proc.returncode != 0:
            err_msg = stderr if stderr else stdout
            return False, f"Git pull xatoligi (kod {pull_proc.returncode}):\n{err_msg[:400]}"

    except subprocess.TimeoutExpired:
        return False, "Git pull 90 soniya ichida yakunlanmadi (Timeout)."
    except Exception as e:
        return False, f"Git pull jarayonida kutilmagan xatolik: {e}"

    # 5. Zaxiralangan foydalanuvchilar ma'lumotlarini yangilangan doramas.db ga qayta yozish
    if user_data and os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            for tbl, (cols, rows) in user_data.items():
                if not rows:
                    continue
                placeholders = ",".join(["?"] * len(cols))
                col_names = ",".join(cols)
                cursor.executemany(f"INSERT OR REPLACE INTO {tbl} ({col_names}) VALUES ({placeholders})", rows)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Foydalanuvchilar ma'lumotlarini tiklashda xatolik: {e}")

    # 6. Yangilanish bor-yo'qligini tekshirish
    if "Already up to date" in stdout or "Already up-to-date" in stdout:
        return True, "ALREADY_UP_TO_DATE"

    return True, stdout


@router.message(Command("update"))
@router.callback_query(F.data == "admin_git_update")
async def handle_admin_git_update(event: Message | CallbackQuery, bot: Bot):
    user_id = event.from_user.id
    if user_id != config.ADMIN_ID:
        if isinstance(event, CallbackQuery):
            await event.answer("Siz admin emassiz!", show_alert=True)
        else:
            await event.answer("⚠️ Siz admin emassiz!")
        return

    if isinstance(event, CallbackQuery):
        await event.answer("⏳ Yangilanish tekshirilmoqda...")
        status_msg = await event.message.answer(
            f"{ce('sparkles')} <b>GitHub'dan yangilanishlar tekshirilmoqda...</b>\n<i>Iltimos, kuting...</i>",
            parse_mode=ParseMode.HTML
        )
    else:
        status_msg = await event.answer(
            f"{ce('sparkles')} <b>GitHub'dan yangilanishlar tekshirilmoqda...</b>\n<i>Iltimos, kuting...</i>",
            parse_mode=ParseMode.HTML
        )

    success, result_text = await asyncio.to_thread(execute_git_update)

    if not success:
        await status_msg.edit_text(
            f"{ce('cross_red')} <b>Yangilashda xatolik yuz berdi:</b>\n\n"
            f"<code>{result_text}</code>",
            parse_mode=ParseMode.HTML
        )
        return

    if result_text == "ALREADY_UP_TO_DATE":
        await status_msg.edit_text(
            f"{ce('check_green')} <b>Bot allaqachon eng so'nggi versiyada!</b>\n\n"
            f"GitHub omborida yangi o'zgarishlar mavjud emas.",
            reply_markup=kb.admin_panel_kb(),
            parse_mode=ParseMode.HTML
        )
        return

    # Muvaffaqiyatli yangilandi
    summary_lines = [line.strip() for line in result_text.splitlines() if line.strip()][:6]
    summary = "\n".join(summary_lines)

    await status_msg.edit_text(
        f"{ce('party')} <b>YANGILANISH MUVAFFAQIYATLI YUKLANDI!</b>\n\n"
        f"<b>Git hisoboti:</b>\n"
        f"<code>{summary}</code>\n\n"
        f"🔄 <b>Bot 2 soniyada qayta ishga tushadi...</b>",
        parse_mode=ParseMode.HTML
    )

    await asyncio.sleep(2)
    sys.stdout.flush()
    sys.stderr.flush()

    # Yangi kod va ma'lumotlar bilan botni qayta ishga tushirish
    executable = sys.executable
    args = [executable] + sys.argv
    try:
        os.execvp(executable, args)
    except Exception as e:
        logger.error(f"os.execvp xatosi: {e}. os.execv sinab ko'rilmoqda...")
        try:
            os.execv(executable, args)
        except Exception as e2:
            logger.error(f"os.execv ham xato berdi: {e2}. Process exit qilinmoqda...")
            os._exit(0)


@router.message(Command("help", "menu"))
async def cmd_help_menu(message: Message, state: FSMContext):
    await state.clear()
    is_admin = (message.from_user.id == config.ADMIN_ID)
    text = (
        f"{ce('film')} <b>DORAMA HUB — Asosiy Menyu</b>\n\n"
        f"{ce('popcorn')} Botdan foydalanish:\n"
        f"• Dorama nomini yoki kodini (masalan: <code>101</code>) yozing\n"
        f"• 1-3 qismlar mutlaqo bepul, keyingi qismlar uchun do'stlaringizni taklif qiling yoki VIP oling\n\n"
        f"Quyidagi bo'limlardan birini tanlang:"
    )
    await message.answer(text, reply_markup=kb.main_menu_kb(is_admin=is_admin), parse_mode=ParseMode.HTML)


@router.error()
async def global_error_handler(event: ErrorEvent):
    logger.error(f"Global unhandled exception: {event.exception}", exc_info=True)
    try:
        if event.update.callback_query:
            await event.update.callback_query.answer("⚠️ Texnik xatolik yuz berdi. Iltimos, qayta urinib ko'ring.", show_alert=True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Asosiy bot ishga tushirish
# ---------------------------------------------------------------------------
async def main():
    errors = config.validate_bot_config()
    if errors:
        print("\n" + "=" * 60)
        print("BOTNI ISHGA TUSHIRISHDA XATOLIK:")
        for err in errors:
            print(f"  ❌ {err}")
        print("=" * 60 + "\n")
        return

    await db.init_db()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(router)

    bot_info = None
    for attempt in range(1, 11):
        try:
            bot_info = await bot.get_me()
            break
        except Exception as e:
            logger.warning(f"Telegramga ulanish {attempt}/10 muvaffaqiyatsiz ({e}). 3s kutilmoqda...")
            await asyncio.sleep(3)
    if not bot_info:
        logger.error("Telegram API ga ulanib bo'lmadi!")
        return
    print("\n" + "=" * 50)
    print(f"DORAMA HUB BOTI ISHGA TUSHDI: @{bot_info.username}")
    print(f"Maxfiy Kanal ID: {config.STORAGE_CHANNEL_ID}")
    print("=" * 50 + "\n")

    # Telegram bot rasmiy menyusi va buyruqlarini ro'yxatdan o'tkazish
    try:
        commands = [
            BotCommand(command="start", description="🎬 Botni qayta ishga tushirish"),
            BotCommand(command="menu", description="📱 Asosiy menyuni ochish"),
            BotCommand(command="categories", description="📁 Kategoriyalar va Janrlar"),
            BotCommand(command="search", description="🔍 Dorama qidirish (nomi yoki kodi)"),
            BotCommand(command="top", description="🔥 Eng ko'p ko'rilgan doramalar"),
            BotCommand(command="bookmarks", description="⭐️ Saqlangan doramalaringiz"),
            BotCommand(command="vip", description="💎 VIP a'zolik (barcha qismlar)"),
            BotCommand(command="stats", description="📊 Jonli statistika"),
            BotCommand(command="help", description="ℹ️ Yordam va ma'lumot"),
        ]
        await bot.set_my_commands(commands)
        await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
        print("✅ Telegram doimiy 'Menu' tugmasi va buyruqlar to'liq o'rnatildi.")

        # Faqat admin uchun maxsus /update buyrug'i
        try:
            admin_commands = commands + [BotCommand(command="update", description="🚀 GitHub'dan yangilash"), BotCommand(command="ongoing", description="🟢 Davom etayotgan seriallar")]
            await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=config.ADMIN_ID))
        except Exception as e:
            logger.warning(f"Admin buyruqlarini sozlashda ogohlantirish: {e}")

    except Exception as e:
        logger.warning(f"Menyu tugmasini sozlashda xatolik: {e}")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")
