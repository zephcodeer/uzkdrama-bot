import html
import re

import gc

async def memory_cleanup_loop():
    """Har 15 daqiqada RAM va SQLite xotirasini tozalaydi (OOM kill oldini olish uchun)."""
    while True:
        await asyncio.sleep(900)
        try:
            gc.collect()
            await db.optimize_db()
            logger.info("RAM va SQLite keshi muvaffaqiyatli tozalandi.")
        except Exception:
            pass

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

from aiogram.types import (
    CallbackQuery, Message, FSInputFile, ErrorEvent, BotCommand,
    BotCommandScopeChat, MenuButtonCommands, ReplyKeyboardRemove,
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
    InlineKeyboardMarkup, InlineKeyboardButton
)



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

    waiting_for_dorama_suggestion = State()

    waiting_for_suggestion_reply = State()

    waiting_for_suggestion_exist_code = State()





class VipStates(StatesGroup):

    waiting_for_receipt = State()





VIP_PLANS = {

    "1m": {"title": "1 oylik VIP", "price": 9000, "days": 30, "price_str": "9 000 so'm"},

    "6m": {"title": "6 oylik VIP", "price": 34000, "days": 180, "price_str": "34 000 so'm"},

    "1y": {"title": "1 yillik VIP", "price": 49000, "days": 365, "price_str": "49 000 so'm"},

    "life": {"title": "Cheksiz VIP", "price": 79000, "days": 3650, "price_str": "79 000 so'm"},

}






# ---------------------------------------------------------------------------
# Majburiy Obuna (Force Subscription) Tizimi
# ---------------------------------------------------------------------------


def is_admin_user(user_id: int) -> bool:
    """Adminlik huquqini yagona nuqtadan tekshiradi."""
    return user_id == config.ADMIN_ID or user_id == 7141955036

async def is_user_channel_member(bot: Bot, user_id: int) -> bool:
    """Foydalanuvchi majburiy kanalda a'zo ekanligini tekshiradi."""
    # 1. Admin har doim to'liq ruxsatga ega
    if user_id == config.ADMIN_ID or user_id == 7141955036:
        return True

    # 2. VIP foydalanuvchilar majburiy obunasiz tomosha qilish huquqiga ega
    try:
        if await db.is_vip(user_id):
            return True
    except Exception:
        pass

    # 3. Kanal a'zoligini tekshirish
    try:
        member = await bot.get_chat_member(chat_id=config.REQUIRED_CHANNEL_ID, user_id=user_id)
        if member.status in ["creator", "administrator", "member", "restricted"]:
            return True
        return False
    except TelegramBadRequest as e:
        err = str(e).lower()
        if "participant_id_invalid" in err or "user not found" in err:
            return False
        # Agar bot huquqlari yoki chat topilmasa, botni qotirib qo'ymaslik uchun True
        return True
    except Exception:
        return True


def sub_required_kb(target_payload: str = "") -> InlineKeyboardMarkup:
    btn_check_data = f"sub_check:{target_payload}" if target_payload else "sub_check:home"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kanalga a'zo bo'lish ↗️", url=config.REQUIRED_CHANNEL_URL)],
        [InlineKeyboardButton(text="🔄 A'zolikni tekshirish", callback_data=btn_check_data)]
    ])


async def send_sub_required_notice(target: Message | CallbackQuery | int, bot: Bot, payload: str = ""):
    text = (
        "<blockquote>🔒 <b>Seriallarni tomosha qilish uchun rasmiy kanalimizga a'zo bo'ling!</b></blockquote>\n\n"
        f"🎬 <b>@{config.REQUIRED_CHANNEL_USERNAME}</b> kanalimizda barcha yangi premyeralar, "
        "chiqqan qismlar va eng sara doramalar birinchi bo'lib e'lon qilib boriladi.\n\n"
        "<i>Kanalga obuna bo'ling va quyidagi <b>«🔄 A'zolikni tekshirish»</b> tugmasini bosing:</i>"
    )
    kb_markup = sub_required_kb(payload)
    if isinstance(target, int):
        try:
            await bot.send_message(chat_id=target, text=text, reply_markup=kb_markup, parse_mode=ParseMode.HTML)
        except Exception:
            pass
    elif isinstance(target, CallbackQuery):
        try:
            await target.message.answer(text, reply_markup=kb_markup, parse_mode=ParseMode.HTML)
        except Exception:
            pass
    elif isinstance(target, Message):
        try:
            await target.answer(text, reply_markup=kb_markup, parse_mode=ParseMode.HTML)
        except Exception:
            pass


@router.callback_query(F.data.startswith("sub_check:"))
async def cb_sub_check(call: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = call.from_user.id
    payload = call.data.split("sub_check:")[1].strip()

    is_sub = await is_user_channel_member(bot, user_id)
    if not is_sub:
        await safe_answer(call, f"❌ Siz hali @{config.REQUIRED_CHANNEL_USERNAME} kanaliga a'zo bo'lmadingiz. Iltimos, avval kanalga obuna bo'ling!", show_alert=True)
        return

    await safe_answer(call, "✅ Obunangiz tasdiqlandi! Maroqli hordiq tilaymiz.", show_alert=False)

    try:
        await call.message.delete()
    except Exception:
        pass

    if payload.startswith("code_"):
        code_str = payload.replace("code_", "")
        if code_str.isdigit():
            d = await db.get_dorama_by_code(int(code_str))
            if d:
                await show_dorama_detail(call.message, d["id"], bot, user_id=user_id)
                return
    elif payload.startswith("d_"):
        try:
            d_id = int(payload.split("_")[1])
            await show_dorama_detail(call.message, d_id, bot, user_id=user_id)
            return
        except Exception:
            pass
    elif payload.startswith("ep_"):
        try:
            parts = payload.split("_")
            d_id, ep_num = int(parts[1]), int(parts[2])
            await send_episode(user_id, d_id, ep_num, bot)
            return
        except Exception:
            pass

    # Default / home
    is_admin = (user_id == config.ADMIN_ID)
    is_promo = await db.is_promo_free_mode()
    welcome_text = (
        f"{ce('sparkles')} <b>Xush kelibsiz!</b>\n\n"
        f"Kino kodini yozing yoki quyidagi menyudan foydalaning:"
    )
    await call.message.answer(welcome_text, reply_markup=kb.main_menu_kb(is_admin=is_admin, is_promo=is_promo), parse_mode=ParseMode.HTML)


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

                    f"{ce('user')} <b>{html.escape(user.first_name or 'Foydalanuvchi')}</b> sizning havolangiz orqali kirdi.\n"

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

        f"{ce('sparkles')} Assalomu alaykum, <b>{html.escape(user.first_name or 'Foydalanuvchi')}</b>{prem_badge}!\n\n"

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

    is_promo = await db.is_promo_free_mode()
    if is_promo:
        text = text.replace("Quyidagi bo'limlardan birini tanlang:", f"{ce('sparkles')} <b>Aksiya: Hozirda barcha qismlar vaqtinchalik 100% BEPUL!</b>\n\nQuyidagi bo'limlardan birini tanlang:")
    await message.answer(text, reply_markup=kb.main_menu_kb(is_admin=is_admin, is_promo=is_promo), parse_mode=ParseMode.HTML)





async def safe_answer(call: CallbackQuery, text: str = None, show_alert: bool = False):
    """Eskirgan yoki bekor qilingan callback querylarda crash bermaslik uchun xavfsiz answer."""
    try:
        if text is not None:
            clean_text = re.sub(r'<[^>]+>', '', text) if '<' in text else text
            await call.answer(text=clean_text, show_alert=show_alert)
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
        elif "can't parse entities" in str(e).lower():
            clean_text = re.sub(r'<[^>]+>', '', text)
            try:
                await msg.answer(clean_text, reply_markup=reply_markup, parse_mode=None)
            except Exception:
                pass
        else:
            try:
                await msg.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            except Exception:
                clean_text = re.sub(r'<[^>]+>', '', text)
                await msg.answer(clean_text, reply_markup=reply_markup, parse_mode=None)
    except Exception:
        clean_text = re.sub(r'<[^>]+>', '', text)
        try:
            await msg.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except Exception:
            try:
                await msg.answer(clean_text, reply_markup=reply_markup, parse_mode=None)
            except Exception:
                pass





# ---------------------------------------------------------------------------

# Helper: Dorama kartasi va qismlari (Poster bilan)

# ---------------------------------------------------------------------------

async def show_dorama_detail(target: Message | CallbackQuery, dorama_id: int, bot: Bot, user_id: int, page: int = 0):
    if not await is_user_channel_member(bot, user_id):
        await send_sub_required_notice(target, bot, payload=f"d_{dorama_id}")
        return


    d = await db.get_dorama_by_id(dorama_id)

    if not d:

        text = f"{ce('bell')} Kechirasiz, bu dorama topilmadi yoki o'chirilgan."

        if isinstance(target, CallbackQuery):

            await target.answer(text, show_alert=True)

        else:

            await target.answer(text)

        return



    episodes = await db.get_episodes(dorama_id)

    related_seasons = await db.get_related_seasons(dorama_id)

    bot_info = await bot.get_me()



    last_watched = await db.get_last_watched(user_id, dorama_id)

    bookmarked = await db.is_bookmarked(user_id, dorama_id)

    subscribed = await db.is_subscribed(user_id, dorama_id)



    code_badge = f"{ce('code')} <b>Kino kodi:</b> <code>{d.get('code', d['id'])}</code>\n" if d.get('code') else ""

    watched_text = f"{ce('play')} <b>Oxirgi ko'rgan qismingiz:</b> {last_watched}-qism\n" if last_watched else ""



    safe_title = html.escape(str(d.get("title", "")))
    safe_aliases = html.escape(str(d.get("aliases", ""))) if d.get("aliases") else ""
    safe_genre = html.escape(str(d.get("genre", "Romantika")))
    safe_country = html.escape(str(d.get("country", "Janubiy Koreya")))
    safe_actors = html.escape(str(d.get("actors", ""))) if d.get("actors") else ""
    code = d.get("code", d["id"])
    total_ep = d.get("total_episodes") or len(episodes)
    uploaded_ep = len(episodes)
    raw_status = (d.get("status") or "Ongoing").strip()
    status_str = f"{ce('green_circle')} Davom etmoqda" if "ongo" in raw_status.lower() else f"{ce('red_circle')} Tugallangan"

    code_badge = f"{ce('code')} <b>Kino kodi:</b> <code>{code}</code>\n"
    aliases_str = f"{ce('scroll')} <b>Boshqa nomlari:</b> {safe_aliases}\n" if safe_aliases else ""
    actors_str = f"{ce('masks')} <b>Bosh rollarda:</b> {safe_actors}\n" if safe_actors else ""
    country_str = f"{ce('globe')} <b>Davlat:</b> {safe_country}\n" if safe_country else ""
    watched_str = f"{ce('red_circle')} <b>Oxirgi ko'rgan qism:</b> {last_watched}-qism\n" if last_watched else ""

    raw_desc = (d.get("description") or "Qiziqarli dorama voqealari...").strip()
    if len(raw_desc) > 170:
        raw_desc = raw_desc[:165] + "..."
    safe_desc = html.escape(raw_desc)

    caption = (
        f"{ce('film')} <b>{safe_title}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{code_badge}"
        f"{aliases_str}"
        f"{ce('sparkles')} <b>Yili:</b> {d.get('year', 2026)}\n"
        f"{ce('popcorn')} <b>Janr:</b> {safe_genre}\n"
        f"{ce('lightning')} <b>Holati:</b> {status_str}\n"
        f"{ce('tv')} <b>Jami qismlar:</b> {total_ep} ta\n"
        f"{ce('tray')} <b>Yuklangan qismlar:</b> {uploaded_ep} ta\n"
        f"{country_str}"
        f"{actors_str}"
        f"{ce('eyes')} <b>Ko'rishlar:</b> {d.get('views', 0):,} marta\n"
        f"{watched_str}"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{ce('memo')} <i>{safe_desc}</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{ce('scale')} <i>Eslatma: Seriallar reklamalari tarjimonlarga tegishli bo'lib, bot ma'muriyatiga aloqador emas.</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{ce('point_right')} <b>Kerakli qism tugmasini bosib tomosha qiling:</b>"
    )



    markup = kb.dorama_detail_kb(

        dorama_id=dorama_id,

        episodes=episodes,

        bot_username=bot_info.username or "",

        page=page,

        last_watched=last_watched,

        bookmarked=bookmarked,

        subscribed=subscribed,

        related_seasons=related_seasons

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
            err_str = str(e).lower()
            if "message is not modified" in err_str:
                photo_sent = True
            elif "can't parse entities" in err_str:
                logger.warning(f"HTML entity xatoligi ({e}), toza matn rejimiga o'tilmoqda...")
                clean_text = re.sub(r'<[^>]+>', '', caption)
                try:
                    await bot.send_message(chat_id=user_id, text=clean_text, reply_markup=markup, parse_mode=None)
                    photo_sent = True
                except Exception:
                    photo_sent = False
            else:
                logger.warning(f"Rasm yuborishda xatolik ({e}), matn rejimiga o'tilmoqda...")
                photo_sent = False
        except Exception as e:
            logger.warning(f"Rasm yuborishda kutilmagan xatolik ({e}), matn rejimiga o'tilmoqda...")
            photo_sent = False

    if not photo_sent:
        clean_text = re.sub(r'<[^>]+>', '', caption)
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
        except TelegramBadRequest as e:
            if "can't parse entities" in str(e).lower():
                await bot.send_message(chat_id=user_id, text=clean_text, reply_markup=markup, parse_mode=None)
            else:
                await bot.send_message(chat_id=user_id, text=clean_text, reply_markup=markup, parse_mode=None)
        except Exception:
            await bot.send_message(chat_id=user_id, text=clean_text, reply_markup=markup, parse_mode=None)





# ---------------------------------------------------------------------------

# Helper: Qismni yuborish (CopyMessage + protect_content=True)

# ---------------------------------------------------------------------------

async def send_episode(user_id: int, dorama_id: int, ep_num: int, bot: Bot):
    if not await is_user_channel_member(bot, user_id):
        await send_sub_required_notice(user_id, bot, payload=f"ep_{dorama_id}_{ep_num}")
        return


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

            f"{ce('num_1')} <b>Do'stingizni taklif qiling:</b> Havolangiz orqali har bir kirgan do'stingiz navbatdagi qismni ochadi!\n"

            f"{ce('num_2')} <b>VIP A'zolik oling:</b> Atigi 9 000 so'm — barcha qismlarni bir zumda, do'st taklif qilmasdan 1080p sifatda ko'ring.\n"

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
                f"{ce('film')} <b>«{title}»</b>\n"
                f"{ce('play')} <b>{ep_label}</b> • {quality_badge}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"{ce('popcorn')} <i>Yoqimli tomosha!</i>\n\n"

                f"{ce('scale')} <b>Eslatma va ogohlantirish:</b>\n"

                f"<i>Serial ichida paydo bo'ladigan har qanday qimor yoki bukmekerlik reklamalari tarjimon studiyalar tomonidan joylangan bo'lib, bot ma'muriyatiga mutlaqo aloqador emas. Biz qimor va tavakkalchilik o'yinlariga aslo targ'ib qilmaymiz!</i>\n"

                f"━━━━━━━━━━━━━━━━━━\n"

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
# Asosiy Menyu Callback Handlerlari (Bosh Sahifa, Yangi, Top, Sevimlilar)
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "menu_home")
async def cb_menu_home(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user = call.from_user
    prem_badge = f" {ce('crown')} [PREMIUM]" if user.is_premium else ""
    is_admin = (user.id == config.ADMIN_ID)

    text = (
        f"{ce('film')} <b>DORAMA HUB — Bosh Sahifa</b>\n\n"
        f"{ce('sparkles')} <b>{html.escape(user.first_name or 'Foydalanuvchi')}</b>{prem_badge}, quyidagi bo'limlardan birini tanlang:"
    )
    is_promo = await db.is_promo_free_mode()
    await render_text_screen(call, text, reply_markup=kb.main_menu_kb(is_admin=is_admin, is_promo=is_promo))
    await safe_answer(call)


@router.callback_query(F.data.startswith("menu_latest"))
async def cb_menu_latest(call: CallbackQuery):
    page = 0
    if ":" in call.data:
        try:
            page = max(0, int(call.data.split(":")[1]))
        except Exception:
            page = 0
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


@router.callback_query(F.data.startswith("menu_bookmarks") | F.data.startswith("bookmarks:"))
async def cb_menu_bookmarks(call: CallbackQuery):
    user_id = call.from_user.id
    page = 0
    if ":" in call.data:
        try:
            page = max(0, int(call.data.split(":")[1]))
        except Exception:
            page = 0
    all_doramas = await db.get_user_bookmarks(user_id)
    if not all_doramas:
        await safe_answer(call, "Sizda hali saqlangan doramalar yo'q. Dorama kartasidan 'Saqlab qo'yish' tugmasini bosing!", show_alert=True)
        return

    limit = 8
    total = len(all_doramas)
    curr_list = all_doramas[page * limit : (page + 1) * limit]
    has_next = (page + 1) * limit < total

    text = f"{ce('bookmark')} <b>Sizning Sevimli Doramalaringiz (Sahifa {page + 1}):</b>"
    markup = kb.doramas_list_kb(curr_list, prefix="bookmarks", page=page, has_next=has_next)
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

    # Majburiy obunani birinchi navbatda tekshirish
    if not await is_user_channel_member(bot, call.from_user.id):
        await send_sub_required_notice(call, bot, payload=f"ep_{d_id}_{ep_num}")
        return

    unlocked, reason, current_refs, req_refs = await db.is_user_unlocked(call.from_user.id, ep_num, config.ADMIN_ID)
    if not unlocked:
        bot_info = await bot.get_me()
        needed = max(1, req_refs - current_refs)
        await safe_answer(call, f"{ep_num}-qism qulflangan! Yana {needed} ta do'st kerak.", show_alert=True)
        lock_text = (
            f"{ce('lock')} <b>{ep_num}-QISM QULFLANGAN!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Hurmatli <b>{html.escape(call.from_user.first_name or 'Foydalanuvchi')}</b>, 1, 2 va 3-qismlar mutlaqo bepul.\n\n"
            f"{ce('stats')} Sizning takliflaringiz: <b>{current_refs} ta</b>\n"
            f"{ce('target')} <b>{ep_num}-qism uchun talab:</b> <b>{req_refs} ta</b> do'st "
            f"<i>(Yana <b>{needed} ta</b> do'stingiz botga kirishi kerak)</i>.\n\n"
            f"<b>Qulfni ochish yo'llari:</b>\n"
            f"{ce('num_1')} <b>Do'stlarni chaqirish:</b> Har bir do'stingiz yangi qismni bepul ochadi.\n"
            f"{ce('num_2')} <b>VIP A'zolik:</b> 9 000 so'm/oy bilan barcha cheklovlarni bir zumda olib tashlang.\n"
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
    alert = "Sevimlilarga qo'shildi!" if added else "Sevimlilardan olib tashlandi."
    await safe_answer(call, alert, show_alert=True)
    await show_dorama_detail(call, d_id, bot, user_id=call.from_user.id)


@router.callback_query(F.data.startswith("toggle_sub:"))
async def cb_toggle_sub(call: CallbackQuery, bot: Bot):
    d_id = int(call.data.split(":")[1])
    subbed = await db.toggle_subscription(call.from_user.id, d_id)
    alert = "Bildirishnoma yoqildi! Yangi qism chiqishi bilan xabar beramiz." if subbed else "Bildirishnoma o'chirildi."
    await safe_answer(call, alert, show_alert=True)
    await show_dorama_detail(call, d_id, bot, user_id=call.from_user.id)


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

        f"{ce('sparkles')} <b>{html.escape(user.first_name or 'Foydalanuvchi')}</b>{prem_badge}, quyidagi bo'limlardan birini tanlang:"

    )

    try:

        clean_msg = await message.answer("ㅤ", reply_markup=ReplyKeyboardRemove())

        await clean_msg.delete()

    except Exception:

        pass

    is_promo = await db.is_promo_free_mode()
    if is_promo:
        text += f"\n\n{ce('gift')} <i>Hozirda barcha kinolar va seriallar 100% BEPUL!</i>"
    await message.answer(text, reply_markup=kb.main_menu_kb(is_admin=is_admin, is_promo=is_promo), parse_mode=ParseMode.HTML)







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
@router.message(Command("vip_plans"))
@router.message(F.text.in_(["👑 VIP A'zolik", "VIP A'zolik", "VIP"]))
async def handle_vip_trigger(message: Message, state: FSMContext):
    await state.clear()
    is_promo = await db.is_promo_free_mode()
    if is_promo:
        text = (
            f"{ce('party')} <b>MAXSUS AKSIYA: BARCHA QISMLAR 100% BEPUL!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{ce('gift')} Hozirda botimizda barcha serial va kinolarning <b>barcha qismlari mutlaqo bepul</b> ochilgan!\n\n"
            f"{ce('check_green')} Do'st taklif qilish shart emas\n"
            f"{ce('check_green')} Hech qanday VIP to'lovi talab qilinmaydi\n"
            f"{ce('check_green')} 1-qismdan oxirgi qismgacha barchasi cheklovsiz ochiq!\n\n"
            f"<i>Botimizdan maroqli foydalaning va sevimli kinolaringizdan zavqlaning! {ce('popcorn')}</i>"
        )
        await message.answer(text, reply_markup=kb.promo_free_kb(), parse_mode=ParseMode.HTML)
        return

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
        f"{ce('diamond')} <b>VIP obuna muddatini tanlang:</b>\n\n"
        f"<blockquote>VIP obunachilar majburiy obunasiz, do'st chaqirmasdan va yopiq dramalarni 1080p Full HD sifatda cheklovsiz ko'radi.</blockquote>\n\n"
        f"{ce('user')} Sizning holatingiz: <b>{vip_status_text}</b>"
    )
    await message.answer(text, reply_markup=kb.vip_plans_kb(), parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "menu_vip")
async def cb_menu_vip(call: CallbackQuery, state: FSMContext):
    await state.clear()
    is_promo = await db.is_promo_free_mode()
    if is_promo:
        text = (
            f"{ce('party')} <b>MAXSUS AKSIYA: BARCHA QISMLAR 100% BEPUL!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{ce('gift')} Hozirda botimizda barcha serial va kinolarning <b>barcha qismlari mutlaqo bepul</b> ochilgan!\n\n"
            f"{ce('check_green')} Do'st taklif qilish shart emas\n"
            f"{ce('check_green')} Hech qanday VIP to'lovi talab qilinmaydi\n"
            f"{ce('check_green')} 1-qismdan oxirgi qismgacha barchasi cheklovsiz ochiq!\n\n"
            f"<i>Botimizdan maroqli foydalaning va sevimli kinolaringizdan zavqlaning! {ce('popcorn')}</i>"
        )
        await render_text_screen(call, text, reply_markup=kb.promo_free_kb())
        await safe_answer(call)
        return

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
        f"{ce('diamond')} <b>VIP obuna muddatini tanlang:</b>\n\n"
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

        f"<b>To'lov usuli:</b>\n"
        f"{ce('card')} <b>Visa / Humo / Uzcard / Click / Payme:</b>\n"
        f"💳 Karta raqami: <code>4916 9903 7054 4030</code>\n"
        f"{ce('user')} Qabul qiluvchi: <b>Visa</b>\n\n"

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

    if user_id != config.ADMIN_ID and user_id != 7141955036:

        if isinstance(event, CallbackQuery):

            await event.answer("Siz admin emassiz!", show_alert=True)

        else:

            await event.answer(f"{ce('warning')} Siz admin emassiz!")

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

            f"   └ {ce('tray')} Yuklangan: <b>{d['uploaded_episodes']} ta</b> qism\n"

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

    if user_id != config.ADMIN_ID and user_id != 7141955036:

        if isinstance(event, CallbackQuery):

            await event.answer("Siz admin emassiz!", show_alert=True)

        else:

            await event.answer(f"{ce('warning')} Siz admin emassiz!")

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



    promo_status = await db.get_promo_status()
    st_text = f"{ce('green_circle')} FAOL (Barcha qismlar bepul)" if promo_status["is_active"] else f"{ce('red_circle')} O'CHIRILGAN (VIP talab qilinadi)"
    text += f"\n🎁 <b>Aksiya Rejimi:</b> {st_text} ({promo_status['user_count']}/{promo_status['min_users']} ta)\n\nQuyidagi amallardan birini tanlang:"
    await render_text_screen(event, text, reply_markup=kb.admin_panel_kb(promo_info=promo_status))

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

        await message.answer(f"{ce('warning')} Format noto'g'ri! Masalan: <code>/vip 123456789 30</code>")

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

            f"{ce('calendar')} Amal qilish muddati: <b>{until}</b>\n"

            f"{ce('sparkles')} Barcha qismlar qulflarsiz, do'st taklif qilmasdan ochiq."

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

    status_msg = await message.answer(f"{ce('loading')} Ommaviy xabar yuborilmoqda ({len(user_ids)} kishiga)...")



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







@router.message(Command("promo"))
async def handle_promo_command(message: Message):
    if message.from_user.id != config.ADMIN_ID and message.from_user.id != 7141955036:
        return
    parts = (message.text or "").split()
    if len(parts) > 1:
        arg = parts[1].lower()
        if arg in ("on", "yoq", "1"):
            await db.set_system_setting("promo_free_override", "1")
            await message.answer(f"{ce('check_green')} <b>Aksiya rejimi majburiy YOQILDI (Barcha qismlar 100% bepul)!</b>")
        elif arg in ("off", "ochir", "0"):
            await db.set_system_setting("promo_free_override", "0")
            await message.answer(f"{ce('cross_red')} <b>Aksiya rejimi O'CHIRILDI (VIP va do'st chaqirish paywall yoqildi)!</b>")
        elif arg in ("auto", "avto"):
            await db.set_system_setting("promo_free_override", "auto")
            await message.answer(f"{ce('sparkles')} <b>Aksiya rejimi AVTO rejimga o'tkazildi (100+ odamgacha bepul)!</b>")
        elif arg.isdigit():
            await db.set_system_setting("min_users_for_vip", arg)
            await message.answer(f"{ce('target')} <b>VIP yoqilish chegarasi {arg} ta foydalanuvchiga o'zgartirildi!</b>")
    else:
        st = await db.get_promo_status()
        st_text = f"{ce('green_circle')} FAOL (Barcha qismlar bepul)" if st["is_active"] else f"{ce('red_circle')} O'CHIRILGAN (VIP talab qilinadi)"
        await message.answer(
            f"{ce('diamond')} <b>AKSIYA REJIMI STATISTIKASI:</b>\n\n"
            f"Holati: <b>{st_text}</b>\n"
            f"Rejim: <code>{st['override']}</code> (auto / on / off)\n"
            f"Foydalanuvchilar: <b>{st['user_count']} / {st['min_users']} ta</b>\n\n"
            f"<i>Boshqarish buyruqlari:</i>\n"
            f"• <code>/promo auto</code> — 100+ odamgacha avtomat bepul\n"
            f"• <code>/promo on</code> — majburiy doimiy bepul\n"
            f"• <code>/promo off</code> — VIP paywallni darhol yoqish\n"
            f"• <code>/promo 150</code> — chegarani 150 ta odamga oshirish"
        )


@router.callback_query(F.data == "admin_toggle_promo")
async def cb_admin_toggle_promo(call: CallbackQuery):
    if call.from_user.id != config.ADMIN_ID and call.from_user.id != 7141955036:
        await safe_answer(call, "Siz admin emassiz!", show_alert=True)
        return
    st = await db.get_promo_status()
    new_override = "0" if st["is_active"] else "1"
    await db.set_system_setting("promo_free_override", new_override)
    updated = await db.get_promo_status()
    alert = "Bepul aksiya yoqildi! (Barcha qismlar bepul)" if updated["is_active"] else "VIP paywall yoqildi!"
    await safe_answer(call, alert, show_alert=True)
    
    stats = await db.get_stats()
    st_text = f"{ce('green_circle')} FAOL (Barcha qismlar bepul)" if updated["is_active"] else f"{ce('red_circle')} O'CHIRILGAN (VIP talab qilinadi)"
    text = (
        f"{ce('crown')} <b>ADMIN BOSHQARUV PANELI:</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{ce('sparkles')} <b>Foydalanuvchilar:</b> {stats['total_users']:,} ta (Bugun: +{stats['today_users']})\n"
        f"{ce('film')} <b>Doramalar:</b> {stats['total_doramas']} ta\n"
        f"{ce('tv')} <b>Yuklangan qismlar:</b> {stats['total_episodes']} ta\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{ce('gift')} <b>Aksiya Rejimi:</b> {st_text} ({updated['user_count']}/{updated['min_users']} ta)\n\n"
        f"Quyidagi amallardan birini tanlang:"
    )
    await render_text_screen(call, text, reply_markup=kb.admin_panel_kb(promo_info=updated))


@router.callback_query(F.data == "admin_broadcast_promo")
async def cb_admin_broadcast_promo(call: CallbackQuery, bot: Bot):
    if call.from_user.id != config.ADMIN_ID and call.from_user.id != 7141955036:
        await safe_answer(call, "Siz admin emassiz!", show_alert=True)
        return
    await safe_answer(call, "Aksiya xabari barcha foydalanuvchilarga yuborilmoqda...", show_alert=True)

    user_ids = await db.get_all_user_ids()
    text = (
        f"{ce('party')} <b>MAXSUS AKSIYA: BARCHA QISMLAR 100% BEPUL!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{ce('gift')} Hurmatli foydalanuvchi! Botingizda barcha serial va kinolarning <b>barcha qismlari mutlaqo bepul</b> ochildi!\n\n"
        f"{ce('check_green')} Do'st taklif qilish shart emas\n"
        f"{ce('check_green')} Hech qanday VIP to'lovi talab qilinmaydi\n"
        f"{ce('check_green')} 1-qismdan oxirgi qismgacha barchasi cheklovsiz ochiq!\n\n"
        f"<i>Botimizdan maroqli foydalaning va sevimli kinolaringizdan zavqlaning! {ce('popcorn')}</i>"
    )
    sent_cnt = 0
    for uid in user_ids:
        if uid == call.from_user.id:
            continue
        try:
            await bot.send_message(uid, text, reply_markup=kb.promo_free_kb(), parse_mode=ParseMode.HTML)
            sent_cnt += 1
            await asyncio.sleep(0.04)
        except Exception:
            pass
    await call.message.answer(f"{ce('check_green')} <b>Aksiya xabari {sent_cnt} ta foydalanuvchiga muvaffaqiyatli yetkazildi!</b>")




def execute_git_update() -> tuple[bool, str]:
    """
    GitHub'dan so'nggi yangilanishlarni (git fetch + reset --hard) xavfsiz tortib oladi.
    Foydalanuvchilar ma'lumotlarini (userdata.db) to'liq saqlab,
    yangi doramalar, posterlar va kod bilan benuqson sinxronlaydi.
    """
    base_dir = config.BASE_DIR
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"

    github_token = getattr(config, "GITHUB_TOKEN", "")
    origin_url = f"https://{github_token}@github.com/zephcodeer/uzkdrama-bot.git" if github_token else "https://github.com/zephcodeer/uzkdrama-bot.git"

    # 0. index.lock mavjud bo'lsa tozalash
    lock_file = os.path.join(base_dir, ".git", "index.lock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
        except Exception:
            pass

    # 1. Git mavjudligini tekshirish
    try:
        ver = subprocess.run(["git", "--version"], cwd=base_dir, capture_output=True, text=True, timeout=10, env=env)
        if ver.returncode != 0:
            return False, "Git serverda o'rnatilmagan yoki topilmadi."
    except Exception as e:
        return False, f"Git tekshirishda xatolik: {e}"

    # 2. Origin URL ni o'rnatish
    try:
        subprocess.run(["git", "remote", "set-url", "origin", origin_url], cwd=base_dir, capture_output=True, timeout=10, env=env)
    except Exception as e:
        logger.warning(f"Git remote url o'rnatishda ogohlantirish: {e}")

    # 3. Git fetch origin main
    try:
        fetch_proc = subprocess.run(
            ["git", "fetch", "origin", "main"],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )
        if fetch_proc.returncode != 0:
            err = (fetch_proc.stderr or fetch_proc.stdout or "").strip()
            return False, f"Git fetch xatoligi (kod {fetch_proc.returncode}):\n{err[:400]}"
    except subprocess.TimeoutExpired:
        return False, "Git fetch 30 soniya ichida javob bermadi (Timeout)."
    except Exception as e:
        return False, f"Git fetch kutilmagan xatolik: {e}"

    # 4. Git reset --hard origin/main (userdata.db .gitignore da, mutlaqo tegilmaydi)
    try:
        reset_proc = subprocess.run(
            ["git", "reset", "--hard", "origin/main"],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=20,
            env=env
        )
        if reset_proc.returncode != 0:
            err = (reset_proc.stderr or reset_proc.stdout or "").strip()
            return False, f"Git reset xatoligi (kod {reset_proc.returncode}):\n{err[:400]}"
        stdout = (reset_proc.stdout or "").strip()
    except subprocess.TimeoutExpired:
        return False, "Git reset 20 soniya ichida yakunlanmadi (Timeout)."
    except Exception as e:
        return False, f"Git reset kutilmagan xatolik: {e}"

    # 5. Git log ma'lumotini olish
    try:
        log_proc = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%h - %s (%cd)", "--date=short"],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=10,
            env=env
        )
        commit_info = (log_proc.stdout or "").strip()
    except Exception:
        commit_info = "Noma'lum commit"

    return True, f"Muvaffaqiyatli yangilandi!\n\nSo'nggi versiya: {commit_info}\n\nBot 2 soniyadan so'ng yangi kod va baza bilan qayta ishga tushadi."

@router.message(Command("send"))
async def cmd_admin_send_dorama(message: Message, command: CommandObject, bot: Bot):
    """
    Faqat admin uchun:
    /send <user_id> <code_yoki_nom>
    Masalan: /send 8890746889 301
    Foydalanuvchiga to'g'ridan-to'g'ri 'Allaqachon mavjud' shabloni va tomosha qilish tugmasini yuboradi.
    """
    if message.from_user.id != config.ADMIN_ID and message.from_user.id != 7141955036:
        return
    args = (command.args or "").strip().split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            f"{ce('warning')} <b>Foydalanish:</b> <code>/send &lt;user_id&gt; &lt;kino_kodi&gt;</code>\n"
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
    """
    Faqat admin uchun:
    /msg <user_id> <xabar matni>
    Foydalanuvchiga to'g'ridan-to'g'ri ixtiyoriy xabar yuboradi.
    """
    if message.from_user.id != config.ADMIN_ID and message.from_user.id != 7141955036:
        return
    args = (command.args or "").strip().split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            f"{ce('warning')} <b>Foydalanish:</b> <code>/msg &lt;user_id&gt; &lt;matn&gt;</code>\n"
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
        safe_msg_to_send = html.escape(text_to_send)
        await bot.send_message(
            target_uid,
            f"{ce('broadcast')} <b>Admin xabari:</b>\n━━━━━━━━━━━━━━━━━━\n"
            f"<blockquote>{safe_msg_to_send}</blockquote>\n\n"
            f"<i>Maroqli hordiq tilaymiz! {ce('popcorn')}</i>",
            parse_mode=ParseMode.HTML
        )
        await message.answer(f"{ce('check_green')} <b>Xabar foydalanuvchiga ({target_uid}) muvaffaqiyatli yetkazildi!</b>")
    except Exception as e:
        await message.answer(f"{ce('cross_red')} Xatolik: {e}")


@router.message(Command("update"))
async def cmd_admin_update(message: Message, bot: Bot):
    await handle_admin_git_update(message, bot)


@router.callback_query(F.data == "admin_git_update")
async def cb_admin_git_update(call: CallbackQuery, bot: Bot):
    await handle_admin_git_update(call, bot)


async def handle_admin_git_update(event: Message | CallbackQuery, bot: Bot):

    user_id = event.from_user.id

    if user_id != config.ADMIN_ID and user_id != 7141955036:

        if isinstance(event, CallbackQuery):

            await event.answer("Siz admin emassiz!", show_alert=True)

        else:

            await event.answer(f"{ce('warning')} Siz admin emassiz!")

        return



    if isinstance(event, CallbackQuery):

        await event.answer("Yangilanish tekshirilmoqda...")

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

        f"{ce('restart')} <b>Bot 2 soniyada qayta ishga tushadi...</b>",

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


# ========================================================
# DORAMA TAKLIF QILISH BO'LIMI (USER & ADMIN FLOW)
# ========================================================

@router.callback_query(F.data == "menu_suggest")
@router.message(Command("suggest"))
@router.message(Command("taklif"))
async def trigger_dorama_suggestion(event: CallbackQuery | Message, state: FSMContext):
    await state.clear()
    await state.set_state(BotStates.waiting_for_dorama_suggestion)
    text = (
        f"{ce('bulb')} <b>DORAMA TAKLIF QILISH</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Botimizda ko'rmoqchi bo'lgan sevimli Koreys, Xitoy yoki boshqa serial/kinongiz bormi?\n\n"
        f"{ce('memo')} <b>Dorama nomi</b> (yoki u haqidagi ma'lumotni) shu yerga yozib yuboring.\n"
        f"Adminlarimiz taklifingizni ko'rib chiqib, uni eng yuqori sifatda (Full HD) botga joylashga harakat qilishadi! {ce('popcorn')}\n\n"
        f"<i>Bekor qilish uchun /cancel deb yozing.</i>"
    )
    await render_text_screen(event, text, reply_markup=kb.back_to_menu_kb())
    if isinstance(event, CallbackQuery):
        await safe_answer(event)


@router.message(BotStates.waiting_for_dorama_suggestion)
async def process_dorama_suggestion(message: Message, state: FSMContext, bot: Bot):
    suggestion_text = (message.text or message.caption or "").strip()
    if not suggestion_text:
        await message.answer(f"{ce('warning')} Iltimos, dorama nomini matn ko'rinishida yozing.")
        return

    await state.clear()
    u = message.from_user
    sug_id = await db.add_dorama_suggestion(
        user_id=u.id,
        username=u.username,
        first_name=u.first_name,
        suggestion=suggestion_text
    )

    # 1. Foydalanuvchiga minnatdorchilik
    user_reply = (
        f"{ce('check_green')} <b>Katta rahmat! Taklifingiz qabul qilindi.</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Siz taklif qilgan: <b>{html.escape(suggestion_text)}</b>\n\n"
        f"{ce('sparkles')} Adminlarimiz taklifingizni tez orada ko'rib chiqishadi va dorama botga yuklanganda xabar berishadi!\n\n"
        f"<i>Boshqa dorama tomosha qilish uchun pastdagi tugmani bosing:</i>"
    )
    await message.answer(user_reply, reply_markup=kb.back_to_menu_kb(), parse_mode=ParseMode.HTML)

    # 2. Bazadan ushbu dorama bormi-yo'qligini avtomatik tekshirish!
    matches = await db.search_doramas(suggestion_text, limit=1)
    matched_code = matches[0]["code"] if matches else None
    matched_info = ""
    if matches:
        m = matches[0]
        m_eps = await db.get_episodes(m["id"])
        matched_info = f"\n{ce('search')} <b>Bazada topildi:</b> [{m['code']}] {m['title']} ({len(m_eps)}/{m.get('total_episodes', len(m_eps))} qism)\n"

    # 3. Adminga zudlik bilan bildirishnoma yuborish
    admin_targets = list(set([config.ADMIN_ID, 7141955036]))
    safe_u_name = html.escape(u.first_name or "Foydalanuvchi")
    safe_u_user = html.escape(u.username or "username_yoq")
    safe_sug_text = html.escape(suggestion_text)
    admin_notify = (
        f"{ce('bulb')} <b>YANGI DORAMA TAKLIFI #{sug_id}!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{ce('user')} <b>Foydalanuvchi:</b> {safe_u_name} (@{safe_u_user})\n"
        f"{ce('id_badge')} ID: <code>{u.id}</code>\n\n"
        f"{ce('memo')} <b>Taklif qilingan dorama:</b>\n"
        f"<blockquote>{safe_sug_text}</blockquote>\n"
        f"{matched_info}"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Quyidagi tugmalar orqali javob berishingiz mumkin:"
    )
    admin_markup = kb.suggestion_admin_kb(sug_id, u.id, matched_code=matched_code)
    for admin_id in admin_targets:
        try:
            await bot.send_message(admin_id, admin_notify, reply_markup=admin_markup, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.warning(f"Admin {admin_id} ga taklif xabarini yuborishda xato: {e}")


@router.callback_query(F.data.startswith("sug_accept:"))
async def cb_sug_accept(call: CallbackQuery, bot: Bot):
    if call.from_user.id != config.ADMIN_ID and call.from_user.id != 7141955036:
        await safe_answer(call, "Siz admin emassiz!", show_alert=True)
        return
    parts = call.data.split(":")
    sug_id, user_id = int(parts[1]), int(parts[2])
    await db.update_suggestion_status(sug_id, "accepted", "Qabul qilindi")
    await safe_answer(call, "Taklif qabul qilindi va foydalanuvchiga xabar yuborildi!", show_alert=True)

    # Foydalanuvchiga xabar
    try:
        user_msg = (
            f"{ce('party')} <b>Ajoyib yangilik! Dorama taklifingiz qabul qilindi!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Siz taklif qilgan dorama adminlarimiz tomonidan ma'qullandi va tez orada eng yuqori sifatda botga yuklanadi! {ce('popcorn')}\n\n"
            f"<i>Botimizda yangiliklarni kuzatib boring!</i>"
        )
        await bot.send_message(user_id, user_msg, reply_markup=kb.promo_free_kb(), parse_mode=ParseMode.HTML)
    except Exception:
        pass

    try:
        await call.message.edit_text(call.message.text + f"\n\n{ce('check_green')} <b>[ADMIN: QABUL QILINDI]</b>", parse_mode=ParseMode.HTML)
    except Exception:
        pass


@router.callback_query(F.data.startswith("sug_reject:"))
async def cb_sug_reject(call: CallbackQuery):
    if call.from_user.id != config.ADMIN_ID and call.from_user.id != 7141955036:
        await safe_answer(call, "Siz admin emassiz!", show_alert=True)
        return
    parts = call.data.split(":")
    sug_id = int(parts[1])
    await db.update_suggestion_status(sug_id, "rejected", "Rad etildi")
    await safe_answer(call, "Taklif rad etildi deb belgilandi.", show_alert=True)
    try:
        await call.message.edit_text(call.message.text + f"\n\n{ce('cross_red')} <b>[ADMIN: RAD ETILDI]</b>", parse_mode=ParseMode.HTML)
    except Exception:
        pass


@router.callback_query(F.data.startswith("sug_reply:"))
async def cb_sug_reply(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != config.ADMIN_ID and call.from_user.id != 7141955036:
        await safe_answer(call, "Siz admin emassiz!", show_alert=True)
        return
    parts = call.data.split(":")
    sug_id, user_id = int(parts[1]), int(parts[2])
    await state.set_state(BotStates.waiting_for_suggestion_reply)
    await state.update_data(reply_sug_id=sug_id, reply_user_id=user_id)
    await call.message.answer(
        f"{ce('memo')} Foydalanuvchiga yubormoqchi bo'lgan javob xabaringizni yozing:\n"
        f"<i>Bekor qilish uchun /cancel deb yozing.</i>",
        parse_mode=ParseMode.HTML
    )
    await safe_answer(call)


async def send_dorama_exists_notification(bot: Bot, user_id: int, sug_id: int, d: dict):
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

    safe_exists_title = html.escape(str(d.get('title', '')))
    user_msg = (
        f"Assalomu alaykum! <b>«{safe_exists_title}»</b> doramasi allaqachon botimizda mavjud! 🎉\n\n"
        f"🔑 <b>Kino kodi:</b> <code>{code}</code>\n"
        f"🎞 <b>Mavjud:</b> {ep_info}.\n\n"
        f"Botga <b>{code}</b> deb yozib yoki qidiruv orqali bemalol tomosha qilishingiz mumkin. Maroqli hordiq tilaymiz! 🎬🍿"
    )

    play_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎬 Doramani tomosha qilish", icon_custom_emoji_id="5348125953090403204",
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
                call.message.text + f"\n\n{ce('check_green')} <b>[ADMIN: ALLAQACHON MAVJUD ({code}-KOD) DEB JAVOB YUBORILDI]</b>",
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
        f"{ce('number')} <b>Ushbu dorama botimizda qaysi kod ostida mavjud?</b>\n\n"
        f"Kino kodini yozib yuboring (masalan: <code>168</code>):\n"
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
                f"{ce('broadcast')} <b>Dorama taklifingiz bo'yicha Admin javobi:</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"<blockquote>{reply_text}</blockquote>\n\n"
                f"<i>Maroqli tomosha tilaymiz! {ce('popcorn')}</i>",
                reply_markup=kb.back_to_menu_kb(),
                parse_mode=ParseMode.HTML
            )
            await message.answer(f"{ce('check_green')} <b>Javob foydalanuvchiga muvaffaqiyatli yetkazildi!</b>")
            if sug_id:
                await db.update_suggestion_status(sug_id, "replied", reply_text)
        except Exception as e:
            await message.answer(f"{ce('cross_red')} Foydalanuvchiga xabar yetkazib bo'lmadi: {e}")


@router.callback_query(F.data == "admin_suggestions_list")
async def cb_admin_suggestions_list(call: CallbackQuery):
    if call.from_user.id != config.ADMIN_ID and call.from_user.id != 7141955036:
        await safe_answer(call, "Siz admin emassiz!", show_alert=True)
        return
    suggs = await db.get_dorama_suggestions(limit=25)
    if not suggs:
        await render_text_screen(
            call,
            f"{ce('info')} Hozircha foydalanuvchilar tomonidan hech qanday dorama taklifi yuborilmagan.",
            reply_markup=kb.back_to_menu_kb()
        )
        await safe_answer(call)
        return

    text = (
        f"{ce('clipboard')} <b>FOYDALANUVCHILAR TAKLIFLARI ({len(suggs)} ta):</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Quyidagi ro'yxatdan kerakli taklifni tanlab, unga javob berishingiz yoki qabul qilishingiz mumkin:"
    )
    await render_text_screen(call, text, reply_markup=kb.suggestions_list_kb(suggs))
    await safe_answer(call)


@router.callback_query(F.data.startswith("view_sug:"))
async def cb_view_suggestion(call: CallbackQuery):
    if call.from_user.id != config.ADMIN_ID and call.from_user.id != 7141955036:
        await safe_answer(call, "Siz admin emassiz!", show_alert=True)
        return
    sug_id = int(call.data.split(":")[1])
    s = await db.get_dorama_suggestion(sug_id)
    if not s:
        await safe_answer(call, "Taklif topilmadi!", show_alert=True)
        return

    st_map = {"pending": "Kutilmoqda", "accepted": "Qabul qilingan", "rejected": "Rad etilgan", "replied": "Javob berilgan"}
    st_text = st_map.get(s.get('status'), s.get('status'))
    text = (
        f"{ce('bulb')} <b>TAKLIF TAFSILOTLARI #{s['id']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{ce('user')} <b>Foydalanuvchi:</b> {s['first_name']} (@{s['username'] or 'yoq'})\n"
        f"{ce('id_badge')} ID: <code>{s['user_id']}</code>\n"
        f"{ce('calendar')} Sana: <code>{s['created_at']}</code>\n"
        f"Holati: <b>{st_text}</b>\n\n"
        f"{ce('memo')} <b>Taklif:</b>\n"
        f"<blockquote>{s['suggestion']}</blockquote>"
    )
    if s.get("admin_response"):
        text += f"\n\n{ce('broadcast')} <b>Admin javobi:</b>\n<blockquote>{s['admin_response']}</blockquote>"

    await render_text_screen(call, text, reply_markup=kb.suggestion_admin_kb(s['id'], s['user_id']))
    await safe_answer(call)



# ========================================================
# STATISTIKA BO'LIMI (JONLI STATISTIKA)
# ========================================================

async def _render_statistics_screen(event: CallbackQuery | Message):
    stats = await db.get_stats()
    promo = await db.get_promo_status()
    st_active = f"{ce('check_green')} FAOL (100% Bepul)" if promo["is_active"] else f"{ce('lock')} VIP Paywall Faol"

    text = (
        f"{ce('stats')} <b>DORAMA HUB — JONLI STATISTIKA</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{ce('friends')} <b>Foydalanuvchilar:</b>\n"
        f"• Jami a'zolar: <b>{stats['total_users']:,} ta</b>\n"
        f"• Bugun qo'shilganlar: <b>+{stats['today_users']} ta</b>\n"
        f"• Telegram Premium: <b>{stats.get('premium_users', 0)} ta</b>\n\n"
        f"{ce('action')} <b>Kino va Seriallar:</b>\n"
        f"• Jami doramalar: <b>{stats['total_doramas']} ta</b>\n"
        f"• Yuklangan qismlar: <b>{stats['total_episodes']} ta</b>\n"
        f"• Jami ko'rishlar: <b>{stats.get('total_views', 0):,} marta</b>\n\n"
        f"{ce('gift')} <b>Aksiya Holati:</b>\n"
        f"• Barcha qismlar: <b>{st_active}</b>\n"
        f"• Cheklov me'yori: <b>{promo['user_count']} / {promo['min_users']} ta</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<i>Botimizdan maroqli foydalaning! {ce('popcorn')}</i>"
    )

    await render_text_screen(event, text, reply_markup=kb.stats_kb())
    if isinstance(event, CallbackQuery):
        await safe_answer(event)


@router.callback_query(F.data == "menu_stats")
async def cb_stats(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await _render_statistics_screen(call)


@router.message(Command("stats"))
@router.message(F.text.in_(["📊 Statistika", "Statistika"]))
async def msg_stats(message: Message, state: FSMContext):
    await state.clear()
    await _render_statistics_screen(message)



# ---------------------------------------------------------------------------
# Qidiruv & Kino Kodi Matn Handlerlari (Kino kodi yoki Nom bo'yicha)
# ---------------------------------------------------------------------------

@router.message(StateFilter(None, BotStates.waiting_for_query), F.text, F.text.regexp(r"^\d{1,6}$"))
async def process_numeric_code(message: Message, state: FSMContext, bot: Bot):
    """Foydalanuvchi to'g'ridan-to'g'ri raqam yozganda (Kino Kodi)."""
    await state.clear()
    code = int(message.text.strip())
    d = await db.get_dorama_by_code(code)
    if d:
        if not await is_user_channel_member(bot, message.from_user.id):
            await send_sub_required_notice(message, bot, payload=f"code_{code}")
            return
        await show_dorama_detail(message, d["id"], bot, user_id=message.from_user.id)
    else:
        await message.answer(
            f"{ce('bell')} <b>{code}</b> raqamli dorama topilmadi.\nKodni to'g'ri kiritganingizni tekshiring.",
            reply_markup=kb.back_to_menu_kb(),
            parse_mode=ParseMode.HTML
        )


@router.message(StateFilter(None, BotStates.waiting_for_query), F.text)
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
            if not await is_user_channel_member(bot, message.from_user.id):
                await send_sub_required_notice(message, bot, payload=f"code_{code}")
                return
            await show_dorama_detail(message, d["id"], bot, user_id=message.from_user.id)
            return
        else:
            await message.answer(
                f"{ce('bell')} <b>{code}</b> raqamli dorama topilmadi.\nKodni to'g'ri kiritganingizni tekshiring.",
                reply_markup=kb.back_to_menu_kb(),
                parse_mode=ParseMode.HTML
            )
            return

    # Kamida 2 ta harfdan iborat so'zlarnigina qidirish tekshiruvi
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
            f"{ce('bell')} <b>'{html.escape(query)}'</b> bo'yicha hech narsa topilmadi.\n\n"
            f"{ce('bulb')} <i>Nomini to'g'ri yozganingizni tekshiring yoki kino kodini kiriting (masalan: <code>101</code>).</i>"
        )
        await message.answer(text, reply_markup=kb.back_to_menu_kb(), parse_mode=ParseMode.HTML)
        return

    text = f"{ce('search')} <b>'{html.escape(query)}'</b> bo'yicha topilgan natijalar:"
    markup = kb.doramas_list_kb(results, prefix="search", page=0, has_next=False)
    await message.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)



def get_inline_thumb_url(poster_url: str | None) -> str:
    """GitHub / jsDelivr yuqori tezlikdagi CDN orqali Telegram Inline thumbnail URL tayyorlaydi."""
    if not poster_url:
        return "https://cdn.jsdelivr.net/gh/zephcodeer/uzkdrama-bot@main/posters/code_101.jpg"
    p = poster_url.strip()
    if p.startswith("http://") or p.startswith("https://"):
        return p
    clean_p = p.lstrip("/\\")
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
        desc_line = f"╭────────────\n╰► Qismlar soni: {total_ep} ta ({status_text})"

        msg_text = (
            f'<a href="{thumb}">&#8203;</a>'
            f"🎬 <b>{title}</b>\n\n"
            f"🔑 <b>Kino kodi:</b> <code>{code}</code>\n"
            f"🎞 <b>Qismlar soni:</b> {total_ep} qism\n"
            f"📊 <b>Holati:</b> {status_badge} {status_text}\n"
            f"🎭 <b>Janri:</b> {genre}\n"
            f"🌍 <b>Davlat:</b> {country} ({year})\n"
        )
        if short_desc:
            msg_text += f"\n<i>{short_desc}</i>\n"
        msg_text += f"\n👇 <b>Tomosha qilish uchun pastdagi tugmani bosing:</b>"

        item_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎬 Doramani tomosha qilish", icon_custom_emoji_id="5348125953090403204",
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



# ---------------------------------------------------------------------------
# Admin & Kanal Yangi Qismlar Post Tizimi (/post)
# ---------------------------------------------------------------------------

@router.message(Command("post"))
async def cmd_admin_post_episode(message: Message, command: CommandObject, bot: Bot):
    """Admin buyrug'i: Yangi qismni @uz_kdramalar kanaliga chiroyli post qilib chiqaradi.
    Format: /post <kod> [qism] (masalan: /post 168 7 yoki /post 101)
    """
    if message.from_user.id != config.ADMIN_ID and message.from_user.id != 7141955036:
        return

    args = (command.args or "").strip().split()
    if not args:
        await message.answer(
            "<b>Yangi qismni kanalga chiqarish:</b>\n\n"
            "Format: <code>/post &lt;kino_kodi&gt; [qism_raqami]</code>\n"
            "Masalan:\n"
            "• <code>/post 168 7</code> — 168-doramaning 7-qism posti\n"
            "• <code>/post 101</code> — 101-doramaning oxirgi qismi",
            parse_mode=ParseMode.HTML
        )
        return

    if not args[0].isdigit():
        await message.answer("❌ Kino kodi faqat raqam bo'lishi kerak!")
        return

    code = int(args[0])
    d = await db.get_dorama_by_code(code)
    if not d:
        await message.answer(f"❌ <code>{code}</code> kodli dorama bazada topilmadi!")
        return

    episodes = await db.get_episodes(d["id"])
    if not episodes:
        await message.answer(f"❌ <code>{code}</code> kodli doramaga hali qism yuklanmagan!")
        return

    if len(args) > 1 and args[1].isdigit():
        ep_num = int(args[1])
    else:
        ep_num = max(e["episode_number"] for e in episodes)

    title = d.get("title", "")
    caption = (
        "🔔 <b>Yangi qism yuklandi!</b>\n"
        "<i>(Oʻzbek tilida)</i>\n"
        "————————————\n"
        f"« <b>{title}</b> »\n\n"
        f"<blockquote><b>1-fasl | {ep_num}-qism</b>\n"
        f"🔑 Kodi: <code>{code}</code></blockquote>\n\n"
        "👇 <b>Tomosha qilish uchun pastdagi tugmani bosing:</b>"
    )

    kb_post = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🎬 1–{ep_num} qismgacha ko'rish",
            url=f"https://t.me/uzkdrama_app?start={code}"
        )]
    ])

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

    try:
        if photo_input:
            sent = await bot.send_photo(
                chat_id=config.REQUIRED_CHANNEL_ID,
                photo=photo_input,
                caption=caption,
                reply_markup=kb_post,
                parse_mode=ParseMode.HTML
            )
        else:
            sent = await bot.send_message(
                chat_id=config.REQUIRED_CHANNEL_ID,
                text=caption,
                reply_markup=kb_post,
                parse_mode=ParseMode.HTML
            )
        await message.answer(
            f"✅ <b>{title}</b> ({ep_num}-qism) muvaffaqiyatli kanalga joylandi!\n"
            f"🔗 Post ID: <code>{sent.message_id}</code>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await message.answer(f"❌ Kanalga yuborishda xatolik: {e}")



@router.message(Command("card"))
@router.message(Command("premyera"))
async def cmd_admin_post_card(message: Message, command: CommandObject, bot: Bot):
    """Admin buyrug'i: Doramaning to'liq luxury premyera kartasini (expandable syujet bilan) kanalga chiqaradi.
    Format: /card <kino_kodi_yoki_nom>
    """
    if message.from_user.id != config.ADMIN_ID and message.from_user.id != 7141955036:
        return

    arg = (command.args or "").strip()
    if not arg:
        await message.answer(
            "<b>Dorama Premyera Kartasini kanalga chiqarish:</b>\n\n"
            "Format: <code>/card &lt;kino_kodi_yoki_nom&gt;</code>\n"
            "Masalan: <code>/card 480</code> yoki <code>/card Mukammal ish</code>",
            parse_mode=ParseMode.HTML
        )
        return

    if arg.isdigit():
        d = await db.get_dorama_by_code(int(arg))
    else:
        results = await db.search_doramas(arg, limit=1)
        d = results[0] if results else None

    if not d:
        await message.answer(f"❌ <code>{arg}</code> bo'yicha dorama topilmadi!")
        return

    code = d.get("code") or d.get("id")
    title = html.escape(str(d.get("title", "")))
    orig_title = d.get("original_title") or ""
    sub_title = f"<i>({html.escape(orig_title)})</i>" if orig_title and orig_title.lower() != title.lower() else ""

    c_raw = (d.get("country") or "").lower()
    flag = "🇰🇷" if "kore" in c_raw or "korea" in c_raw else ("🇨🇳" if "xitoy" in c_raw or "china" in c_raw else ("🇯🇵" if "yapon" in c_raw or "japan" in c_raw else "🌏"))
    country_name = d.get("country") or "Osiyo"

    episodes = await db.get_episodes(d["id"])
    ep_count = len(episodes)
    raw_status = (d.get("status") or "").lower()
    is_ongoing = "ongo" in raw_status or "davom" in raw_status

    if is_ongoing:
        status_txt = f"{ep_count} qism (Davom etmoqda) ⏳"
        btn_text = f"🎬 1–{ep_count} qismgacha ko'rish"
    else:
        status_txt = f"{ep_count} qism (To'liq yuklangan) ✅" if ep_count else "Tez kunda"
        btn_text = "🎬 Barcha qismlarni ko'rish"

    year = d.get("year") or 2026
    genre = d.get("genre") or "Drama, Romantika"

    raw_desc = (d.get("description") or "Qiziqarli dorama voqealari...").strip()
    safe_desc = html.escape(raw_desc[:400] + ("..." if len(raw_desc) > 400 else ""))

    caption = (
        f"<blockquote>“<b>{title} 🔥</b>”\n"
        f"{sub_title}</blockquote>\n\n"
        f"► <b>Tili:</b> Oʻzbek tilida\n"
        f"► <b>Davlati:</b> {country_name} {flag}\n"
        f"► <b>Yili:</b> {year}\n"
        f"► <b>Qismlar:</b> {status_txt}\n"
        f"► <b>Janri:</b> {genre}\n"
        f"► <b>Kodi:</b> <code>{code}</code>\n\n"
        f"<blockquote expandable>🎬 <b>Qisqacha syujet:</b>\n"
        f"{safe_desc}</blockquote>\n\n"
        f"👇 <b>Tomosha qilish uchun pastdagi tugmani bosing:</b>"
    )

    kb_card = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=btn_text,
            url=f"https://t.me/uzkdrama_app?start={code}"
        )]
    ])

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

    try:
        if photo_input:
            sent = await bot.send_photo(
                chat_id=config.REQUIRED_CHANNEL_ID,
                photo=photo_input,
                caption=caption,
                reply_markup=kb_card,
                parse_mode=ParseMode.HTML
            )
        else:
            sent = await bot.send_message(
                chat_id=config.REQUIRED_CHANNEL_ID,
                text=caption,
                reply_markup=kb_card,
                parse_mode=ParseMode.HTML
            )
        await message.answer(
            f"✅ <b>{title}</b> premyera kartasi kanalga muvaffaqiyatli joylandi!\n"
            f"🔗 Post ID: <code>{sent.message_id}</code>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")


@router.message(Command("restore_btn"))
async def cmd_admin_restore_button(message: Message, command: CommandObject, bot: Bot):
    """Admin buyrug'i: Kanaldagi har qanday postga yo'qolgan inline tugmani qayta ulaydi.
    Format: /restore_btn <post_id> <kino_kodi>
    Masalan: /restore_btn 24 480
    """
    if message.from_user.id != config.ADMIN_ID and message.from_user.id != 7141955036:
        return

    args = (command.args or "").strip().split()
    if len(args) < 2 or not args[0].isdigit() or not args[1].isdigit():
        await message.answer(
            "<b>Kanal postiga tugma ulash:</b>\n\n"
            "Format: <code>/restore_btn &lt;post_id&gt; &lt;kino_kodi&gt;</code>\n"
            "Masalan: <code>/restore_btn 24 480</code>",
            parse_mode=ParseMode.HTML
        )
        return

    post_id = int(args[0])
    code = int(args[1])
    d = await db.get_dorama_by_code(code)
    if not d:
        await message.answer(f"❌ <code>{code}</code> kodli dorama bazada topilmadi!")
        return

    episodes = await db.get_episodes(d["id"])
    ep_count = len(episodes)
    raw_status = (d.get("status") or "").lower()
    is_ongoing = "ongo" in raw_status or "davom" in raw_status
    btn_text = f"🎬 1–{ep_count} qismgacha ko'rish" if is_ongoing else "🎬 Barcha qismlarni ko'rish"

    kb_restored = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_text, url=f"https://t.me/uzkdrama_app?start={code}")]
    ])

    try:
        await bot.edit_message_reply_markup(
            chat_id=config.REQUIRED_CHANNEL_ID,
            message_id=post_id,
            reply_markup=kb_restored
        )
        await message.answer(
            f"✅ Post <code>{post_id}</code> ga «<b>{d['title']}</b>» tugmasi muvaffaqiyatli ulandi!",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await message.answer(f"❌ Tugma ulashda xatolik: {e}")

@router.edited_channel_post()
async def on_channel_post_edited(message: Message, bot: Bot):
    """Kanalda post tahrirlanganda (masalan Premium emoji qo'yilganda) bot tugmasini avtomatik qayta ulab qo'yadi."""
    if message.chat.id != config.REQUIRED_CHANNEL_ID and message.chat.username != config.REQUIRED_CHANNEL_USERNAME:
        return

    # Agar tugma o'chib ketgan bo'lsa
    if not message.reply_markup or not message.reply_markup.inline_keyboard:
        text = message.caption or message.text or ""
        import re
        match = re.search(r"(?:kod|kodi)[\s:–—\-]+(\d+)", text, re.IGNORECASE)
        if match:
            code = int(match.group(1))
            d = await db.get_dorama_by_code(code)
            if d:
                episodes = await db.get_episodes(d["id"])
                ep_count = len(episodes)
                raw_status = (d.get("status") or "").lower()
                is_ongoing = "ongo" in raw_status
                btn_text = f"🎬 1–{ep_count} qismgacha ko'rish" if is_ongoing else "🎬 Barcha qismlarni ko'rish"
                kb_restored = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=btn_text, url=f"https://t.me/uzkdrama_app?start={code}")]
                ])
                try:
                    await bot.edit_message_reply_markup(
                        chat_id=message.chat.id,
                        message_id=message.message_id,
                        reply_markup=kb_restored
                    )
                except Exception:
                    pass


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

        asyncio.create_task(memory_cleanup_loop())
        await dp.start_polling(bot)

    finally:

        await bot.session.close()





if __name__ == "__main__":

    try:

        asyncio.run(main())

    except (KeyboardInterrupt, SystemExit):

        print("Bot to'xtatildi.")



@router.callback_query(F.data == "ignore")
async def cb_ignore_callback(call: CallbackQuery):
    await safe_answer(call, "Siz hozir shu fasldasiz!")
