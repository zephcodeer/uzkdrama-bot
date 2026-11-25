import asyncio
import logging
import html
import os
from typing import List, Optional

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.exceptions import (
    TelegramRetryAfter,
    TelegramForbiddenError,
    TelegramBadRequest,
    TelegramAPIError,
)

import config
from emojis import ce

logger = logging.getLogger(__name__)

__all__ = ["notify_subscribers_async", "TelegramRetryAfter"]


def _resolve_photo_input(poster_raw: Optional[str]):
    """
    Poster yo'lini FSInputFile (lokal fayl) yoki URL formatiga o'tkazadi.
    """
    if not poster_raw:
        return None
    p_str = str(poster_raw).strip()
    if not p_str:
        return None

    if p_str.startswith("http://") or p_str.startswith("https://"):
        return p_str

    # 1. BASE_DIR ga nisbatan lokal fayl tekshirish
    local_path = os.path.join(config.BASE_DIR, p_str)
    if os.path.isfile(local_path):
        return FSInputFile(local_path)

    # 2. To'g'ridan-to'g'ri berilgan lokal yo'l
    if os.path.isfile(p_str):
        return FSInputFile(p_str)

    # 3. posters/ papkasi ichidagi fayl nomi
    basename = os.path.basename(p_str)
    posters_fallback = os.path.join(config.BASE_DIR, "posters", basename)
    if os.path.isfile(posters_fallback):
        return FSInputFile(posters_fallback)

    # 4. Yuqori tezlikdagi jsDelivr CDN fallback
    clean_p = p_str.lstrip("/\\")
    return f"https://cdn.jsdelivr.net/gh/zephcodeer/uzkdrama-bot@main/{clean_p}"


async def notify_subscribers_async(
    dorama_id: int,
    ep_list: List[int],
    quality: str = "720p",
    bot: Optional[Bot] = None
) -> int:
    """
    Dorama obunachilariga yangi qism chiqqani haqida Push Notification yuboradi.
    Telegram Flood-Wait va Rate-Limitlarga (0.04s oraliq, 25 msgs/sec max) qat'iy rioya qiladi.
    TelegramRetryAfter va xato holatlarini avtomatik boshqaradi.
    """
    if not ep_list:
        logger.warning(f"notify_subscribers_async: ep_list bo'sh (dorama_id={dorama_id}).")
        return 0

    import database as db

    subscribers = await db.get_dorama_subscribers(dorama_id)
    if not subscribers:
        logger.info(f"Dorama ID={dorama_id} uchun obunachilar yo'q.")
        return 0

    dorama = await db.get_dorama_by_id(dorama_id)
    if not dorama:
        logger.warning(f"Dorama ID={dorama_id} bazadan topilmadi.")
        return 0

    title = dorama.get("title", "Nomsiz Dorama")
    code = dorama.get("code") or dorama_id
    poster_raw = dorama.get("poster_url") or ""
    eps_str = f"{min(ep_list)}–{max(ep_list)}" if len(ep_list) > 1 else str(ep_list[0])
    total_ep = dorama.get("total_episodes") or max(ep_list)
    quality_badge = f" ({quality})" if quality else ""

    msg_caption = (
        f"{ce('bell')} <b>YANGI QISM CHIQDI!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎬 <b>Dorama:</b> <b>{html.escape(str(title))}</b>\n"
        f"🎞 <b>Qism:</b> <b>{eps_str}-qism</b>{quality_badge} (Jami: {total_ep} ta)\n"
        f"🔑 <b>Kino kodi:</b> <code>{code}</code>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<i>Tomosha qilish uchun quyidagi tugmani bosing:</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎬 {eps_str}-qismni ko'rish", url=f"https://t.me/uzkdrama_app?start={code}")],
        [InlineKeyboardButton(text="📋 Serial sahifasi", callback_data=f"view_dorama:{dorama_id}")]
    ])

    photo = _resolve_photo_input(poster_raw)

    sent_count = 0
    fail_count = 0

    created_own_bot = False
    active_bot = bot

    if active_bot is None:
        if not config.BOT_TOKEN:
            logger.error("BOT_TOKEN sozlanmagan, bildirishnoma yuborib bo'lmaydi.")
            return 0
        active_bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        created_own_bot = True

    try:
        for user_id in subscribers:
            delivered = False
            use_photo = photo is not None
            for attempt in range(3):
                try:
                    if use_photo:
                        try:
                            await active_bot.send_photo(
                                chat_id=user_id,
                                photo=photo,
                                caption=msg_caption,
                                reply_markup=kb
                            )
                            delivered = True
                            break
                        except TelegramRetryAfter as e:
                            logger.warning(f"TelegramRetryAfter: user {user_id} uchun {e.retry_after}s kutish.")
                            await asyncio.sleep(e.retry_after + 1)
                            continue
                        except TelegramForbiddenError as e:
                            logger.debug(f"User {user_id} botni bloklagan: {e}")
                            break
                        except TelegramBadRequest as e:
                            logger.debug(f"send_photo TelegramBadRequest ({e}), matn ko'rinishida yuboriladi.")
                            use_photo = False
                        except Exception as e:
                            logger.debug(f"send_photo xatolik ({e}), matn ko'rinishida yuboriladi.")
                            use_photo = False

                    await active_bot.send_message(
                        chat_id=user_id,
                        text=msg_caption,
                        reply_markup=kb
                    )
                    delivered = True
                    break

                except TelegramRetryAfter as e:
                    logger.warning(f"TelegramRetryAfter: user {user_id} uchun {e.retry_after}s kutish.")
                    await asyncio.sleep(e.retry_after + 1)
                    continue
                except (TelegramForbiddenError, TelegramBadRequest) as e:
                    logger.debug(f"User {user_id} ga yuborib bo'lmadi: {e}")
                    break
                except Exception as e:
                    logger.debug(f"Notification error for {user_id}: {e}")
                    break

            if delivered:
                sent_count += 1
            else:
                fail_count += 1

            # 25 xabar/sekund xavfsiz rate limit (0.04s kutish)
            await asyncio.sleep(0.04)

    finally:
        if created_own_bot and active_bot:
            try:
                await active_bot.session.close()
            except Exception:
                pass

    logger.info(
        f"✅ Notification yakunlandi: {sent_count} muvaffaqiyatli, {fail_count} xato "
        f"(Dorama ID={dorama_id}, Qismlar={ep_list})."
    )
    return sent_count
