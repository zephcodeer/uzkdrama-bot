from datetime import datetime
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

from aiogram import BaseMiddleware, Bot, Dispatcher, F, Router

from aiogram.client.default import DefaultBotProperties

from aiogram.client.session.aiohttp import AiohttpSession

from aiogram.enums import ParseMode

from aiogram.filters import Command, CommandObject, CommandStart, StateFilter

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from aiogram.fsm.context import FSMContext

from aiogram.fsm.state import State, StatesGroup

import sqlite3

import subprocess

from aiogram.types import (
    TelegramObject, CallbackQuery, Message, FSInputFile, ErrorEvent, BotCommand,
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

BOT_START_TIME = datetime.now()


def get_bot_uptime() -> str:
    """Bot ishga tushgandan beri o'tgan vaqtni hisoblash."""
    now = datetime.now()
    delta = now - BOT_START_TIME
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    parts = []
    if days > 0:
        parts.append(f"{days} kun")
    if hours > 0:
        parts.append(f"{hours} soat")
    parts.append(f"{minutes} daqiqa")
    return " ".join(parts) if parts else "yangi ishga tushdi"


class UserActivityMiddleware(BaseMiddleware):
    """Har qanday xabar yoki tugma bosilganda foydalanuvchi faolligini avtomatik yangilash."""
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get("event_from_user")
        if user and not user.is_bot:
            # Referal orqali kirgan yangi a'zolarni cmd_start to'g'ri hisobga olishi uchun touch ni chetlab o'tish
            msg_text = getattr(event, "text", "") or ""
            is_ref = msg_text.startswith("/start ref_") or msg_text.startswith("/start r_")
            if not is_ref:
                asyncio.create_task(db.touch_user_activity(
                    tg_id=user.id,
                    username=user.username or "",
                    first_name=user.first_name or "",
                    is_premium=bool(getattr(user, "is_premium", False))
                ))
        return await handler(event, data)





class BotStates(StatesGroup):

    waiting_for_query = State()

    waiting_for_broadcast = State()

    waiting_for_dorama_suggestion = State()

    waiting_for_suggestion_reply = State()

    waiting_for_suggestion_exist_code = State()

    waiting_for_dorama_feedback = State()





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
    return user_id in config.ADMIN_IDS

async def is_user_channel_member(bot: Bot, user_id: int) -> bool:
    """Foydalanuvchi majburiy kanalda a'zo ekanligini tekshiradi."""
    # 1. Admin har doim to'liq ruxsatga ega
    if is_admin_user(user_id):
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
        if member.status in ["creator", "administrator", "member"]:
            return True
        if member.status == "restricted":
            return bool(getattr(member, "is_member", False))
        return False
    except TelegramBadRequest as e:
        err = str(e).lower()
        if "participant_id_invalid" in err or "user not found" in err:
            return False
        logger.warning("Kanal a'zoligini tekshirib bo'lmadi: %s", e)
        return False
    except Exception:
        logger.exception("Kanal a'zoligini tekshirib bo'lmadi")
        return False


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
    is_admin = is_admin_user(user_id)
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

    is_admin = is_admin_user(user.id)



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

    safe_title = html.escape(str(d.get("title", "")).strip()[:45])
    code = d.get("code", d["id"])
    total_ep = d.get("total_episodes") or len(episodes)
    uploaded_ep = len(episodes)
    raw_status = (d.get("status") or "Ongoing").strip()
    is_ongoing = "ongo" in raw_status.lower() or "davom" in raw_status.lower()
    status_str = f"{ce('ongoing')} Davom etmoqda" if is_ongoing else f"{ce('completed')} Tugallangan"

    code_badge = f"{ce('code')} <b>Kino kodi:</b> <code>{code}</code>\n"

    aliases_str = ""
    raw_aliases = d.get("aliases")
    if raw_aliases:
        clean_alias = str(raw_aliases).split(",")[0].strip()
        if clean_alias and clean_alias.lower() != safe_title.lower():
            aliases_str = f"📜 <b>Boshqa nomi:</b> {html.escape(clean_alias[:35])}\n"

    actors_str = ""
    raw_actors = d.get("actors")
    if raw_actors:
        actors_list = [a.strip() for a in str(raw_actors).split(",") if a.strip()]
        if actors_list:
            actors_str = f"🎭 <b>Bosh rollarda:</b> {html.escape(', '.join(actors_list[:2]))}\n"

    safe_genre = html.escape(str(d.get("genre", "Romantika"))[:30])
    watched_str = f"🔴 <b>Oxirgi ko'rgan qism:</b> {last_watched}-qism\n" if last_watched else ""

    fixed_header = (
        f"{ce('film')} <b>{safe_title}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{code_badge}"
        f"{aliases_str}"
        f"🗓 <b>Yili:</b> {d.get('year', 2026)}\n"
        f"{ce('popcorn')} <b>Janr:</b> {safe_genre}\n"
        f"⚡ <b>Holati:</b> {status_str}\n"
        f"{ce('tv')} <b>Jami qismlar:</b> {total_ep} ta\n"
        f"📥 <b>Yuklangan qismlar:</b> {uploaded_ep} ta\n"
        f"{actors_str}"
        f"{ce('eyes')} <b>Ko'rishlar:</b> {d.get('views', 0):,} marta\n"
        f"{watched_str}"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 <i>"
    )
    fixed_footer = (
        f"</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚖️ <i>Seriallar reklamalari tarjimonlarga tegishli.</i>\n"
        f"{ce('point_right')} <b>Kerakli qism tugmasini bosing:</b>"
    )

    raw_desc = (d.get("description") or "Qiziqarli dorama voqealari...").strip()
    safe_desc = html.escape(raw_desc)

    while len(fixed_header) + len(safe_desc) + len(fixed_footer) > 1010 and len(raw_desc) > 15:
        raw_desc = raw_desc[:-8]
        safe_desc = html.escape(raw_desc.strip()) + "..."

    caption = f"{fixed_header}{safe_desc}{fixed_footer}"



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





    d = await db.get_dorama_by_id(dorama_id)

    title = html.escape(d["title"]) if d else "Dorama"



    episodes = await db.get_episodes(dorama_id)

    # Birlashgan qismlarni (1-2 qism) hisoblash

    display_items = kb.build_display_episodes(episodes)

    current_item = next((it for it in display_items if it['start_ep'] <= ep_num <= it['end_ep']), None)

    

    if current_item:

        ep_label = current_item['label']

        watched_episode = current_item['end_ep']

        next_item = next((it for it in display_items if it['start_ep'] > current_item['end_ep']), None)

        has_next = next_item is not None

        next_ep_target = next_item['start_ep'] if next_item else None

    else:

        ep_label = f"{ep_num}-qism"

        watched_episode = ep_num

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
    else:
        try:
            await db.increment_views(dorama_id)
            await db.save_last_watched(user_id, dorama_id, watched_episode)
        except Exception:
            logger.exception("Video yuborildi, lekin ko'rish tarixi saqlanmadi")






# ---------------------------------------------------------------------------
# Asosiy Menyu Callback Handlerlari (Bosh Sahifa, Yangi, Top, Sevimlilar)
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "menu_home")
async def cb_menu_home(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user = call.from_user
    prem_badge = f" {ce('crown')} [PREMIUM]" if user.is_premium else ""
    is_admin = is_admin_user(user.id)

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

    is_admin = is_admin_user(message.from_user.id)

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
    await db.set_pending_receipt(call.from_user.id, plan_code)



    text = (

        f"{ce('card')} <b>TO'LOV MA'LUMOTLARI: {plan['title'].upper()}</b>\n"

        f"━━━━━━━━━━━━━━━━━━\n"

        f"{ce('cash')} To'lov summasi: <b>{plan['price_str']}</b>\n"

        f"{ce('calendar')} Muddat: <b>{plan['days']} kun</b>\n\n"

        f"<b>To'lov usuli:</b>\n"
        f"{ce('card')} <b>Visa / Humo / Uzcard / Click / Payme:</b>\n"
        f"💳 Karta raqami: <code>{html.escape(config.VIP_CARD_NUMBER)}</code>\n"
        f"{ce('user')} Qabul qiluvchi: <b>{html.escape(config.VIP_CARD_HOLDER)}</b>\n\n"

        f"{ce('camera')} <b>QADAMLAR:</b>\n"

        f"1. Yuqoridagi kartaga <b>{plan['price_str']}</b> o'tkazing.\n"

        f"2. To'lov amalga oshirilgan <b>chek skrinshotini</b> yoki PDF hujjatini to'g'ridan-to'g'ri shu yerga yuboring.\n"

        f"3. Chek tekshirilgach, botingizga darhol VIP maqomi faollashadi!\n\n"

        f"<i>Bekor qilish uchun /cancel yozing.</i>"

    )

    await render_text_screen(call, text, reply_markup=kb.back_to_menu_kb())

    await safe_answer(call)





@router.message(VipStates.waiting_for_receipt, F.photo | F.document)
@router.message(StateFilter(None), F.photo | F.document)

async def process_receipt(message: Message, state: FSMContext, bot: Bot):

    data = await state.get_data()

    plan_code = data.get("plan") or await db.get_pending_receipt(message.from_user.id)
    if plan_code not in VIP_PLANS:
        return
    plan = VIP_PLANS[plan_code]

    await state.clear()



    file_id = message.photo[-1].file_id if message.photo else message.document.file_id

    user = message.from_user



    order_id = await db.create_vip_order(

        user_id=user.id,

        plan=plan_code,

        amount=plan["price"],

        receipt_file_id=file_id

    )
    await db.set_pending_receipt(user.id, None)



    user_msg = (

        f"{ce('check_green')} <b>To'lov chekingiz qabul qilindi! (Buyurtma #{order_id})</b>\n\n"

        f"Tanlangan tarif: <b>{plan['title']}</b> ({plan['price_str']})\n"

        f"Administrator chekni tekshirib, tez orada VIP a'zoligingizni yoqadi "

        f"(odatda 5-15 daqiqa ichida).\n\n"

        f"Sabringiz uchun tashakkur! {ce('popcorn')}"

    )




    admin_caption = (

        f"{ce('bell')} <b>YANGI VIP BUYURTMA #{order_id}</b>\n"

        f"━━━━━━━━━━━━━━━━━━\n"

        f"{ce('user')} Foydalanuvchi: <a href='tg://user?id={user.id}'>{html.escape(user.full_name)}</a>\n"

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
        logger.error("Adminga chek yuborishda xatolik: %s", e)
        await message.answer(
            f"Chekingiz #{order_id} raqam bilan saqlandi, lekin adminga xabar yetmadi. Iltimos, buyurtma raqami bilan adminga murojaat qiling.",
            reply_markup=kb.back_to_menu_kb())
    else:
        await message.answer(user_msg, reply_markup=kb.back_to_menu_kb(), parse_mode=ParseMode.HTML)





@router.callback_query(F.data.startswith("submit_receipt:"))

async def cb_submit_receipt(call: CallbackQuery, state: FSMContext):

    plan_code = call.data.split(":")[1]
    if plan_code not in VIP_PLANS:
        await safe_answer(call, "Noma'lum tarif!", show_alert=True)
        return
    await state.set_state(VipStates.waiting_for_receipt)
    await state.update_data(plan=plan_code)
    await db.set_pending_receipt(call.from_user.id, plan_code)

    text = (

        f"{ce('camera')} Iltimos, to'lov amalga oshirilgan <b>chek skrinshotini (rasm)</b> yoki PDF hujjatini shu yerga yuboring:\n\n"

        f"<i>Bekor qilish uchun /cancel deb yozing.</i>"

    )

    await render_text_screen(call, text, reply_markup=kb.back_to_menu_kb())

    await safe_answer(call)





@router.message(VipStates.waiting_for_receipt, F.text)

async def process_receipt_text_guide(message: Message, state: FSMContext):
    if (message.text or "").strip().lower() == "/cancel":
        await db.set_pending_receipt(message.from_user.id, None)
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=kb.back_to_menu_kb())
        return

    if message.text.startswith("/"):

        return

    await message.answer(

        f"{ce('bell')} Iltimos, to'lov tasdiqlanishi uchun <b>chek skrinshotini (rasm)</b> yoki PDF faylini yuboring.\n"

        f"Bekor qilish uchun /cancel deb yozing.",

        reply_markup=kb.back_to_menu_kb(),

        parse_mode=ParseMode.HTML

    )





@router.message(Command("orders"))
async def pending_vip_orders(message: Message, bot: Bot):
    if not is_admin_user(message.from_user.id):
        return
    orders = await db.get_pending_vip_orders()
    if not orders:
        await message.answer("Kutilayotgan VIP buyurtmalar yo'q.")
        return
    await message.answer(f"Kutilayotgan buyurtmalar: {len(orders)} ta.")
    for order in orders:
        plan = VIP_PLANS.get(order["plan"])
        if not plan:
            continue
        caption = (f"<b>VIP buyurtma #{order['id']}</b>\n"
                   f"Foydalanuvchi: <code>{order['user_id']}</code>\n"
                   f"Tarif: {html.escape(plan['title'])} — {html.escape(plan['price_str'])}")
        markup = kb.admin_order_kb(order['id'], order['user_id'], plan['days'])
        try:
            await bot.send_photo(message.chat.id, order['receipt_file_id'], caption=caption, reply_markup=markup)
        except TelegramBadRequest:
            try:
                await bot.send_document(message.chat.id, order['receipt_file_id'], caption=caption, reply_markup=markup)
            except Exception:
                logger.exception("Buyurtma chekini qayta ko'rsatib bo'lmadi: %s", order['id'])
                await message.answer(caption + "\nChekni ochib bo'lmadi.", reply_markup=markup)


@router.callback_query(F.data.startswith("admin_approve:"))

async def cb_admin_approve(call: CallbackQuery, bot: Bot):

    if not is_admin_user(call.from_user.id):

        await safe_answer(call, "Siz admin emassiz!", show_alert=True)

        return



    parts = call.data.split(":")

    order_id = int(parts[1])

    target_user_id = int(parts[2])

    days = int(parts[3])



    result = await db.resolve_vip_order(order_id, True, VIP_PLANS)
    if result is None:
        await safe_answer(call, "Buyurtma topilmadi yoki avval ko'rib chiqilgan.", show_alert=True)
        return
    target_user_id, days = result



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

    if not is_admin_user(call.from_user.id):

        await safe_answer(call, "Siz admin emassiz!", show_alert=True)

        return



    parts = call.data.split(":")

    order_id = int(parts[1])

    target_user_id = int(parts[2])



    result = await db.resolve_vip_order(order_id, False, VIP_PLANS)
    if result is None:
        await safe_answer(call, "Buyurtma topilmadi yoki avval ko'rib chiqilgan.", show_alert=True)
        return
    target_user_id, _ = result



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

    if not is_admin_user(user_id):

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

    if not is_admin_user(user_id):

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





@router.message(Command("setvip"))

async def handle_set_vip_command(message: Message):

    user_id = message.from_user.id

    if not is_admin_user(user_id):

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

    if not is_admin_user(call.from_user.id):

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
    await db.set_pending_receipt(message.from_user.id, None)

    await state.clear()

    await message.answer("Amal bekor qilindi.", reply_markup=kb.main_menu_kb(is_admin=is_admin_user(message.from_user.id)))





@router.message(BotStates.waiting_for_broadcast)

async def process_broadcast(message: Message, state: FSMContext, bot: Bot):

    if not is_admin_user(message.from_user.id):

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

        f"{ce('cross_red')} Yetib bormadi (sabablar turlicha bo'lishi mumkin): <b>{failed}</b> ta"

    )

    await status_msg.edit_text(report, parse_mode=ParseMode.HTML)







@router.message(Command("promo"))
async def handle_promo_command(message: Message):
    if not is_admin_user(message.from_user.id):
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
    if not is_admin_user(call.from_user.id):
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
    if not is_admin_user(call.from_user.id):
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


@router.message(Command("reward_promo", "promo_reward", "finish_promo"))
async def cmd_admin_reward_promo(message: Message, bot: Bot):
    await execute_promo_reward(message, bot)


@router.message(Command("finish_promo"))
async def cmd_admin_finish_promo(message: Message, bot: Bot):
    """Admin buyrug'i: Ilk 100 ta foydalanuvchiga 3 oylik VIP beradi, aksiyani to'xtatadi va xabar yuboradi."""
    await execute_promo_reward(message, bot)


@router.callback_query(F.data == "admin_reward_promo_3m")
async def cb_admin_reward_promo_3m(call: CallbackQuery, bot: Bot):
    await execute_promo_reward(call, bot)


async def execute_promo_reward(event: Message | CallbackQuery, bot: Bot):
    user_id = event.from_user.id
    if not is_admin_user(user_id):
        if isinstance(event, CallbackQuery):
            await safe_answer(event, "Siz admin emassiz!", show_alert=True)
        else:
            await event.answer(f"{ce('warning')} Siz admin emassiz!")
        return

    if isinstance(event, CallbackQuery):
        await safe_answer(event, "Aksiya yakunlanmoqda va 3 oylik VIP berilmoqda...", show_alert=True)
        status_msg = await event.message.answer(
            f"{ce('sparkles')} <b>Mavjud foydalanuvchilarga 3 oylik VIP berilmoqda va aksiya yopilmoqda...</b>\n<i>Iltimos, kuting...</i>",
            parse_mode=ParseMode.HTML
        )
    else:
        status_msg = await event.answer(
            f"{ce('sparkles')} <b>Mavjud foydalanuvchilarga 3 oylik VIP berilmoqda va aksiya yopilmoqda...</b>\n<i>Iltimos, kuting...</i>",
            parse_mode=ParseMode.HTML
        )

    rewarded_count = await db.grant_vip_to_all_existing_users(days=90)
    user_ids = await db.get_all_user_ids()

    reward_text = (
        f"{ce('party')} <b>TABRIKLAYMIZ! SIZ 3 OYLIK BEPUL VIP GA EGA BOʻLDINGIZ!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Hurmatli foydalanuvchi! {ce('sparkles')}\n\n"
        f"Siz botimizning <b>ilk 100 nafar faol foydalanuvchisi</b> aksiyasida ishtirok etib, maxsus mukofot — "
        f"<b>3 OYLIK MUTLAQO BEPUL VIP OBUNA</b> yutib oldingiz! {ce('gift')}\n\n"
        f"{ce('crown')} <b>Sizning VIP imtiyozlaringiz:</b>\n"
        f"✅ Barcha dorama va eng soʻnggi premyerani 1080p Full HD sifatda koʻrish\n"
        f"✅ 1-qismdan oxirgi qismgacha barchasi cheklovsiz ochiq\n"
        f"✅ Doʻst taklif qilish yoki toʻlov qilish mutlaqo talab qilinmaydi\n"
        f"⏳ <b>Amal qilish muddati:</b> 3 oy (90 kun) davomida toʻliq faol!\n\n"
        f"<i>Biz bilan birga boʻlganingiz uchun minnatdormiz! Maroqli hordiq tilaymiz! {ce('popcorn')}</i>"
    )
    kb_reward = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎬 Doramalarni tomosha qilish",
            url="https://t.me/uzkdrama_app"
        )]
    ])

    sent_cnt = 0
    for uid in user_ids:
        if uid == user_id:
            continue
        try:
            await bot.send_message(uid, reward_text, reply_markup=kb_reward, parse_mode=ParseMode.HTML)
            sent_cnt += 1
            await asyncio.sleep(0.04)
        except Exception:
            pass

    res_text = (
        f"{ce('check_green')} <b>AKSIYA MUVAFFAQIYATLI YAKUNLANDI!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎁 <b>3 oylik VIP berildi:</b> <code>{rewarded_count}</code> ta foydalanuvchiga\n"
        f"📨 <b>Tabrik xabari yetkazildi:</b> <code>{sent_cnt}</code> ta foydalanuvchiga\n"
        f"🔒 <b>Aksiya rejimi:</b> OʻCHIRILDI (VIP Paywall faollashtirildi)\n\n"
        f"<i>Bundan keyin botga qoʻshiladigan barcha yangi aʼzolar uchun VIP faqat pullik yoki doʻst taklif qilish orqali boʻladi!</i>"
    )
    await status_msg.edit_text(res_text, parse_mode=ParseMode.HTML)





def execute_git_update() -> tuple[bool, str]:
    """Pull the latest code and doramas catalog from GitHub while preserving userdata.db."""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    def run(*args):
        return subprocess.run(["git", *args], cwd=config.BASE_DIR, env=env,
                              capture_output=True, text=True, timeout=45)
    try:
        # 1. Fetch latest changes from origin
        fetch = run("fetch", "origin", "main")
        if fetch.returncode:
            return False, f"Git fetch bajarilmadi: {fetch.stderr.strip() or 'Ulanish xatosi'}"

        # 2. Check if already up to date
        diff = run("diff", "--name-only", "HEAD", "origin/main")
        if diff.returncode:
            return False, "Git o'zgarishlarini tekshirib bo'lmadi."

        status = run("status", "--porcelain", "--untracked-files=no")
        if not diff.stdout.strip() and not status.stdout.strip():
            return True, "ALREADY_UP_TO_DATE"

        # 3. Cleanly reset tracked catalog/files (e.g. doramas.db views counter or scripts)
        # Note: userdata.db is gitignored/untracked, so it is 100% untouched and safe!
        reset = run("reset", "--hard", "origin/main")
        if reset.returncode:
            return False, f"Git reset bajarilmadi: {reset.stderr.strip()}"

        diff_summary = diff.stdout.strip()
        lines = [l.strip() for l in diff_summary.splitlines() if l.strip()]
        return True, f"Kod va doramalar bazasi muvaffaqiyatli yangilandi ({len(lines)} ta fayl):\n" + "\n".join(lines[:5])
    except (OSError, subprocess.TimeoutExpired) as e:
        logger.exception("Git yangilash xatosi")
        return False, f"Git yangilash ishlamadi: {e}"


async def cmd_admin_send_dorama(message: Message, command: CommandObject, bot: Bot):
    """
    Faqat admin uchun:
    /send <user_id> <code_yoki_nom>
    Masalan: /send 8890746889 301
    Foydalanuvchiga to'g'ridan-to'g'ri 'Allaqachon mavjud' shabloni va tomosha qilish tugmasini yuboradi.
    """
    if not is_admin_user(message.from_user.id):
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
    if not is_admin_user(message.from_user.id):
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


@router.message(Command("send"))
async def cmd_admin_send(message: Message, bot: Bot):
    """
    Admin buyrug'i: Foydalanuvchiga to'g'ridan-to'g'ri kino kodi yoki xabar yuborish.
    Format: /send <user_id> <kino_kodi> yoki /send <user_id> <matn>
    Masalan: /send 8777393066 482
    """
    if not is_admin_user(message.from_user.id):
        return
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"{ce('info')} <b>/send buyrug'idan foydalanish:</b>\n\n"
                 f"1) <b>Kino kodi bilan xabar:</b> <code>/send &lt;user_id&gt; &lt;kino_kodi&gt;</code>\n"
                 f"<i>(Masalan: <code>/send 8777393066 482</code>)</i>\n\n"
                 f"2) <b>Ixtiyoriy matn yuborish:</b> <code>/send &lt;user_id&gt; &lt;xabar matni&gt;</code>\n"
                 f"<i>(Masalan: <code>/send 8777393066 Salom, taklifingiz qabul qilindi!</code>)</i>",
            parse_mode=ParseMode.HTML
        )
        return

    target_id_str, payload = args[1].strip(), args[2].strip()
    if not target_id_str.isdigit():
        await bot.send_message(chat_id=message.chat.id, text=f"{ce('cross_red')} Noto'g'ri foydalanuvchi ID raqami: <code>{target_id_str}</code>", parse_mode=ParseMode.HTML)
        return

    target_user_id = int(target_id_str)

    # 1. Agar dorama kodi yozilgan bo'lsa
    if payload.isdigit():
        code = int(payload)
        d = await db.get_dorama_by_code(code)
        if d:
            title = d.get('title', f'{code}-kodli dorama')
            msg_text = (
                f"{ce('party')} <b>Assalomu alaykum! Dorama taklifingiz yuklandi!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Siz so'ragan/taklif qilgan <b>«{html.escape(title)}»</b> seriali botimizga to'liq joylandi! {ce('popcorn')}\n\n"
                f"{ce('diamond')} <b>Kino kodi:</b> <code>{code}</code>\n\n"
                f"<i>Botga <b>{code}</b> deb yozib yoki pastdagi tugma orqali bemalol tomosha qilishingiz mumkin. Maroqli hordiq tilaymiz!</i> {ce('sparkles')}"
            )
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🎬 Serialni tomosha qilish",
                    url=f"https://t.me/uzkdrama_app?start={code}"
                )]
            ])
            try:
                await bot.send_message(target_user_id, msg_text, reply_markup=markup, parse_mode=ParseMode.HTML)
                await bot.send_message(chat_id=message.chat.id, text=f"{ce('check_green')} Foydalanuvchiga <b>[{code}] {html.escape(title)}</b> seriali haqida bildirishnoma yetkazildi!", parse_mode=ParseMode.HTML)
            except TelegramForbiddenError:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=f"{ce('warning')} <b>Xatolik:</b> Foydalanuvchi botni bloklagan (Forbidden: bot was blocked by the user).\n"
                         f"Foydalanuvchi botni qayta ochmaguncha xabar yetkazib bo'lmaydi.",
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                await bot.send_message(chat_id=message.chat.id, text=f"{ce('cross_red')} Xabar yuborishda xatolik: {e}", parse_mode=ParseMode.HTML)
            return

    # 2. Oddiy matn yuborish
    try:
        custom_msg = (
            f"{ce('broadcast')} <b>Admin xabari:</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{html.escape(payload)}"
        )
        await bot.send_message(target_user_id, custom_msg, parse_mode=ParseMode.HTML)
        await bot.send_message(chat_id=message.chat.id, text=f"{ce('check_green')} Foydalanuvchiga xabar muvaffaqiyatli yetkazildi!", parse_mode=ParseMode.HTML)
    except TelegramForbiddenError:
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"{ce('warning')} <b>Xatolik:</b> Foydalanuvchi botni bloklagan (Forbidden: bot was blocked by the user).",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await bot.send_message(chat_id=message.chat.id, text=f"{ce('cross_red')} Xabar yuborishda xatolik: {e}", parse_mode=ParseMode.HTML)


@router.message(Command("update"))
async def cmd_admin_update(message: Message, bot: Bot):
    await handle_admin_git_update(message, bot)


@router.callback_query(F.data == "admin_git_update")
async def cb_admin_git_update(call: CallbackQuery, bot: Bot):
    await handle_admin_git_update(call, bot)


async def handle_admin_git_update(event: Message | CallbackQuery, bot: Bot):

    user_id = event.from_user.id

    if not is_admin_user(user_id):

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

    is_admin = is_admin_user(message.from_user.id)

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
# DORAMA FIKR BILDIRISH (USER PLAYER FEEDBACK FLOW)
# ========================================================

@router.callback_query(F.data.startswith("dorama_feedback:"))
async def cb_dorama_feedback(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    dorama_id = int(parts[1])
    d = await db.get_dorama_by_id(dorama_id)
    if not d:
        await safe_answer(call, "Dorama topilmadi!", show_alert=True)
        return

    await state.clear()
    await state.set_state(BotStates.waiting_for_dorama_feedback)
    await state.update_data(
        feedback_dorama_id=dorama_id,
        feedback_dorama_title=d["title"],
        feedback_dorama_code=d["code"]
    )

    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="Bekor qilish",
                callback_data=f"view_dorama:{dorama_id}",
                icon_custom_emoji_id=kb.ICON_BACK
            )
        ]]
    )

    text = (
        f"{ce('bulb')} <b>«{html.escape(d['title'])}» haqida fikringiz</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Ushbu film/serial haqidagi taassurotlaringiz, fikringiz yoki izohingizni yozib yuboring.\n\n"
        f"{ce('sparkles')} <i>Fikringiz adminlarimiz va boshqa tomoshabinlar uchun juda qadrli!</i>\n\n"
        f"<i>Bekor qilish uchun /cancel deb yozing yoki pastdagi tugmani bosing.</i>"
    )
    await call.message.answer(text, reply_markup=cancel_kb, parse_mode=ParseMode.HTML)
    await safe_answer(call)


@router.message(BotStates.waiting_for_dorama_feedback)
async def process_dorama_feedback(message: Message, state: FSMContext, bot: Bot):
    feedback_text = (message.text or message.caption or "").strip()
    if feedback_text.lower() in ["/cancel", "bekor qilish"]:
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=kb.main_menu_kb())
        return

    if not feedback_text:
        await message.answer(f"{ce('warning')} Iltimos, fikringizni matn ko'rinishida yozing.")
        return

    data = await state.get_data()
    dorama_id = data.get("feedback_dorama_id")
    title = data.get("feedback_dorama_title", "Noma'lum dorama")
    code = data.get("feedback_dorama_code", "---")
    await state.clear()

    u = message.from_user
    formatted_content = f"[{code}] {title} haqida fikr: {feedback_text}"
    sug_id = await db.add_dorama_suggestion(
        user_id=u.id,
        username=u.username,
        first_name=u.first_name,
        suggestion=formatted_content
    )

    # 1. Foydalanuvchiga minnatdorchilik
    back_markup = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="Doramaga qaytish",
                callback_data=f"view_dorama:{dorama_id}" if dorama_id else "menu_home",
                icon_custom_emoji_id=kb.ICON_SERIES
            ),
            InlineKeyboardButton(
                text="Bosh menyu",
                callback_data="menu_home",
                icon_custom_emoji_id=kb.ICON_HOME
            )
        ]]
    )
    user_reply = (
        f"{ce('check_green')} <b>Katta rahmat! Fikringiz qabul qilindi.</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎬 <b>«{html.escape(title)}»</b> haqidagi fikringiz adminlarimizga yetkazildi.\n\n"
        f"{ce('sparkles')} <i>Biz bilan birga bo'lganingiz uchun tashakkur!</i>"
    )
    await message.answer(user_reply, reply_markup=back_markup, parse_mode=ParseMode.HTML)

    # 2. Adminga zudlik bilan bildirishnoma yuborish
    admin_targets = list(config.ADMIN_IDS)
    safe_u_name = html.escape(u.first_name or "Foydalanuvchi")
    safe_u_user = html.escape(u.username or "username_yoq")
    safe_text = html.escape(feedback_text)
    admin_notify = (
        f"{ce('bulb')} <b>YANGI DORAMA FIKRI / TAQRIZ #{sug_id}!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎬 <b>Dorama:</b> [{code}] {html.escape(title)}\n"
        f"{ce('user')} <b>Foydalanuvchi:</b> {safe_u_name} (@{safe_u_user})\n"
        f"{ce('id_badge')} ID: <code>{u.id}</code>\n\n"
        f"{ce('memo')} <b>Fikr / Izoh:</b>\n"
        f"<blockquote>{safe_text}</blockquote>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Foydalanuvchiga javob berish uchun pastdagi tugmadan foydalanishingiz mumkin:"
    )
    admin_markup = kb.suggestion_admin_kb(sug_id, u.id, matched_code=code)
    for admin_id in admin_targets:
        try:
            await bot.send_message(admin_id, admin_notify, reply_markup=admin_markup, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.warning(f"Admin {admin_id} ga dorama fikrini yuborishda xato: {e}")


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
    admin_targets = list(config.ADMIN_IDS)
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
    if not is_admin_user(call.from_user.id):
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
    if not is_admin_user(call.from_user.id):
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
    if not is_admin_user(call.from_user.id):
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
    if not is_admin_user(call.from_user.id):
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
    if not is_admin_user(call.from_user.id):
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
    if not is_admin_user(message.from_user.id):
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
    if not is_admin_user(message.from_user.id):
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


@router.callback_query(F.data.in_({"admin_suggestions", "admin_suggestions_list"}))
async def cb_admin_suggestions_list(call: CallbackQuery):
    if not is_admin_user(call.from_user.id):
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
    if not is_admin_user(call.from_user.id):
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
        f"{ce('user')} <b>Foydalanuvchi:</b> {html.escape(s['first_name'] or '')} (@{html.escape(s['username'] or 'yoq')})\n"
        f"{ce('id_badge')} ID: <code>{s['user_id']}</code>\n"
        f"{ce('calendar')} Sana: <code>{s['created_at']}</code>\n"
        f"Holati: <b>{st_text}</b>\n\n"
        f"{ce('memo')} <b>Taklif:</b>\n"
        f"<blockquote>{html.escape(s['suggestion'] or '')}</blockquote>"
    )
    if s.get("admin_response"):
        text += f"\n\n{ce('broadcast')} <b>Admin javobi:</b>\n<blockquote>{html.escape(s['admin_response'])}</blockquote>"

    await render_text_screen(call, text, reply_markup=kb.suggestion_admin_kb(s['id'], s['user_id']))
    await safe_answer(call)



# ========================================================
# STATISTIKA BO'LIMI (JONLI STATISTIKA)
# ========================================================

async def _render_statistics_screen(event: CallbackQuery | Message):
    user_id = event.from_user.id
    is_admin = is_admin_user(user_id)

    promo = await db.get_promo_status()
    st_active = f"{ce('check_green')} FAOL (100% Bepul)" if promo["is_active"] else f"{ce('lock')} VIP Paywall Faol"

    if is_admin:
        s = await db.get_admin_detailed_stats()
        uptime_str = get_bot_uptime()

        # Top 5 eng ko'p ko'rilgan seriallar
        top_list_str = ""
        if s["top_doramas"]:
            for idx, item in enumerate(s["top_doramas"], 1):
                d_code, d_title, d_views = item
                clean_title = d_title.split("(")[0].strip()[:24]
                top_list_str += f"  {idx}. <b>{html.escape(clean_title)}</b> (<code>{d_code}</code>) — <b>{d_views:,}</b> ko'rish\n"
        else:
            top_list_str = "  <i>Hozircha ma'lumot yo'q</i>\n"

        # Top referallarni formatlash
        ref_list_str = ""
        if s["top_referrers"]:
            for idx, r in enumerate(s["top_referrers"], 1):
                r_id, r_user, r_name, r_cnt = r
                uname = f"@{r_user}" if r_user else html.escape(r_name or str(r_id))
                ref_list_str += f"  {idx}. {uname} — <b>{r_cnt} ta</b> do'st\n"

        # RAM sarfi
        ram_str = f"{s['ram_used_mb']:,} MB / {s['ram_total_mb']:,} MB ({s['ram_percent']}%)" if s['ram_total_mb'] else "N/A"
        bot_ram_str = f"{s['bot_ram_mb']} MB" if s['bot_ram_mb'] else "N/A"

        text = (
            f"{ce('stats')} <b>BOSH ADMIN — BOSHQARUV STATISTIKASI</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{ce('friends')} <b>Foydalanuvchilar Faolligi:</b>\n"
            f"• Jami a'zolar: <b>{s['total_users']:,} ta</b>\n"
            f"• 🟢 Faol (so'nggi 24 soat): <b>{s['active_24h']:,} ta</b> (DAU)\n"
            f"• 🟡 Faol (so'nggi 7 kun): <b>{s['active_7d']:,} ta</b> (WAU)\n"
            f"• 🔵 Faol (so'nggi 30 kun): <b>{s['active_30d']:,} ta</b> (MAU)\n\n"
            f"{ce('fire')} <b>O'sish Ko'rsatkichlari:</b>\n"
            f"• Bugun qo'shilganlar: <b>+{s['joined_today']} ta</b>\n"
            f"• Hafta davomida: <b>+{s['joined_7d']} ta</b>\n"
            f"• Oy davomida: <b>+{s['joined_30d']} ta</b>\n\n"
            f"{ce('diamond')} <b>Monetizatsiya & Segment:</b>\n"
            f"• Telegram Premium: <b>{s['premium_users']:,} ta</b>\n"
            f"• VIP a'zolar: <b>{s['vip_users']:,} ta</b>\n"
            f"• Do'st taklifi orqali: <b>{s['referred_users']:,} ta</b>\n"
            + (f"• Yetakchilar:\n{ref_list_str}\n" if ref_list_str else "\n") +
            f"{ce('action')} <b>Kontent & Auditoriya:</b>\n"
            f"• Jami doramalar: <b>{s['total_doramas']} ta</b>\n"
            f"• Yuklangan qismlar: <b>{s['total_episodes']} ta</b>\n"
            f"• Jami ko'rishlar: <b>{s['total_views']:,} marta</b>\n"
            f"• Saqlanganlar (Bookmarks): <b>{s['total_bookmarks']:,} ta</b>\n"
            f"• Obunachilar: <b>{s['total_subscribers']:,} ta</b>\n\n"
            f"{ce('star')} <b>Eng Ko'p Ko'rilgan Top-5:</b>\n"
            f"{top_list_str}\n"
            f"{ce('bulb')} <b>Takliflar & Fikrlar:</b>\n"
            f"• Jami kelgan: <b>{s['total_suggestions']} ta</b>\n"
            f"• ⏳ Kutilayotgan: <b>{s['pending_suggestions']} ta</b>\n"
            f"• ✅ Qabul qilingan: <b>{s['approved_suggestions']} ta</b>\n\n"
            f"{ce('settings')} <b>Server & Tizim Holati:</b>\n"
            f"• Server RAM: <b>{ram_str}</b>\n"
            f"• Bot RAM sarfi: <b>{bot_ram_str}</b>\n"
            f"• Kontent bazasi (doramas.db): <b>{s['doramas_db_size']} MB</b>\n"
            f"• Foydalanuvchilar (userdata.db): <b>{s['userdata_db_size']} MB</b>\n"
            f"• Uptime: <b>{uptime_str}</b>\n"
            f"• Aksiya holati: <b>{st_active}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<i>Ma'lumotlar jonli SQLite bazasidan yangilandi.</i>"
        )
        markup = kb.admin_stats_kb()
    else:
        stats = await db.get_stats()
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
        markup = kb.stats_kb()

    await render_text_screen(event, text, reply_markup=markup)
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

@router.callback_query(F.data.startswith("search:"))
async def cb_search_page(call: CallbackQuery, state: FSMContext):
    try:
        page = max(0, int(call.data.split(":", 1)[1]))
    except ValueError:
        await safe_answer(call, "Sahifa topilmadi.")
        return
    query = (await state.get_data()).get("search_query")
    if not query:
        await safe_answer(call, "Iltimos, qayta qidiring.", show_alert=True)
        return
    results = await db.search_doramas(query, limit=11, offset=page * 10)
    text = f"{ce('search')} <b>'{html.escape(query)}' bo'yicha natijalar (sahifa {page + 1}):</b>"
    await render_text_screen(call, text, reply_markup=kb.doramas_list_kb(results[:10], prefix="search", page=page, has_next=len(results) > 10))
    await safe_answer(call)


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

    results = await db.search_doramas(query, limit=11)
    if not results:
        text = (
            f"{ce('bell')} <b>'{html.escape(query)}'</b> bo'yicha hech narsa topilmadi.\n\n"
            f"{ce('bulb')} <i>Nomini to'g'ri yozganingizni tekshiring yoki kino kodini kiriting (masalan: <code>101</code>).</i>"
        )
        await message.answer(text, reply_markup=kb.back_to_menu_kb(), parse_mode=ParseMode.HTML)
        return

    text = f"{ce('search')} <b>'{html.escape(query)}'</b> bo'yicha topilgan natijalar:"
    await state.update_data(search_query=query)
    markup = kb.doramas_list_kb(results[:10], prefix="search", page=0, has_next=len(results) > 10)
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
    if not is_admin_user(message.from_user.id):
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

    ep_text = None
    btn_text = None
    if len(args) > 1:
        raw_ep = args[1].strip()
        if raw_ep.isdigit():
            ep_num = int(raw_ep)
            ep_text = f"{ep_num}-qism"
            btn_text = f"🎬 1–{ep_num} qismgacha ko'rish"
        elif "-" in raw_ep:
            parts = raw_ep.split("-")
            if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
                ep_text = f"{parts[0].strip()}–{parts[1].strip()}-qismlar"
                btn_text = f"🎬 {parts[0].strip()}–{parts[1].strip()} qismlarni ko'rish"
                ep_num = int(parts[1].strip())
    if not ep_text:
        ep_num = max(e["episode_number"] for e in episodes)
        ep_text = f"{ep_num}-qism"
        btn_text = f"🎬 1–{ep_num} qismgacha ko'rish"

    title = d.get("title", "")
    caption = (
        "🔔 <b>Yangi qism yuklandi!</b>\n"
        "<i>(Oʻzbek tilida)</i>\n"
        "————————————\n"
        f"« <b>{title}</b> »\n\n"
        f"<blockquote><b>1-fasl | {ep_text}</b>\n"
        f"🔑 Kodi: <code>{code}</code></blockquote>\n\n"
        "👇 <b>Tomosha qilish uchun pastdagi tugmani bosing:</b>"
    )

    kb_post = InlineKeyboardMarkup(inline_keyboard=[
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
            f"✅ <b>{title}</b> ({ep_text}) muvaffaqiyatli kanalga joylandi!\n"
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
    if not is_admin_user(message.from_user.id):
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
    if not is_admin_user(message.from_user.id):
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
    dp.message.outer_middleware(UserActivityMiddleware())
    dp.callback_query.outer_middleware(UserActivityMiddleware())
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

            admin_commands = commands + [
            BotCommand(command="orders", description="💳 Kutilayotgan VIP buyurtmalar"),
            BotCommand(command="update", description="🚀 GitHub'dan yangilash"),
            BotCommand(command="card", description="🎴 Dorama kartasini kanalga joylash"),
            BotCommand(command="post", description="🔔 Yangi qismni kanalga chiqarish"),
            BotCommand(command="finish_promo", description="🎁 100 ta a'zoga 3 oylik VIP berish & Aksiyani yopish"),
            BotCommand(command="restore_btn", description="🛠 Kanal postlariga tugma ulash"),
            BotCommand(command="ongoing", description="🟢 Davom etayotgan seriallar")
        ]

            await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=config.ADMIN_ID))

        except Exception as e:

            logger.warning(f"Admin buyruqlarini sozlashda ogohlantirish: {e}")



    except Exception as e:

        logger.warning(f"Menyu tugmasini sozlashda xatolik: {e}")



    try:

        await bot.delete_webhook(drop_pending_updates=False)

        asyncio.create_task(memory_cleanup_loop())
        await dp.start_polling(bot)

    finally:

        await bot.session.close()





@router.callback_query(F.data == "ignore")
async def cb_ignore_callback(call: CallbackQuery):
    await safe_answer(call, "Siz hozir shu fasldasiz!")


if __name__ == "__main__":

    try:

        asyncio.run(main())

    except (KeyboardInterrupt, SystemExit):

        print("Bot to'xtatildi.")




