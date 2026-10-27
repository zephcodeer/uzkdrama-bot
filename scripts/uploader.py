#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
uploader.py — Telethon Turbo Parallel Uploader (12 workers)
with automatic FFmpeg thumbnail generation, duration extraction,
and poster scraping for full-screen video player in Telegram.
"""

import argparse
import asyncio
import html as html_utils
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from telethon import TelegramClient, helpers
from telethon.tl.types import InputFileBig, DocumentAttributeVideo
from telethon.tl.functions.upload import SaveBigFilePartRequest

import config
import database as db

client = TelegramClient(
    session=str(config.BASE_DIR / "premium_session"),
    api_id=config.API_ID,
    api_hash=config.API_HASH
)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://uzdrama.tv/",
    "Origin": "https://uzdrama.tv",
    "Accept": "*/*",
}


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def parse_uzdrama(movie_url: str):
    raw_html = fetch_html(movie_url)
    html = html_utils.unescape(raw_html)

    # Sarlavha
    t_m = re.search(r"<h1[^>]*>([^<]+)</h1>", html)
    title = re.sub(r"\s+", " ", t_m.group(1)).strip() if t_m else "Noma'lum Dorama"

    # Poster
    poster_m = re.search(r'<div[^>]*class=[\'"][^\'"]*poster[^\'"]*[\'"][^>]*>.*?<img[^>]+src=[\'"]([^\'"]+)', html, re.S)
    poster_url = ""
    if poster_m:
        src = poster_m.group(1)
        poster_url = src if src.startswith("http") else "https://uzdrama.tv" + src

    episodes = {}
    first_m = re.search(r'var\s+firstEp\s*=\s*["\']([^"\']+)["\']', html)
    if first_m:
        u = first_m.group(1).replace(r"\/", "/")
        episodes[1] = u

    for m in re.finditer(r'playEpisodeModern\s*\(\s*["\']([^"\']+)["\']', html):
        u = m.group(1).replace(r"\/", "/")
        ep_num_m = re.search(r"/(\d+)\.mp4$", u)
        if ep_num_m:
            episodes[int(ep_num_m.group(1))] = u
        else:
            episodes[len(episodes) + 1] = u

    return title, episodes, poster_url


def get_video_meta_and_thumb(video_path: Path, poster_path: Path = None):
    """FFmpeg yoki poster orqali video muqovasi (thumbnail) va davomiyligini olish."""
    thumb_path = video_path.parent / f"{video_path.stem}_thumb.jpg"
    duration = 0
    w = 1280
    h = 720

    # 1. Agar dorama posteri bo'lsa, undan tiniq muqova yaratamiz
    if poster_path and Path(poster_path).exists():
        try:
            from PIL import Image
            p_img = Image.open(poster_path)
            thumb = p_img.convert("RGB")
            thumb.thumbnail((320, 320), Image.Resampling.LANCZOS)
            thumb.save(thumb_path, "JPEG", quality=92)
        except Exception as e:
            print(f"   ⚠️ Posterdan thumbnail yaratishda xatolik: {e}")

    # 2. Agar poster bo'lmasa, videoning 3-daqiqasidagi jonli kadrni olamiz (qora 00:00 ekran bo'lmasligi uchun)
    if not thumb_path.exists():
        try:
            subprocess.run([
                "ffmpeg", "-y", "-ss", "00:03:00", "-i", str(video_path),
                "-vframes", "1", "-q:v", "2", str(thumb_path)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
        except Exception as e:
            print(f"   ⚠️ FFmpeg thumbnail olishda xatolik: {e}")

    # 3. FFprobe orqali o'lcham va davomiylikni aniqlash
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "stream=width,height,duration", "-of", "json", str(video_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        data = json.loads(res.stdout)
        for s in data.get("streams", []):
            if "width" in s and "height" in s:
                w = int(s["width"])
                h = int(s["height"])
                if "duration" in s:
                    duration = int(float(s["duration"]))
                break
    except Exception as e:
        print(f"   ⚠️ FFprobe o'lchovida xatolik: {e}")

    return (thumb_path if thumb_path.exists() else None), w, h, duration


def download_file_stream(url: str, dest_path: Path, referer: str = "https://uzdrama.tv/"):
    print(f"\n📥 CDN dan yuklanmoqda: {url}")
    dest_path.parent.mkdir(exist_ok=True, parents=True)

    headers = dict(DEFAULT_HEADERS)
    if referer:
        headers["Referer"] = referer

    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req, timeout=90) as response, open(dest_path, "wb") as out_file:
        total_size = int(response.info().get("Content-Length", 0))
        downloaded = 0
        chunk_size = 2 * 1024 * 1024

        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                percent = downloaded / total_size * 100
                mb_down = downloaded / (1024 * 1024)
                mb_tot = total_size / (1024 * 1024)
                sys.stdout.write(f"\r   [CDN YUKLASH: {percent:5.1f}%] {mb_down:6.1f} MB / {mb_tot:6.1f} MB")
                sys.stdout.flush()

    print("\n   ✅ CDN dan to'liq yuklab olindi.")
    return dest_path


async def fast_upload_file(file_path: Path, progress_callback=None, max_workers: int = 12):
    """Telegramga 12 ta parallel oqimda yuklash (Speedup: 20x)."""
    file_size = os.path.getsize(file_path)
    part_size = 512 * 1024  # 512 KB
    part_count = (file_size + part_size - 1) // part_size
    file_id = helpers.generate_random_long()
    file_name = file_path.name

    sem = asyncio.Semaphore(max_workers)
    uploaded_bytes = 0
    lock = asyncio.Lock()

    async def upload_part(part_index, data):
        nonlocal uploaded_bytes
        async with sem:
            req = SaveBigFilePartRequest(file_id, part_index, part_count, data)
            await client(req)
            async with lock:
                uploaded_bytes += len(data)
                if progress_callback:
                    progress_callback(uploaded_bytes, file_size)

    tasks = []
    with open(file_path, "rb") as f:
        for i in range(part_count):
            tasks.append(upload_part(i, f.read(part_size)))

    await asyncio.gather(*tasks)

    return InputFileBig(
        id=file_id,
        parts=part_count,
        name=file_name
    )


async def upload_episode(dorama_id: int, title: str, ep_num: int, file_path: Path, poster_path: Path = None):
    print(f"\n🚀 Telegram maxfiy omboriga TURBO yuklanmoqda: {title} | {ep_num}-qism...")

    caption = (
        f"🎬 <b>{title}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🍿 <b>{ep_num}-qism</b> (Full HD)\n"
        f"💎 <i>Dorama Hub rasmiy ombori</i>"
    )

    file_size = os.path.getsize(file_path)

    if not poster_path:
        d = await db.get_dorama_by_id(dorama_id)
        if d and d.get("poster_url") and os.path.exists(d["poster_url"]):
            poster_path = Path(d["poster_url"])
        else:
            local_p = Path("posters/doktor_x_clean_poster.jpg")
            if local_p.exists():
                poster_path = local_p

    # Video davomiyligi va muqovasini olish
    thumb_path, w, h, duration = get_video_meta_and_thumb(file_path, poster_path=poster_path)
    print(f"   📐 Video formati: {w}x{h}, Davomiyligi: {duration // 60}:{duration % 60:02d}")

    attributes = [
        DocumentAttributeVideo(
            duration=duration,
            w=w,
            h=h,
            supports_streaming=True
        )
    ]

    def progress_callback(current, total):
        pct = current / total * 100
        mb_curr = current / (1024 * 1024)
        mb_tot = total / (1024 * 1024)
        sys.stdout.write(f"\r   [TG TURBO: {pct:5.1f}%] {mb_curr:6.1f} MB / {mb_tot:6.1f} MB")
        sys.stdout.flush()

    input_file = await fast_upload_file(file_path, progress_callback=progress_callback, max_workers=12)

    msg = await client.send_file(
        entity=config.STORAGE_CHANNEL_ID,
        file=input_file,
        caption=caption,
        parse_mode="html",
        thumb=str(thumb_path) if thumb_path else None,
        attributes=attributes,
        supports_streaming=True
    )
    print(f"\n   ✅ Maxfiy kanalga yuklandi! (Xabar ID: {msg.id})")

    if thumb_path and thumb_path.exists():
        thumb_path.unlink()

    file_id = ""
    if msg.media and hasattr(msg.media, "document"):
        file_id = str(msg.media.document.id)

    # SQLite bazaga yozish
    await db.add_episode(
        dorama_id=dorama_id,
        episode_number=ep_num,
        channel_message_id=msg.id,
        file_id=file_id,
        file_size=file_size,
        quality=f"{h}p" if h else "720p"
    )
    print(f"   💾 Bazaga saqlandi: {title} — {ep_num}-qism.")

    # Obunachilarga avtomat bildirishnoma yuborish
    try:
        subscribers = await db.get_dorama_subscribers(dorama_id)
        if subscribers:
            print(f"   🔔 {len(subscribers)} ta obunachiga xabarnoma yuborilmoqda...")
            import json
            api_url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
            notif_text = (
                f"🔥 <b>YANGI QISM CHIQDI!</b>\n\n"
                f"🎬 <b>{title}</b> — <b>{ep_num}-qism</b> allaqachon tayyor!\n\n"
                f"🍿 Tomosha qilish uchun quyidagi tugmani bosing:"
            )
            for uid in subscribers:
                try:
                    payload = {
                        "chat_id": uid,
                        "text": notif_text,
                        "parse_mode": "HTML",
                        "reply_markup": {
                            "inline_keyboard": [[
                                {"text": f"▶️ {ep_num}-qismni tomosha qilish", "callback_data": f"get_ep:{dorama_id}:{ep_num}"}
                            ]]
                        }
                    }
                    req = urllib.request.Request(
                        api_url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=5):
                        pass
                except Exception:
                    pass
    except Exception as e:
        print(f"   ⚠️ Obunachilarga bildirishnoma yuborishda xatolik: {e}")

    return msg.id, file_id


async def process_scraper(movie_url: str):
    await db.init_db()
    title, episodes, poster_url = parse_uzdrama(movie_url)
    print(f"\n🎬 Sarlavha: {title}")
    print(f"🖼 Poster: {poster_url or 'Mavjud emas'}")
    print(f"📺 Topilgan qismlar: {len(episodes)} ta: {sorted(episodes.keys())}")

    if not episodes:
        print("❌ Hech qanday qism topilmadi!")
        return

    dorama_id = await db.add_or_get_dorama(title=title, genre="Dorama", year=2026, poster_url=poster_url)

    existing_eps = {ep["episode_number"] for ep in await db.get_episodes(dorama_id)}

    for ep_num in sorted(episodes.keys()):
        if ep_num in existing_eps:
            print(f"⏩ {ep_num}-qism allaqachon bazada bor, o'tkazib yuborildi.")
            continue

        url = episodes[ep_num]
        temp_file = config.TEMP_DIR / f"{dorama_id}_{ep_num}.mp4"
        try:
            download_file_stream(url, temp_file, referer=movie_url)
            await upload_episode(dorama_id, title, ep_num, temp_file)
        except Exception as e:
            print(f"\n❌ {ep_num}-qismni yuklashda xatolik: {e}")
        finally:
            if temp_file.exists():
                temp_file.unlink()
                print(f"   🧹 Vaqtinchalik fayl tozalandi: {temp_file.name}")


async def main():
    parser = argparse.ArgumentParser(description="Dorama Telegram Turbo Uploader")
    parser.add_argument("--scrape", type=str, help="uzdrama.tv video sahifasi havolasi")

    args = parser.parse_args()

    errs = config.validate_uploader_config()
    if errs:
        print("XATOLIK:")
        for e in errs:
            print(f"  ❌ {e}")
        return

    await client.start()
    me = await client.get_me()
    print(f"\n👤 Telethon yuklovchi tizimga kirdi: {me.first_name} (Premium: {me.premium})")

    if args.scrape:
        await process_scraper(args.scrape)
    else:
        print("Misol: python uploader.py --scrape https://uzdrama.tv/movie.php?id=1903")


if __name__ == "__main__":
    asyncio.run(main())
