import asyncio
import os
import sys
import subprocess
import time
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

DORAMA_ID = 18
TITLE = "Ovchi itlar 1-fasl"
TEMP_DIR = Path(r"E:\Agent\Drama Bot\temp_downloads")

EPISODE_URLS = {
    2: "https://ok.ru/video/15972446177842",
    3: "https://ok.ru/video/15972446833202",
    4: "https://ok.ru/video/15972447423026",
    5: "https://ok.ru/video/15972448078386",
    6: "https://ok.ru/video/15972448471602",
    7: "https://ok.ru/video/15972448995890",
    8: "https://ok.ru/video/15972449651250"
}

async def process_episode(ep_num: int, url: str):
    await db.init_db()
    existing = await db.get_episode(DORAMA_ID, ep_num)
    if existing:
        print(f"⏩ {ep_num}-qism allaqachon bazada mavjud, o'tkazib yuborildi.")
        return

    dest_file = TEMP_DIR / f"ovchi_itlar_ep{ep_num}.mp4"

    # 1. Download if not exists
    if not dest_file.exists() or os.path.getsize(dest_file) < 100 * 1024 * 1024:
        print(f"\n==========================================")
        print(f"📥 {ep_num}-QISM YUKLANMOQDA: {url}")
        print(f"==========================================")
        cmd = [
            "yt-dlp",
            "-f", "hls-1544/hls-1489/full/best",
            "-o", str(dest_file),
            url,
            "--no-playlist"
        ]
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print(f"❌ Yuklab olishda xatolik: {res.returncode}")
            return

    file_size = os.path.getsize(dest_file)
    print(f"\n🚀 {ep_num}-QISMNI TELEGRAMGA YUKLASH (12 WORKERS)... Hajmi: {file_size / (1024*1024):.1f} MB")

    try:
        msg_id, file_id = await upload_episode(
            dorama_id=DORAMA_ID,
            title=TITLE,
            ep_num=ep_num,
            file_path=dest_file,
            poster_path=None
        )

        await db.add_episode(
            dorama_id=DORAMA_ID,
            episode_number=ep_num,
            channel_message_id=msg_id,
            file_id=file_id or "",
            file_size=file_size,
            quality="1080p"
        )
        # Update quality to 1080p
        import sqlite3
        c = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
        c.execute("UPDATE episodes SET quality = '1080p' WHERE dorama_id = ? AND episode_number = ?", (DORAMA_ID, ep_num))
        c.commit()
        c.close()

        print(f"🎉 {ep_num}-QISM MUVAFFAQIYATLI TELEGRAMGA YUKLANDI VA BAZAGA QO'SHILDI! Msg ID: {msg_id}")

        # Delete local file after successful upload to free space
        try:
            dest_file.unlink()
            print(f"🧹 Mahalliy disk tozalandi: {dest_file.name}")
        except Exception:
            pass

    except Exception as e:
        print(f"❌ Telegramga yuklashda xatolik ({ep_num}-qism): {e}")

async def main():
    await client.start()
    print("🚀 Telethon ishga tushdi. Navbatdagi qismlar yuklanmoqda...")

    for ep_num in sorted(EPISODE_URLS.keys()):
        url = EPISODE_URLS[ep_num]
        await process_episode(ep_num, url)

    print("\n🏁 BARCHA MAVJUD QISMLAR YUKLANDI VA BAZAGA UL㚅NDI!")

if __name__ == "__main__":
    asyncio.run(main())
