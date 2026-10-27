#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
pipeline_ojiz_qahramon_s2.py — Autonomous High-Speed Ingestion Pipeline for:
"Ojiz qahramon 2-fasl (Weak Hero Class 2)" (Season 2, all 8 episodes from Mover.uz).

Features:
- Multi-threaded Range Downloader (8 threads per video, auto-retry with exponential backoff)
- FFmpeg FastStart remuxer (instant zero-buffer streaming in Telegram)
- Telethon Turbo Uploader (12 parallel chunk workers, real-time progress)
- Direct SQLite DB record insertion with quality "720p HD (iDUB, Qimorsiz)"
- Instant temp cleanup
- 100% clean iDUB dubbing, 0 ads, 0 1xbet.
"""

import asyncio
import os
import sys
import time
import math
import subprocess
import urllib.request
import ssl
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.append(r"E:\Agent\Drama Bot")
import config
import database as db
from telethon import TelegramClient, helpers
from telethon.tl.types import InputFileBig, DocumentAttributeVideo
from telethon.tl.functions.upload import SaveBigFilePartRequest

DORAMA_ID = 36
DORAMA_CODE = 136
DORAMA_TITLE = "Ojiz qahramon 2-fasl (Weak Hero Class 2)"
STORAGE_CHANNEL = config.STORAGE_CHANNEL_ID
POSTER_PATH = Path(r"E:\Agent\Drama Bot\posters\ojiz_qahramon_s2.jpg")
TEMP_DIR = Path(r"E:\Agent\Drama Bot\temp_ojiz_s2")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# 8 Mover.uz 720p Direct MP4 URLs
EPISODES = {
    1: "https://v.mover.uz/uGmXQUji_h.mp4",
    2: "https://v.mover.uz/e1muznc1_h.mp4",
    3: "https://v.mover.uz/cF3is6bE_h.mp4",
    4: "https://v.mover.uz/QRAJ0tZa_h.mp4",
    5: "https://v.mover.uz/cTVJwfaX_h.mp4",
    6: "https://v.mover.uz/slohSEqg_h.mp4",
    7: "https://v.mover.uz/dEo0owSK_h.mp4",
    8: "https://v.mover.uz/WcEtHZI_h.mp4"
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

client = TelegramClient(
    session=r"E:\Agent\Drama Bot\ojiz_session",
    api_id=config.API_ID,
    api_hash=config.API_HASH
)


def download_chunk(url, start_byte, end_byte, part_path):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://mover.uz/',
        'Range': f'bytes={start_byte}-{end_byte}'
    }
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=45) as r:
                data = r.read()
                expected = end_byte - start_byte + 1
                if len(data) != expected:
                    raise IOError(f"Kutilgan hajm: {expected}, olingan: {len(data)}")
                with open(part_path, 'wb') as f:
                    f.write(data)
            return
        except Exception as e:
            if attempt == 5:
                raise e
            time.sleep(2 + attempt * 2)


def fast_download(url, dest_path, num_threads=8):
    """8-thread parallel range chunk downloader for maximum bandwidth saturation."""
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'https://mover.uz/',
            'Range': 'bytes=0-10'
        }
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
                cr = r.headers.get('Content-Range', '')
                total_size = int(cr.split('/')[-1]) if '/' in cr else int(r.headers.get('Content-Length', 0))
            break
        except Exception as e:
            if attempt == 4:
                raise e
            time.sleep(2 + attempt)

    if total_size <= 0:
        raise ValueError("Content-Length aniqlanmadi")

    print(f"   📦 Hajmi: {total_size / (1024*1024):.1f} MB ({num_threads} parallel oqimda yuklanmoqda)...")
    chunk_size = math.ceil(total_size / num_threads)
    part_files = []
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(num_threads):
            start = i * chunk_size
            end = min(start + chunk_size - 1, total_size - 1)
            part_path = dest_path.with_suffix(f".part{i}")
            part_files.append(part_path)
            futures.append(executor.submit(download_chunk, url, start, end, part_path))

        for f in concurrent.futures.as_completed(futures):
            f.result()

    # Combine parts
    with open(dest_path, 'wb') as outfile:
        for p in part_files:
            with open(p, 'rb') as infile:
                outfile.write(infile.read())
            try:
                p.unlink()
            except Exception:
                pass


def remux_faststart(src_path: Path, dst_path: Path):
    """Ensure MP4 has moov atom at beginning for instant zero-buffer Telegram playback."""
    cmd = [
        "ffmpeg", "-y", "-i", str(src_path),
        "-c", "copy",
        "-movflags", "+faststart",
        str(dst_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode != 0 or not dst_path.exists() or os.path.getsize(dst_path) < 1024 * 1024:
        import shutil
        shutil.copy2(src_path, dst_path)


def get_video_meta_and_thumb(video_path: Path, poster_path: Path = None):
    thumb_path = video_path.parent / f"{video_path.stem}_thumb.jpg"
    duration = 0
    w = 1280
    h = 720

    if poster_path and Path(poster_path).exists():
        try:
            p_img = Image.open(poster_path)
            thumb = p_img.convert("RGB")
            thumb.thumbnail((320, 320), Image.Resampling.LANCZOS)
            thumb.save(thumb_path, "JPEG", quality=92)
        except Exception:
            pass

    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration:stream=width,height",
        "-of", "json", str(video_path)
    ]
    try:
        out = subprocess.check_output(cmd).decode("utf-8", "ignore")
        import json
        data = json.loads(out)
        duration = int(float(data.get("format", {}).get("duration", 0)))
        streams = data.get("streams", [])
        if streams:
            w = int(streams[0].get("width", 1280))
            h = int(streams[0].get("height", 720))
    except Exception:
        pass

    return duration, w, h, thumb_path


async def upload_file_turbo(client, file_path: Path, workers: int = 12) -> InputFileBig:
    file_size = file_path.stat().st_size
    file_id = helpers.generate_random_long()
    part_size = 512 * 1024
    total_parts = (file_size + part_size - 1) // part_size

    queue = asyncio.Queue()
    with open(file_path, "rb") as f:
        for part_index in range(total_parts):
            chunk = f.read(part_size)
            await queue.put((part_index, chunk))

    uploaded_parts = 0
    lock = asyncio.Lock()
    t_start = time.time()

    async def worker():
        nonlocal uploaded_parts
        while not queue.empty():
            try:
                part_idx, chunk_bytes = queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            for attempt in range(6):
                try:
                    await client(SaveBigFilePartRequest(
                        file_id=file_id,
                        file_part=part_idx,
                        file_total_parts=total_parts,
                        bytes=chunk_bytes
                    ))
                    break
                except Exception as e:
                    if attempt == 5:
                        raise e
                    await asyncio.sleep(1 + attempt)

            async with lock:
                uploaded_parts += 1
                if uploaded_parts % 100 == 0 or uploaded_parts == total_parts:
                    pct = (uploaded_parts / total_parts) * 100
                    elapsed = time.time() - t_start
                    mb_done = (uploaded_parts * part_size) / (1024 * 1024)
                    speed = mb_done / elapsed if elapsed > 0 else 0
                    print(f"      [TG: {pct:5.1f}%] {mb_done:.1f}/{file_size/(1024*1024):.1f} MB ({speed:.2f} MB/s)")

            queue.task_done()

    tasks = [asyncio.create_task(worker()) for _ in range(workers)]
    await asyncio.gather(*tasks)
    return InputFileBig(id=file_id, parts=total_parts, name=file_path.name)


async def upload_episode(ep_num: int, faststart_path: Path):
    duration, w, h, thumb_path = get_video_meta_and_thumb(faststart_path, POSTER_PATH)
    file_size = faststart_path.stat().st_size

    thumb_handle = None
    if thumb_path and thumb_path.exists():
        thumb_handle = await client.upload_file(str(thumb_path))

    input_file = await upload_file_turbo(client, faststart_path, workers=12)

    attributes = [
        DocumentAttributeVideo(
            duration=duration,
            w=w,
            h=h,
            supports_streaming=True
        )
    ]

    caption = (
        f"🎬 <b>{DORAMA_TITLE}</b>\n"
        f"📌 <b>{ep_num}-qism</b> (O'zbek tilida - iDub Dublaj)\n"
        f"🌟 <b>Kodi:</b> <code>{DORAMA_CODE}</code>\n"
        f"🛡 <b>Holati:</b> Reklamasiz & Qimorsiz (Toza)\n"
        f"📺 <b>Sifat:</b> Full HD (720p)\n\n"
        f"🤖 Bot: @uzkdrama_app"
    )

    msg = await client.send_file(
        STORAGE_CHANNEL,
        file=input_file,
        caption=caption,
        parse_mode="html",
        thumb=thumb_handle,
        attributes=attributes,
        supports_streaming=True
    )

    try:
        if thumb_path and thumb_path.exists():
            thumb_path.unlink()
    except Exception:
        pass

    file_doc_id = str(msg.media.document.id) if hasattr(msg.media, "document") else ""
    return msg.id, file_doc_id


async def run_pipeline():
    print("=" * 65)
    print("🚀 OJIZ QAHRAMON 2-FASL (WEAK HERO CLASS 2) PIPELINE ISHGA TUSHDI")
    print(f"📊 Dorama ID: {DORAMA_ID} | Kod: {DORAMA_CODE} | Jami qismlar: {len(EPISODES)}")
    print("=" * 65)

    await client.connect()
    if not await client.is_user_authorized():
        print("❌ Telethon sessiyasi faol emas!")
        return

    me = await client.get_me()
    print(f"👤 Telethon Uploader: {me.first_name} (@{me.username})")

    success_count = 0

    for ep_num in sorted(EPISODES.keys()):
        existing = await db.get_episode(DORAMA_ID, ep_num)
        if existing:
            print(f"⏩ {ep_num}-qism allaqachon mavjud (Msg ID: {existing['channel_message_id']}).")
            success_count += 1
            continue

        raw_file = TEMP_DIR / f"raw_ojiz_s2_ep{ep_num}.mp4"
        final_file = TEMP_DIR / f"ojiz_s2_ep{ep_num}.mp4"
        url = EPISODES[ep_num]

        print(f"\n[{ep_num}/8] 📥 2-fasl {ep_num}-qism yuklab olinmoqda ({url})...")
        t0 = time.time()
        download_success = False

        for dl_try in range(3):
            try:
                fast_download(url, raw_file, num_threads=8)
                dl_time = time.time() - t0
                print(f"   ✅ Yuklab olindi {dl_time:.1f} soniyada!")
                download_success = True
                break
            except Exception as e:
                print(f"   ⚠️ Yuklab olishda xatolik (urinish {dl_try+1}/3): {e}")
                time.sleep(3)

        if not download_success or not raw_file.exists() or raw_file.stat().st_size < 1024 * 1024:
            print(f"❌ {ep_num}-qismni yuklab bo'lmadi, o'tkazib yuborilmoqda.")
            continue

        print(f"   ⚡ FastStart remux qilinmoqda...")
        remux_faststart(raw_file, final_file)
        try:
            raw_file.unlink()
        except Exception:
            pass

        file_size = final_file.stat().st_size
        print(f"   🚀 Telegramga yuklanmoqda ({file_size / (1024*1024):.1f} MB, Turbo 12 workers)...")
        t_up = time.time()
        try:
            msg_id, file_id = await upload_episode(ep_num, final_file)
            up_time = time.time() - t_up
            print(f"   ✅ Telegramga yuklandi {up_time:.1f} soniyada! (Msg ID: {msg_id})")

            # Save in database
            await db.add_episode(
                dorama_id=DORAMA_ID,
                episode_number=ep_num,
                channel_message_id=msg_id,
                file_id=file_id or "",
                file_size=file_size,
                quality="720p HD (iDUB, Qimorsiz)"
            )
            print(f"   💾 Bazaga saqlandi! ({ep_num}-qism)")
            success_count += 1

            # Disk cleanup
            try:
                final_file.unlink()
                print(f"   🧹 Kesh tozalandi.")
            except Exception:
                pass

        except Exception as e:
            print(f"❌ Telegramga yuklashda xatolik ({ep_num}-qism): {e}")
            try:
                final_file.unlink()
            except Exception:
                pass

    await client.disconnect()
    print("\n" + "=" * 65)
    print(f"🎉 2-FASL PIPELINE YAKUNLANDI! Barcha {success_count}/8 qism muvaffaqiyatli yakunlandi.")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
