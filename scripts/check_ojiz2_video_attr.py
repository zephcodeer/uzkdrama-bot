import asyncio
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.append(r"E:\Agent\Drama Bot")
import config
from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeVideo

async def check():
    c = TelegramClient(r'E:\Agent\Drama Bot\ojiz_session', config.API_ID, config.API_HASH)
    await c.connect()

    ch = await c.get_entity("@ojiz_1")
    m = await c.get_messages(ch, ids=13)
    for attr in m.media.document.attributes:
        if isinstance(attr, DocumentAttributeVideo):
            print(f"Video attributes: {attr.w}x{attr.h}, duration: {attr.duration}s, supports_streaming: {attr.supports_streaming}")

    await c.disconnect()

asyncio.run(check())
