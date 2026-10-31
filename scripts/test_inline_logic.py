import sys, os, asyncio
sys.path.insert(0, r"E:\Agent\Drama Bot")
import database as db
import aiosqlite

async def test_search(q: str):
    q = q.strip()
    if len(q) >= 2:
        return await db.search_doramas(q, limit=20)
    elif len(q) == 1:
        async with aiosqlite.connect(db.DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            pattern = f"{q}%"
            async with conn.execute(
                "SELECT * FROM doramas WHERE code LIKE ? OR title LIKE ? ORDER BY views DESC LIMIT 20",
                (pattern, pattern)
            ) as cur:
                rows = await cur.fetchall()
                return [dict(r) for r in rows]
    else:
        return await db.get_latest_doramas(limit=20)

async def main():
    for test_q in ["", "4", "48", "480", "mukammal", "rux", "12 farishta"]:
        res = await test_search(test_q)
        print(f"Query: '{test_q}' -> {len(res)} results")
        if res:
            print(f"   First: [{res[0]['code']}] {res[0]['title']}")

asyncio.run(main())
