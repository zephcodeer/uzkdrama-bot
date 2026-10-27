import asyncio
import os
import sys
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

DORAMA_ID = 18
TITLE = "Ovchi itlar 1-fasl"
POSTER_URL = "https://m.media-amazon.com/images/M/MV5BZWYwMWRiZWMtYzg4Ni00ZmM5LTlhNWItNzNjMjIzZDA4NDc5XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
POSTER_PATH = Path(r"E:\Agent\Drama Bot\posters\ovchi_itlar_poster.jpg")
VIDEO_PATH = Path(r"E:\Agent\Drama Bot\temp_downloads\ovchi_itlar_ep1.mp4")

async def main():
    await db.init_db()

    # 1. Start Telethon
    await client.start()
    print("\n🚀 1-QISMNI TELEGRAM SAQLASH KANALIGA YUKLASH BOSHLANDI (12 Parallel Worker)...")
    file_size = os.path.getsize(VIDEO_PATH)
    print(f"Hajmi: {file_size / (1024*1024):.1f} MB")

    msg_id, file_id = await upload_episode(
        dorama_id=DORAMA_ID,
        title=TITLE,
        ep_num=1,
        file_path=VIDEO_PATH,
        poster_path=None
    )

    print(f"✅ Telegramga yuklandi! Msg ID: {msg_id}")

    # 3. Save to database
    await db.add_episode(
        dorama_id=DORAMA_ID,
        episode_number=1,
        channel_message_id=msg_id,
        file_id=file_id or "",
        file_size=file_size,
        quality="1080p"
    )

    print("🎉 BAZAGA 1-QISM 1080p FULL HD SIFATDA QO'SHILDI!")

if __name__ == "__main__":
    asyncio.run(main())
