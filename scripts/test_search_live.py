import asyncio, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import search_doramas

async def test():
    queries = [
        "rux",
        "ruh",
        "yovuz ru",
        "yovuz rux",
        "yovuz ruh",
        "darbadar rux",
        "Doktor x",
        "Doktor X",
        "O'n Ikki Farishta",
        "12 ta farishta",
        "12 Farishta",
        "on ikki farishta",
        "To'qqiz dumli tulki",
        "9 dumli tulki",
        "Xalk 1",
        "Xalk 2",
        "yigirma besh yigirma bir",
        "25 21",
        "100 kunlik yolg'on",
        "yuz kunlik yolg'on"
    ]
    for q in queries:
        res = await search_doramas(q)
        top = f"[{res[0]['code']}] {res[0]['title']}" if res else "NONE"
        print(f"Query: {q:25} -> Found: {len(res):2} | Top: {top}")

if __name__ == '__main__':
    asyncio.run(test())
