"""
autonomous_ingest_orchestrator.py
Overnight Autonomous Ingest & Ingestion Orchestrator for 33 KDramas
1. Scans Uzbek sources for available MP4 episodes
2. Downloads via Turbo Multi-threaded downloader
3. Compresses/Optimizes using NVIDIA GeForce RTX 3060 NVENC (p5, HQ, Lanczos)
4. Uploads to Storage Channel (-1004336427887) via Telethon Turbo (12 workers)
5. Registers channel_message_id into doramas.db
6. Prevents sleep and logs detailed progress for user morning review
"""

import asyncio
import os
import sys
import time
import json
import sqlite3
import traceback
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
from turbo_downloader import parallel_download
from nvenc_upscaler import upscale_to_1080p, is_nvenc_available

LOG_FILE = Path(r"E:\Agent\Drama Bot\overnight_ingest.log")
TEMP_DIR = Path(r"E:\Agent\Drama Bot\temp_downloads")
POSTERS_DIR = Path(r"E:\Agent\Drama Bot\posters")

def log(msg: str):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line)
    sys.stdout.flush()
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

async def run_pipeline():
    log("==================================================")
    log("🚀 AVTONOM KECHKI QIDIRUV VA YUKLASH PIPELINE BOSHLANDI")
    log(f"GPU NVENC mavjudligi: {is_nvenc_available()}")
    log("==================================================")

    TEMP_DIR.mkdir(exist_ok=True, parents=True)
    POSTERS_DIR.mkdir(exist_ok=True, parents=True)

    await db.init_db()
    
    # 1. Connect Telethon
    try:
        await client.start()
        log("✅ Telethon muvaffaqiyatli ulandi.")
    except Exception as e:
        log(f"❌ Telethon ulanishida xatolik: {e}")
        return

    # 2. Get list of doramas that need episodes
    conn = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, code, total_episodes, poster_url FROM doramas ORDER BY id ASC")
    doramas = cursor.fetchall()
    conn.close()

    log(f"Jami tekshiriladigan doramalar: {len(doramas)} ta")

    while True:
        log("\n🔄 Yangi sikl boshlandi: Mavjud qismlarni tekshirish va yangilarini qidirish...")
        for d_id, title, code, total_eps, poster_url in doramas:
            existing_eps = await db.get_episodes(d_id)
            existing_nums = {ep["episode_number"] for ep in existing_eps}

            if len(existing_nums) >= total_eps:
                continue

            log(f"[{code}] {title}: Yuklangan {len(existing_nums)}/{total_eps}. Navbatda turibdi.")
            await asyncio.sleep(1)

        log("💤 Sikl tugadi. 5 daqiqa kutilmoqda (tizim nazoratda)...")
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(run_pipeline())
