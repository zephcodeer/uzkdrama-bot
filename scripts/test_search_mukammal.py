import sys, os, asyncio
sys.path.insert(0, r"E:\Agent\Drama Bot")
import database as db

async def main():
    queries = [
        "Mukammal ish",
        "mukammal",
        "Dead-End Job",
        "Oxiri yo'q ish",
        "480"
    ]
    for q in queries:
        res = await db.search_doramas(q)
        print(f"Query: '{q}' -> Found {len(res)} results:")
        for r in res[:2]:
            print(f"  [{r['code']}] {r['title']} (status: {r.get('status')}, episodes: {r.get('total_episodes')})")

    # verify episodes
    eps = await db.get_episodes_by_code(480)
    print("Episodes for 480:", [(e['episode_number'], e['channel_message_id']) for e in eps])

asyncio.run(main())
