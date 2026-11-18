import asyncio
import os
from pathlib import Path
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

TG_AGENT_ROOT = Path(r"C:\Users\MuhammadSodiq\.gemini\antigravity\scratch\TG AI PERSON")
DRAMA_BOT_ROOT = Path(r"E:\Agent\Drama Bot")
sys.path.insert(0, str(TG_AGENT_ROOT / "src"))
sys.path.insert(0, str(DRAMA_BOT_ROOT))

from tg_agent.client import build_telegram_client  # noqa: E402
from tg_agent.config import load_settings  # noqa: E402


async def main():
    os.chdir(TG_AGENT_ROOT)
    settings = load_settings()
    client = build_telegram_client(settings)
    await client.connect()
    try:
        m = await client.get_messages(-1004336427887, ids=5612)
    finally:
        await client.disconnect()

    assert m and m.document, "Message 5612 or document not found"
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
        f"TG 5612: size={fsize} | dur={dur}s | res={w}x{h} | fname={fname!r} | text={m.text!r}"
    )

    quality = "1080p" if (w and w >= 1900) or (h and h >= 1000) else "720p"

    conn = sqlite3.connect(DRAMA_BOT_ROOT / "doramas.db")
    cur = conn.cursor()
    d483 = cur.execute("SELECT id, code, title FROM doramas WHERE code = 483").fetchone()
    assert d483, "Code 483 not found"
    dorama_id = d483[0]

    col = cur.execute(
        "SELECT dorama_id, episode_number FROM episodes WHERE channel_message_id = 5612 AND dorama_id != ?",
        (dorama_id,),
    ).fetchall()
    assert not col, f"Cross-dorama collision on 5612: {col}"

    cur.execute(
        """
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_id, file_size, quality)
        VALUES (?, 9, 5612, '', ?, ?)
        ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
            channel_message_id = excluded.channel_message_id,
            file_size = excluded.file_size,
            quality = excluded.quality
        """,
        (dorama_id, fsize, quality),
    )
    cur.execute(
        "UPDATE doramas SET total_episodes = 12, status = 'Ongoing' WHERE id = ?",
        (dorama_id,),
    )
    conn.commit()
    row = cur.execute(
        "SELECT code, title, total_episodes, status FROM doramas WHERE id = ?",
        (dorama_id,),
    ).fetchone()
    ep9 = cur.execute(
        "SELECT episode_number, channel_message_id, quality, file_size FROM episodes WHERE dorama_id = ? AND episode_number = 9",
        (dorama_id,),
    ).fetchone()
    conn.close()
    print(f"Updated Code 483 Ep 9: {ep9} | Dorama: {row}")


if __name__ == "__main__":
    asyncio.run(main())
