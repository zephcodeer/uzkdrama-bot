import sys, os, asyncio
sys.path.insert(0, r"E:\Agent\Drama Bot")
import database as db

async def main():
    queries = [
        "Mening dilim mening boshlig'im",
        "Mening dilim",
        "Mening yulduzim va boshlig'im",
        "Mening idolim mening boshlig'im",
        "301"
    ]
    for q in queries:
        res = await db.search_doramas(q, limit=2)
        print(f"Query: '{q}' -> Found {len(res)} results:")
        for r in res:
            print(f"   [{r['code']}] {r['title']}")

asyncio.run(main())
