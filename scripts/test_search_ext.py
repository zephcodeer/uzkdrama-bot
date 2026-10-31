import sys, os, asyncio
sys.path.insert(0, r"E:\Agent\Drama Bot")
import database as db

# Let's test search with the proposed change
async def search_test(query: str, limit: int = 10):
    q = (query or "").strip()
    if not q:
        return await db.get_latest_doramas(limit=limit)
    
    # If 1 char and not digit, simple prefix match
    if len(q) == 1 and not q.isdigit():
        import aiosqlite
        async with aiosqlite.connect(db.DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM doramas WHERE title LIKE ? ORDER BY views DESC LIMIT ?",
                (f"{q}%", limit)
            ) as cur:
                rows = await cur.fetchall()
                return [dict(r) for r in rows]

    return await db.search_doramas(q, limit=limit)

async def main():
    for q in ["", "4", "48", "480", "m", "mu", "mukammal"]:
        res = await search_test(q)
        print(f"Query: '{q}' -> {len(res)} results")
        if res:
            print(f"   Top: [{res[0]['code']}] {res[0]['title']}")

asyncio.run(main())
