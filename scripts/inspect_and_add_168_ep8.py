import asyncio
import sqlite3
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, "E:/Agent/Drama Bot")
import config
import database as db
from telethon import TelegramClient

async def main():
    client = TelegramClient(os.path.join(config.BASE_DIR, 'ojiz_session'), config.API_ID, config.API_HASH)
    await client.connect()
    m = await client.get_messages(config.STORAGE_CHANNEL_ID, ids=5310)
    if not m:
        await client.disconnect()
        sys.exit("Msg 5310 topilmadi!")
    dur = getattr(m.file, 'duration', None)
    size = getattr(m.file, 'size', None)
    fn = m.file.name if m.file else None
    print(f"Msg 5310: dur={dur}s ({dur//60 if dur else 0}m), size={size}, fn={fn}")
    print(f"Caption:\n{m.message}\n" + "-"*40)
    await client.disconnect()

    d = await db.get_dorama_by_code(168)
    if not d:
        sys.exit("Code 168 topilmadi!")
    d_id = d['id']

    quality = '1080p' if (size and size > 900_000_000) else '720p'
    await db.add_episode(
        dorama_id=d_id,
        episode_number=8,
        channel_message_id=5310,
        quality=quality
    )

    con = sqlite3.connect("E:/Agent/Drama Bot/doramas.db")
    con.execute("UPDATE doramas SET total_episodes = 16, status = 'Ongoing' WHERE id = ?", (d_id,))
    con.commit()
    eps = con.execute("SELECT episode_number, channel_message_id, quality FROM episodes WHERE dorama_id = ? ORDER BY episode_number", (d_id,)).fetchall()
    con.close()
    print(f"Code 168 total uploaded: {len(eps)}/16 | Ep 8: {eps[-1]}")

if __name__ == '__main__':
    asyncio.run(main())
