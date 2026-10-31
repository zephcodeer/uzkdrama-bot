import sys, os, asyncio
sys.path.insert(0, os.path.abspath("."))
import database

async def main():
    queries = [
        "O'n Ikki Farishta",
        "12 ta farishta",
        "rux",
        "yovuz rux",
        "yovuz ruh",
        "doktor x",
        "doktor",
        "Doctor X",
        "Yuragimni quvvatla",
        "yuragimni quvatla"
    ]

    for q in queries:
        res = await database.search_doramas(q)
        print(f"Query: '{q}' -> Found {len(res)} results:")
        for r in res[:3]:
            print(f"   [{r['code']}] {r['title']} (aliases: {r.get('aliases')})")

asyncio.run(main())
