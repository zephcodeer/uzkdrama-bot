import asyncio
import os
import sys
import subprocess
import time
import base64
import urllib.request
import re
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
from uploader import upload_episode, client

DORAMA_ID = 35
TITLE = "Ovchi itlar 2-fasl"
TEMP_DIR = Path(r"E:\Agent\Drama Bot\temp_downloads")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

EPISODES = {
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
            
    # Fallback to m3u8
    m3u8 = decode_doramalar(b64_matches[0])
    return m3u8

async def download_episode(ep_num: int, info: dict, dest_file: Path):
    if dest_file.exists() and os.path.getsize(dest_file) > 50 * 1024 * 1024:
        print(f"⏩ {ep_num}-qism fayli allaqachon diskda bor ({os.path.getsize(dest_file)/(1024*1024):.1f} MB)")
        return True

    print(f"\n==========================================")
    print(f"📥 2-FASL {ep_num}-QISM YUKLANMOQDA: {info['url']}")
    print(f"==========================================")

    if info["type"] == "ok":
        cmd = [
            "yt-dlp",
            "-f", "hls-1544/hls-1489/full/hls-764/best",
            "-o", str(dest_file),
            info["url"],
            "--no-playlist"
        ]
        res = subprocess.run(cmd)
        return res.returncode == 0
    elif info["type"] == "doramalar":
        try:
            stream_url = resolve_doramalar_stream(info["url"])
            print(f"Direct stream URL topildi: {stream_url[:80]}...")
            cmd = [
                "yt-dlp",
                "--add-header", "Referer:https://doramalar.net/",
                "-o", str(dest_file),
                stream_url,
                "--no-playlist"
            ]
            res = subprocess.run(cmd)
            return res.returncode == 0
        except Exception as e:
            print(f"❌ Doramalar stream xatosi: {e}")
            return False

async def process_episode(ep_num: int, info: dict):
    await db.init_db()
    existing = await db.get_episode(DORAMA_ID, ep_num)
    if existing:
        print(f"⏩ 2-fasl {ep_num}-qism allaqachon bazada mavjud, o'tkazib yuborildi.")
        return

    dest_file = TEMP_DIR / f"ovchi_itlar_s2_ep{ep_num}.mp4"
    success = await download_episode(ep_num, info, dest_file)
    if not success or not dest_file.exists():
        print(f"❌ 2-fasl {ep_num}-qismni yuklab olish muvaffaqiyatsiz bo'ldi.")
        return

    file_size = os.path.getsize(dest_file)
    print(f"\n🚀 2-FASL {ep_num}-QISMNI TELEGRAMGA YUKLASH (12 WORKERS)... Hajmi: {file_size / (1024*1024):.1f} MB")

    try:
        msg_id, file_id = await upload_episode(
            dorama_id=DORAMA_ID,
            title=TITLE,
            ep_num=ep_num,
            file_path=dest_file,
            poster_path=None
        )

        quality = "1080p" if info["type"] == "ok" else "720p"
        await db.add_episode(
            dorama_id=DORAMA_ID,
            episode_number=ep_num,
            channel_message_id=msg_id,
            file_id=file_id or "",
            file_size=file_size,
            quality=quality
        )

        import sqlite3
        c = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
        c.execute("UPDATE episodes SET quality = ? WHERE dorama_id = ? AND episode_number = ?", (quality, DORAMA_ID, ep_num))
        c.commit()
        c.close()

        print(f"🎉 2-FASL {ep_num}-QISM MUVAFFAQIYATLI TELEGRAMGA YUKLANDI VA BAZAGA QO'SHILDI! Msg ID: {msg_id}")

        try:
            dest_file.unlink()
            print(f"🧹 Mahalliy disk tozalandi: {dest_file.name}")
        except Exception:
            pass

    except Exception as e:
        print(f"❌ Telegramga yuklashda xatolik (2-fasl {ep_num}-qism): {e}")

async def wait_for_season_1():
    print("⏳ 1-fasl to'liq yuklanishi kutilmoqda...")
    import sqlite3
    while True:
        c = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
        cur = c.cursor()
        cur.execute("SELECT COUNT(*) FROM episodes WHERE dorama_id = 18")
        count = cur.fetchone()[0]
        c.close()
        if count >= 8:
            print(f"✅ 1-faslning barcha 8 ta qismi yuklandi! 2-fasl boshlanmoqda...")
            break
        print(f"1-fasldan hozircha {count}/8 qism yuklangan. 15 soniya kutilmoqda...")
        await asyncio.sleep(15)

async def main():
    await wait_for_season_1()
    # Pause 5s to ensure previous telethon session is fully released
    await asyncio.sleep(5)
    await client.start()
    print("🚀 Telethon ishga tushdi. 2-Fasl qismlari yuklanmoqda...")

    for ep_num in sorted(EPISODES.keys()):
        await process_episode(ep_num, EPISODES[ep_num])

    print("\n🏁 2-FASLNING BARCHA QISMLARI MUVAFFAQIYATLI YUKLANDI!")

if __name__ == "__main__":
    asyncio.run(main())
