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
    m = await client.get_messages(config.STORAGE_CHANNEL_ID, ids=5370)
    await client.disconnect()

    assert m and m.document, "Message 5370 or document not found"
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
        f"TG 5370: size={fsize} | dur={dur}s | res={w}x{h} | fname={fname!r} | text={m.text!r}"
    )

    quality = "1080p" if (w and w >= 1900) or (h and h >= 1000) else "720p"

    d501 = await db.get_dorama_by_code(501)
    assert d501, "Code 501 not found"

    await db.add_episode(
        dorama_id=d501["id"],
        episode_number=3,
        channel_message_id=5370,
        file_size=fsize,
        quality=quality,
    )

    conn = sqlite3.connect("doramas.db")
    conn.execute(
        "UPDATE doramas SET total_episodes = 4, status = 'Ongoing' WHERE id = ?",
        (d501["id"],),
    )
    conn.commit()
    row = conn.execute(
        "SELECT code, title, total_episodes, status FROM doramas WHERE code = 501"
    ).fetchone()
    conn.close()
    print(f"Added Code 501 Ep 3 -> msg 5370 ({quality}). Row: {row}")


if __name__ == "__main__":
    asyncio.run(main())
