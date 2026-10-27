#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
pipeline_ojiz_qahramon.py — Autonomous High-Speed Ingestion Pipeline for:
"Ojiz qahramon" / "Weak Hero Class 1" (1-fasl, barcha 8 qism)
Multi-threaded Range Downloader + FastStart Remuxer + Telethon Turbo Uploader (12 workers).
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

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.append(r"E:\Agent\Drama Bot")
import config
import database as db
from telethon import TelegramClient, helpers
from telethon.tl.types import InputFileBig, DocumentAttributeVideo
from telethon.tl.functions.upload import SaveBigFilePartRequest
from PIL import Image

DORAMA_ID = 12
DORAMA_CODE = 112
DORAMA_TITLE = "Ojiz qahramon 1-fasl (Weak Hero Class 1)"
STORAGE_CHANNEL = config.STORAGE_CHANNEL_ID
POSTER_PATH = Path(r"E:\Agent\Drama Bot\posters\ojiz_qahramon.jpg")
TEMP_DIR = Path(r"E:\Agent\Drama Bot\temp_ojiz")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Uzmovi / k1.qnbuz.net direct high-speed CDN URLs (all 8 episodes confirmed)
EPISODES = {
    1: "https://k1.qnbuz.net/serial/ojiz_1_qism.mp4",
    2: "https://k1.qnbuz.net/serial/ojiz_2_qism.mp4",
    3: "https://k1.qnbuz.net/serial/ojiz_3_qism.mp4",
    4: "https://k1.qnbuz.net/serial/ojiz_4_qism.mp4",
    5: "https://k1.qnbuz.net/serial/ojiz_5_qism.mp4",
    6: "https://k1.qnbuz.net/serial/ojiz_6_qism.mp4",
    7: "https://k1.qnbuz.net/serial/ojiz_7_qism.mp4",
    8: "https://k1.qnbuz.net/serial/ojiz_8_qism.mp4",
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://uzmovi.me/',
        'Range': f'bytes={start_byte}-{end_byte}'
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        with open(part_path, 'wb') as f:
            f.write(r.read())


def fast_download(url, dest_path, num_threads=4):
    """Parallel range chunk downloader for maximum saturation."""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://uzmovi.me/'})
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        total_size = int(r.headers.get('Content-Length', 0))

    if total_size <= 0:
        raise ValueError("Content-Length aniqlanmadi")

    print(f"   Hajmi: {total_size / (1024*1024):.1f} MB ({num_threads} parallel oqimda yuklanmoqda)...")
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
        # Fallback to copy
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

    if not thumb_path.exists() or thumb_path.stat().st_size == 0:
        ss_time = min(15, max(1, duration // 3))
        cmd = [
            "ffmpeg", "-y", "-ss", str(ss_time),
            "-i", str(video_path),
            "-vframes", "1", "-vf", "scale=320:-1",
            str(thumb_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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

    async def worker():
        while not queue.empty():
            try:
                part_idx, chunk_bytes = queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            for attempt in range(5):
                try:
                    await client(SaveBigFilePartRequest(
                        file_id=file_id,
                        file_part=part_idx,
                        file_total_parts=total_parts,
                        bytes=chunk_bytes
                    ))
                    break
                except Exception as e:
                    if attempt == 4:
                        raise e
                    await asyncio.sleep(1 + attempt)
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
        f"📌 <b>{ep_num}-qism</b> (O'zbek tilida)\n"
        f"🌟 <b>Kodi:</b> <code>{DORAMA_CODE}</code>\n"
        f"📺 <b>Sifat:</b> HD (720p)\n\n"
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

    return msg.id, str(msg.media.document.id) if hasattr(msg.media, "document") else ""


async def run_ojiz_pipeline():
    print("=" * 65)
    print("🚀 OJIZ QAHRAMON (WEAK HERO CLASS 1) 1-FASL PIPELINE ISHGA TUSHDI")
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
        # 1. Check if already in DB
        existing = await db.get_episode(DORAMA_ID, ep_num)
        if existing:
            print(f"⏩ {ep_num}-qism allaqachon bazada mavjud (Msg ID: {existing['channel_message_id']}).")
            success_count += 1
            continue

        raw_file = TEMP_DIR / f"raw_ojiz_ep{ep_num}.mp4"
        final_file = TEMP_DIR / f"ojiz_ep{ep_num}.mp4"
        url = EPISODES[ep_num]

        print(f"\n[{ep_num}/8] 📥 {ep_num}-qism yuklab olinmoqda...")
        t0 = time.time()
        try:
            fast_download(url, raw_file, num_threads=4)
        except Exception as e:
            print(f"❌ Yuklab olishda xatolik ({ep_num}-qism): {e}")
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
                quality="HD"
            )
            print(f"   💾 Ma'lumotlar bazasiga saqlandi! ({ep_num}-qism)")
            success_count += 1

            # Disk cleanup
            try:
                final_file.unlink()
                print(f"   🧹 Kesh fayli o'chirildi.")
            except Exception:
                pass

        except Exception as e:
            print(f"❌ Telegramga yuklashda xatolik ({ep_num}-qism): {e}")

    await client.disconnect()
    print("\n" + "=" * 65)
    print(f"🎉 PIPELINE YAKUNLANDI! Barcha {success_count}/8 qism muvaffaqiyatli yakunlandi.")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_ojiz_pipeline())
