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
        # Check if already in DB
        existing = await db.get_episode(DORAMA_ID, ep_num)
        if existing:
            print(f"⏩ {ep_num}-qism allaqachon bazada mavjud, o'tkazib yuborildi.")
            continue

        temp_file = TEMP_DIR / f"doktor_x_ep_{ep_num}.mp4"

        # Agar test_ep4 to'liq yuklangan bo'lsa shuni olamiz
        test_file = TEMP_DIR / "test_ep4.mp4"
        if ep_num == 4 and test_file.exists() and os.path.getsize(test_file) > 550 * 1024 * 1024:
            print("📦 Allaqachon yuklangan test_ep4.mp4 ishlatilmoqda!")
            if temp_file.exists():
                temp_file.unlink()
            shutil.move(str(test_file), str(temp_file))
        else:
            print(f"\n==========================================")
            print(f"🚀 {ep_num}-QISM: 16 OQIMLI TURBO YUKLASH BOSHLANDI...")
            print(f"URL: {url}")
            print(f"==========================================")
            parallel_download(url, temp_file, referer="https://uzmovi.me/", num_workers=16)

        file_size = os.path.getsize(temp_file)
        print(f"\n🚀 {ep_num}-QISMNI TELEGRAMGA TURBO YUKLASH (12 WORKERS)... Hajmi: {file_size / (1024*1024):.1f} MB")
        try:
            msg_id, file_id = await upload_episode(
                dorama_id=DORAMA_ID,
                title=TITLE,
                ep_num=ep_num,
                file_path=temp_file,
                poster_path=POSTER
            )

            # DB ga yozish
            await db.add_episode(
                dorama_id=DORAMA_ID,
                episode_number=ep_num,
                channel_message_id=msg_id,
                file_id=file_id,
                file_size=file_size,
                quality="720p"
            )
            print(f"\n🎉 {ep_num}-QISM TELEGRAM VA BAZAGA JOYLANDI! (Msg ID: {msg_id})")

        except Exception as e:
            print(f"❌ Telegramga yuklashda xatolik: {e}")
        finally:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                    print(f"🧹 Vaqtinchalik fayl tozalandi: {temp_file.name}")
                except Exception:
                    pass

    print("\n🏁 BARCHA 4 VA 5-QISMLAR MUVAFFAQIYATLI YUKLANDI!")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
