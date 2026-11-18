import asyncio
import os
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding="utf-8")

TG_AGENT_ROOT = Path(r"C:\Users\MuhammadSodiq\.gemini\antigravity\scratch\TG AI PERSON")
sys.path.insert(0, str(TG_AGENT_ROOT / "src"))

from tg_agent.client import build_telegram_client  # noqa: E402
from tg_agent.config import load_settings  # noqa: E402


async def main():
    os.chdir(TG_AGENT_ROOT)
    settings = load_settings()
    client = build_telegram_client(settings)
    await client.connect()
    try:
        msg = await client.send_message("@uzkdrama_app", "/update")
        print(f"Sent /update to @uzkdrama_app (msg_id={msg.id})", flush=True)
        for _ in range(5):
            await asyncio.sleep(2.5)
            replies = await client.get_messages("@uzkdrama_app", limit=2)
            for r in replies:
                if r.id > msg.id:
                    txt = (r.text or "").replace("\n", " ")
                    print(f"Server response (id={r.id}): {txt[:200]}", flush=True)
                    if "MUVAFFAQIYATLI" in txt or "YANGILANISH" in txt and "tekshirilmoqda" not in txt.lower():
                        return
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
