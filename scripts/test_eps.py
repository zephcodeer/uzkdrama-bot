import sys, os, asyncio
sys.path.insert(0, r"E:\Agent\Drama Bot")
import database as db

async def main():
    d = await db.get_dorama_by_code(480)
    print("Dorama:", d['id'], d['code'], d['title'])
    eps = await db.get_episodes(d['id'])
    print("Episodes:", [(e['episode_number'], e['channel_message_id']) for e in eps])

asyncio.run(main())
