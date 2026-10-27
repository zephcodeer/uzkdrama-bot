import asyncio
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.append(r"E:\Agent\Drama Bot")
import config
from telethon import TelegramClient

async def inspect():
    c = TelegramClient(r'E:\Agent\Drama Bot\ojiz_session', config.API_ID, config.API_HASH)
    await c.connect()

    ch = await c.get_entity("@ojiz_1")
    for mid in range(13, 21):
        m = await c.get_messages(ch, ids=mid)
        ep = mid - 12
        print(f"Ep {ep} (Msg {mid}): {m.file.size / (1024*1024):.1f}MB | Name: {m.file.name}")
        print(f"   Caption: {repr(m.text)}")

    await c.disconnect()

asyncio.run(inspect())
