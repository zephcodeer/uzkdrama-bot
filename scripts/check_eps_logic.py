import sys, os
sys.path.insert(0, r"E:\Agent\Drama Bot")
import database as db
import asyncio

async def main():
    # Check dorama 101 which is Ongoing
    eps = await db.get_episodes(101)
    print("Dorama 101 episodes:", len(eps), [e['episode_number'] for e in eps])
    
    # Check dorama 168 which is Ongoing (total 16, count 5)
    eps168 = await db.get_episodes(168)
    print("Dorama 168 episodes:", len(eps168), [e['episode_number'] for e in eps168])

asyncio.run(main())
