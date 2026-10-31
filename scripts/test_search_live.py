import asyncio, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import search_doramas

async def test():
    queries = [
        "351",
        "Bugun barchasi sotildi",
        "Chekka qishloqdagi doktor",
        "Dr Romantic",
        "Sichqon",
        "Mouse",
        "Ertaga",
        "One Ordinary Day",
        "Oddiy bir kun",
        "383",
        "Ditto",
        "Parazitlar",
        "Parasite",
        "479",
        "Mening Ilohiy Elchim",
        "rux",
        "12 ta farishta"
    ]
    for q in queries:
        res = await search_doramas(q)
        top = f"[{res[0]['code']}] {res[0]['title']}" if res else "NONE"
        print(f"Query: {q:28} -> Found: {len(res):2} | Top: {top}")

if __name__ == '__main__':
    asyncio.run(test())
