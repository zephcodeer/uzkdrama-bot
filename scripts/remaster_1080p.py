import asyncio
import os
import sys
import shutil
from pathlib import Path

# Add project root
sys.path.append(r"E:\Agent\Drama Bot")
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import database as db
from uploader import upload_episode, client
from turbo_downloader import parallel_download
from nvenc_upscaler import upscale_to_1080p

TARGET_EPS = [
    (4, "https://sherlar.net/serial/doktorx/4.mp4"),
    (5, "https://k1.qnbuz.net/doktorx/5.mp4")
]

DORAMA_ID = 1
TITLE = "Doktor X , Oq Mafia"
POSTER = Path(r"E:\Agent\Drama Bot\posters\doktor_x_clean_poster.jpg")
TEMP_DIR = Path(r"E:\Agent\Drama Bot\temp_downloads")


async def main():
    TEMP_DIR.mkdir(exist_ok=True, parents=True)
    await db.init_db()
    await client.start()

    for ep_num, url in TARGET_EPS:
        raw_file = TEMP_DIR / f"raw_ep_{ep_num}.mp4"
        remastered_file = TEMP_DIR / f"doktor_x_ep_{ep_num}_1080p.mp4"

        print(f"\n{'=' * 50}")
        print(f"🚀 {ep_num}-QISMNI 1080p FULL HD REMASTER QILISH BOSHLANDI")
        print(f"Manba: {url}")
        print(f"{'=' * 50}")

        # 1. 16-oqimli turbo yuklab olish
        if not raw_file.exists() or os.path.getsize(raw_file) < 500 * 1024 * 1024:
            print(f"📥 16-oqimli parallel yuklash: {raw_file.name}")
            parallel_download(url, raw_file, referer="https://uzmovi.me/", num_workers=16)

        # 2. NVIDIA GeForce RTX 3060 NVENC 1080p Upscale
        if not remastered_file.exists() or os.path.getsize(remastered_file) < 500 * 1024 * 1024:
            print(f"⚡️ NVENC apparat tezlatgichida 1080p Full HD ga konvertatsiya...")
            upscale_to_1080p(raw_file, remastered_file, use_nvenc=True)

        remastered_size = os.path.getsize(remastered_file)
        print(f"\n🚀 TELEGRAM MAXFIY KANALGA 1080p YUKLASH... Hajmi: {remastered_size / (1024*1024):.1f} MB")

        try:
            msg_id, file_id = await upload_episode(
                dorama_id=DORAMA_ID,
                title=f"{TITLE} [1080p Full HD]",
                ep_num=ep_num,
                file_path=remastered_file,
                poster_path=POSTER
            )

            # DB dagi eski yozuvni yangilash
            import aiosqlite
            from config import DB_PATH
            async with aiosqlite.connect(DB_PATH) as conn:
                await conn.execute("""
                    UPDATE episodes 
                    SET channel_message_id = ?, file_id = ?, file_size = ?, quality = '1080p'
                    WHERE dorama_id = ? AND episode_number = ?
                """, (msg_id, file_id, remastered_size, DORAMA_ID, ep_num))
                await conn.commit()

            print(f"\n🎉 {ep_num}-QISM 1080p FULL HD DA TELEGRAM VA BAZADA YANGILANDI! (Msg ID: {msg_id})")

        except Exception as e:
            print(f"❌ Telegramga yuklashda xatolik: {e}")
        finally:
            for f in [raw_file, remastered_file]:
                if f.exists():
                    try:
                        f.unlink()
                        print(f"🧹 Tozalandi: {f.name}")
                    except Exception:
                        pass

    print("\n🏁 4 VA 5-QISMLAR 1080p FULL HD SIFATIDA TAYYOR BO'LDI!")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
