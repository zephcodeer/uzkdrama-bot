import asyncio, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\Agent\Drama Bot')
from database import search_doramas

async def test():
    for q in ['yuragimni quvatla', 'yuragimni quvvatla', '242']:
        res = await search_doramas(q)
        top = f"[{res[0]['code']}] {res[0]['title']}" if res else 'NONE'
        print(f"{q:20} -> Found: {len(res):2} | Top: {top}")

if __name__ == '__main__':
    asyncio.run(test())
