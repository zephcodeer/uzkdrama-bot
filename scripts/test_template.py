import sys, os, asyncio
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Agent\Drama Bot")
import database as db

async def test_template(code: int):
    d = await db.get_dorama_by_code(code)
    if not d:
        print(f"Code {code} not found")
        return
    eps = await db.get_episodes(d["id"])
    raw_status = (d.get("status") or "").strip()
    is_ongoing = "ongo" in raw_status.lower()
    total_ep = d.get("total_episodes") or len(eps)
    
    if is_ongoing and len(eps) < total_ep:
        ep_info = f"1–{len(eps)} qismlar (davomi chiqishi bilan qo'shib boriladi)"
    elif len(eps) > 1:
        ep_info = f"1–{len(eps)} qismlar (barcha qismlar to'liq yuklangan)"
    else:
        ep_info = "To'liq film/dorama yuklangan"
        
    user_msg = (
        f"Assalomu alaykum! <b>«{d['title']}»</b> doramasi allaqachon botimizda mavjud! 🎉\n\n"
        f"🔑 <b>Kino kodi:</b> <code>{code}</code>\n"
        f"🎞 <b>Mavjud:</b> {ep_info}.\n\n"
        f"Botga <b>{code}</b> deb yozib yoki qidiruv orqali bemalol tomosha qilishingiz mumkin. Maroqli hordiq tilaymiz! 🎬🍿"
    )
    print("--- GENERATED MESSAGE ---")
    print(user_msg)

async def main():
    await test_template(168)
    await test_template(101)
    await test_template(480)

asyncio.run(main())
