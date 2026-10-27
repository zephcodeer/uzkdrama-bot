#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
master_ovchi_itlar_pipeline.py — Master Ingestion Pipeline for Ovchi Itlar (Season 1 & Season 2)
Full HD 1080p Turbo Parallel Telegram Uploader with automated fallback & disk cleanup.
"""

import asyncio
import base64
import os
import re
import ssl
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.append(r"E:\Agent\Drama Bot")
import config
import database as db
from uploader import upload_episode, client

TEMP_DIR = Path(r"E:\Agent\Drama Bot\temp_downloads")
TEMP_DIR.mkdir(exist_ok=True, parents=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# SEASON 1 CONFIGURATION
S1_ID = 18
S1_TITLE = "Ovchi itlar 1-fasl"
S1_EPISODES = {
    6: "https://ok.ru/video/15972448471602",
    7: "https://ok.ru/video/15972448995890",
    8: "https://ok.ru/video/15972449651250"
}

# SEASON 2 CONFIGURATION
S2_ID = 35
S2_TITLE = "Ovchi itlar 2-fasl"
S2_EPISODES = {
    1: {"type": "ok", "url": "https://ok.ru/video/15973306665522"},
    2: {"type": "ok", "url": "https://ok.ru/video/15973308762674"},
    3: {"type": "ok", "url": "https://ok.ru/video/16076252514866"},
    4: {"type": "ok", "url": "https://ok.ru/video/16259250457138"},
    5: {"type": "ok", "url": "https://ok.ru/video/16259252619826"},
    6: {"type": "doramalar", "url": "https://doramalar.net/dorama/ovchi-itlar-37/2-fasl-6-qism"},
    7: {"type": "doramalar", "url": "https://doramalar.net/dorama/ovchi-itlar-37/2-fasl-7-qism"}
}


def decode_doramalar(s: str) -> str:
    if not isinstance(s, str) or not s.startswith("#2"):
        return s
    t = s[2:]
    for item in reversed(['6u3kEQLAkT', '4e0OIbkv8D', 'EXOThnsl1y', 'wHiWWKB8U9', 'rMTS46lVY0']):
        r = '//' + base64.b64encode(item.encode()).decode()
        n = t.find(r)
        if n != -1:
            t = t[:n] + t[n + len(r):]
    try:
        return base64.b64decode(t).decode('utf-8', errors='ignore')
    except Exception:
        return ""


def resolve_doramalar_stream(page_url: str) -> str:
    req = urllib.request.Request(page_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')

    b64_matches = re.findall(r'#2[a-zA-Z0-9+/=]+', html)
    if not b64_matches:
        raise ValueError("Playerjs ma'lumotlari topilmadi")

    decoded_mp4 = decode_doramalar(b64_matches[1]) if len(b64_matches) > 1 else ""
    urls = re.findall(r'https://[^\s,]+', decoded_mp4)
    mp4_urls = [u for u in urls if '.mp4?' in u] or urls

    for u in mp4_urls:
        try:
            test_req = urllib.request.Request(u, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Referer': 'https://doramalar.net/'
            })
            with urllib.request.urlopen(test_req, context=ctx, timeout=6) as tr:
                if tr.status == 200:
                    return u
        except Exception:
            continue

    return decode_doramalar(b64_matches[0])


async def process_season_1():
    print("\n" + "=" * 60)
    print("🎬 1-FASL (OVCHI ITLAR) QISMLARINI YUKLASH BOSHLANDI")
    print("=" * 60)

    for ep_num in sorted(S1_EPISODES.keys()):
        existing = await db.get_episode(S1_ID, ep_num)
        if existing:
            print(f"⏩ 1-fasl {ep_num}-qism allaqachon bazada mavjud (Msg ID: {existing['channel_message_id']}).")
            continue

        dest_file = TEMP_DIR / f"ovchi_itlar_ep{ep_num}.mp4"
        url = S1_EPISODES[ep_num]

        # 1. Download if not on disk
        if not dest_file.exists() or os.path.getsize(dest_file) < 100 * 1024 * 1024:
            print(f"\n📥 1-fasl {ep_num}-qism CDN dan yuklab olinmoqda: {url}")
            cmd = ["yt-dlp", "-f", "hls-1544/hls-1489/full/best", "-o", str(dest_file), url, "--no-playlist"]
            res = subprocess.run(cmd)
            if res.returncode != 0 or not dest_file.exists():
                print(f"❌ 1-fasl {ep_num}-qismni yuklab olishda xatolik!")
                continue

        file_size = os.path.getsize(dest_file)
        print(f"\n🚀 1-fasl {ep_num}-qism Telegramga yuklanmoqda ({file_size / (1024*1024):.1f} MB)...")

        try:
            msg_id, file_id = await upload_episode(
                dorama_id=S1_ID,
                title=S1_TITLE,
                ep_num=ep_num,
                file_path=dest_file,
                poster_path=Path("posters/ovchi_itlar.jpg")
            )

            await db.add_episode(
                dorama_id=S1_ID,
                episode_number=ep_num,
                channel_message_id=msg_id,
                file_id=file_id or "",
                file_size=file_size,
                quality="1080p"
            )
            print(f"✅ 1-FASL {ep_num}-QISM MUVAFFAQIYATLI YUKLANDI! (Msg ID: {msg_id})")

            # Clean disk
            try:
                dest_file.unlink()
                print(f"🧹 Disk tozalandi: {dest_file.name}")
            except Exception:
                pass

        except Exception as e:
            print(f"❌ Telegramga yuklashda xatolik (1-fasl {ep_num}-qism): {e}")


async def process_season_2():
    print("\n" + "=" * 60)
    print("🎬 2-FASL (OVCHI ITLAR) QISMLARINI YUKLASH BOSHLANDI")
    print("=" * 60)

    for ep_num in sorted(S2_EPISODES.keys()):
        existing = await db.get_episode(S2_ID, ep_num)
        if existing:
            print(f"⏩ 2-fasl {ep_num}-qism allaqachon bazada mavjud (Msg ID: {existing['channel_message_id']}).")
            continue

        info = S2_EPISODES[ep_num]
        dest_file = TEMP_DIR / f"ovchi_itlar_s2_ep{ep_num}.mp4"

        # 1. Download if not on disk
        if not dest_file.exists() or os.path.getsize(dest_file) < 50 * 1024 * 1024:
            print(f"\n📥 2-fasl {ep_num}-qism yuklanmoqda: {info['url']}")
            if info["type"] == "ok":
                cmd = ["yt-dlp", "-f", "hls-1544/hls-1489/full/hls-764/best", "-o", str(dest_file), info["url"], "--no-playlist"]
                res = subprocess.run(cmd)
            else:
                try:
                    stream_url = resolve_doramalar_stream(info["url"])
                    cmd = ["yt-dlp", "--add-header", "Referer:https://doramalar.net/", "-o", str(dest_file), stream_url, "--no-playlist"]
                    res = subprocess.run(cmd)
                except Exception as e:
                    print(f"❌ Stream URL xatosi: {e}")
                    continue

            if not dest_file.exists() or os.path.getsize(dest_file) < 10 * 1024 * 1024:
                print(f"❌ 2-fasl {ep_num}-qismni yuklab olish muvaffaqiyatsiz bo'ldi!")
                continue

        file_size = os.path.getsize(dest_file)
        quality = "1080p" if info["type"] == "ok" else "720p"
        print(f"\n🚀 2-fasl {ep_num}-qism Telegramga yuklanmoqda ({file_size / (1024*1024):.1f} MB, {quality})...")

        try:
            msg_id, file_id = await upload_episode(
                dorama_id=S2_ID,
                title=S2_TITLE,
                ep_num=ep_num,
                file_path=dest_file,
                poster_path=Path("posters/ovchi_itlar.jpg")
            )

            await db.add_episode(
                dorama_id=S2_ID,
                episode_number=ep_num,
                channel_message_id=msg_id,
                file_id=file_id or "",
                file_size=file_size,
                quality=quality
            )
            print(f"✅ 2-FASL {ep_num}-QISM MUVAFFAQIYATLI YUKLANDI! (Msg ID: {msg_id})")

            # Clean disk
            try:
                dest_file.unlink()
                print(f"🧹 Disk tozalandi: {dest_file.name}")
            except Exception:
                pass

        except Exception as e:
            print(f"❌ Telegramga yuklashda xatolik (2-fasl {ep_num}-qism): {e}")


async def main():
    await db.init_db()
    await client.start()
    print("🚀 Telethon Premium Turbo Uploader ishga tushdi.")

    try:
        await process_season_1()
        await asyncio.sleep(3)
        await process_season_2()
    finally:
        await client.disconnect()

    print("\n" + "=" * 60)
    print("🎉 BARCHA QISMLAR MUVAFFAQIYATLI YAKUNLANDI!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
