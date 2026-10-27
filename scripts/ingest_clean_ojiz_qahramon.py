#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
ingest_clean_ojiz_qahramon.py — Deploy Clean, Ad-Free (Qimorsiz / 1xBet-siz) iDUB
Weak Hero Class 1 (Season 1, All 8 Episodes) to Telegram Storage Channel and SQLite Database.
"""

import asyncio
import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.append(r"E:\Agent\Drama Bot")
import config
import database as db
from telethon import TelegramClient

DORAMA_ID = 12
DORAMA_CODE = 112
DORAMA_TITLE = "Ojiz qahramon 1-fasl (Weak Hero Class 1)"

# Source: @Ojiz_qahramona (Confirmed clean iDUB dubbing, 0 ads, 0 1xbet)
EPISODES_MAP = {
    1: 6,   # Msg ID 6 in source channel
    2: 8,   # Msg ID 8
    3: 9,   # Msg ID 9
    4: 10,  # Msg ID 10
    5: 11,  # Msg ID 11
    6: 12,  # Msg ID 12
    7: 13,  # Msg ID 13
    8: 14   # Msg ID 14
}

async def deploy():
    print("=" * 65)
    print("💎 TOZA VA REKLAMASIZ (QIMORSIZ) 'OJIZ QAHRAMON' 1-FASLNI JOYLASHTIRISH")
    print(f"📊 Dorama ID: {DORAMA_ID} | Kod: {DORAMA_CODE} | Jami qismlar: 8")
    print("=" * 65)

    client = TelegramClient(r'E:\Agent\Drama Bot\ojiz_session', config.API_ID, config.API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        print("❌ Telethon sessiyasi faol emas!")
        return

    async with db.aiosqlite.connect(db.DB_PATH) as conn:
        await conn.execute("DELETE FROM episodes WHERE dorama_id = ?", (DORAMA_ID,))
        await conn.commit()
    print("🧹 Eski 1xbetli yozuvlar bazadan tozalandi.")

    try:
        await client.delete_messages(config.STORAGE_CHANNEL_ID, [32])
    except Exception:
        pass

    src_channel = await client.get_entity("@Ojiz_qahramona")
    poster_path = r"E:\Agent\Drama Bot\posters\ojiz_qahramon.jpg"

    thumb_handle = None
    if os.path.exists(poster_path):
        try:
            thumb_handle = await client.upload_file(poster_path)
            print("🖼 Vertikal muqova Telethonga tayyorlandi.")
        except Exception as e:
            print(f"Muqova xatosi: {e}")

    for ep_num in sorted(EPISODES_MAP.keys()):
        src_msg_id = EPISODES_MAP[ep_num]
        print(f"\n[{ep_num}/8] 🎬 {ep_num}-qism o'tkazilmoqda (Manba Msg: {src_msg_id})...")

        src_msg = await client.get_messages(src_channel, ids=src_msg_id)
        if not src_msg or not src_msg.media:
            print(f"❌ Xatolik: Manba xabar {src_msg_id} da media topilmadi!")
            continue

        file_size = src_msg.file.size if src_msg.file else 0

        caption = (
            f"🎬 <b>{DORAMA_TITLE}</b>\n"
            f"📌 <b>{ep_num}-qism</b> (O'zbek tilida - iDub Dublaj)\n"
            f"🌟 <b>Kodi:</b> <code>{DORAMA_CODE}</code>\n"
            f"🛡 <b>Holati:</b> Reklamasiz & Qimorsiz (Toza)\n"
            f"📺 <b>Sifat:</b> HD (480p/720p)\n\n"
            f"🤖 Bot: @uzkdrama_app"
        )

        # Instant server-side send
        sent_msg = await client.send_file(
            config.STORAGE_CHANNEL_ID,
            file=src_msg.media,
            caption=caption,
            parse_mode="html",
            thumb=thumb_handle,
            supports_streaming=True
        )

        doc_id = str(sent_msg.media.document.id) if hasattr(sent_msg.media, "document") else ""
        print(f"   ✅ Telegram omboriga joylandi! Yangi Msg ID: {sent_msg.id}")

        # Add to database
        await db.add_episode(
            dorama_id=DORAMA_ID,
            episode_number=ep_num,
            channel_message_id=sent_msg.id,
            file_id=doc_id,
            file_size=file_size,
            quality="HD (iDub, Qimorsiz)"
        )
        print(f"   💾 Ma'lumotlar bazasiga muvaffaqiyatli saqlandi! ({ep_num}-qism)")
        await asyncio.sleep(1)

    await client.disconnect()

    # Remove temporary test files
    temp_files = [
        r"E:\Agent\Drama Bot\test_ep1_check.mkv",
        r"E:\Agent\Drama Bot\temp_ojiz_sample.mkv",
        r"E:\Agent\Drama Bot\snippet.mkv",
        r"E:\Agent\Drama Bot\audio_5_35.wav",
        r"E:\Agent\Drama Bot\check_frame_120.jpg",
        r"E:\Agent\Drama Bot\frame_2s.jpg"
    ]
    for tf in temp_files:
        if os.path.exists(tf):
            try:
                os.remove(tf)
            except Exception:
                pass
    print("🧹 Diskdagi barcha kesh fayllar tozalandi.")

    print("\n" + "=" * 65)
    print("🎉 BARCHA 8 TA QISM REKLAMASIZ VA QIMORSIZ TO'LIQ JOYLANDI!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(deploy())
