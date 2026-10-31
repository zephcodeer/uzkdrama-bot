import sys, os
sys.path.insert(0, r"E:\Agent\Drama Bot")
import keyboards as kb
import database as db
import asyncio

async def main():
    eps = await db.get_episodes(101)
    d = await db.get_dorama_by_code(101)
    k = kb.get_episodes_keyboard(eps, dorama_id=d['id'], code=101)
    print("Keyboard buttons count:")
    for row in k.inline_keyboard:
        print([btn.text for btn in row])

asyncio.run(main())
