import asyncio
import sqlite3
import sys
from telethon import TelegramClient

sys.stdout.reconfigure(encoding="utf-8")

import config  # noqa: E402
import database as db  # noqa: E402


async def main():
    client = TelegramClient("ojiz_session", config.API_ID, config.API_HASH)
    await client.connect()
    m = await client.get_messages(config.STORAGE_CHANNEL_ID, ids=5328)
    await client.disconnect()

    assert m and m.document, "Message 5328 or document not found"
    fsize = m.document.size
    dur = w = h = fname = None
    for attr in m.document.attributes:
        cls = attr.__class__.__name__
        if cls == "DocumentAttributeVideo":
            dur = getattr(attr, "duration", None)
            w = getattr(attr, "w", None)
            h = getattr(attr, "h", None)
        elif cls == "DocumentAttributeFilename":
            fname = getattr(attr, "file_name", None)

    print(
        f"TG 5328: size={fsize} | dur={dur}s | res={w}x{h} | fname={fname!r} | text={m.text!r}"
    )

    text_lower = (m.text or "").lower()
    assert "52" in text_lower or (fname and "52" in fname), f"Unexpected message text: {m.text!r}"

    quality = "1080p" if (w and w >= 1900) or (h and h >= 1000) or "1080" in text_lower else "720p"

    d481 = await db.get_dorama_by_code(481)
    assert d481, "Code 481 not found"

    await db.add_episode(
        dorama_id=d481["id"],
        episode_number=52,
        channel_message_id=5328,
        file_size=fsize,
        quality=quality,
    )

    conn = sqlite3.connect("doramas.db")
    row = conn.execute(
        "SELECT code, title, total_episodes, status FROM doramas WHERE code = 481"
    ).fetchone()
    conn.close()
    print(f"Added Code 481 Ep 52 -> msg 5328 ({quality}). Row: {row}")


if __name__ == "__main__":
    asyncio.run(main())
