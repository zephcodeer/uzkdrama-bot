import asyncio
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, "E:/Agent/Drama Bot")
import database as db

async def main():
    d = await db.get_dorama_by_code(483)
    if not d:
        sys.exit("Code 483 topilmadi!")
    d_id = d['id']

    await db.add_episode(
        dorama_id=d_id,
        episode_number=6,
        channel_message_id=5308,
        quality='720p'
    )

    con = sqlite3.connect("E:/Agent/Drama Bot/doramas.db")
    con.execute("UPDATE doramas SET total_episodes = 12, status = 'Ongoing' WHERE id = ?", (d_id,))
    con.commit()
    row = con.execute("SELECT id, code, title, total_episodes, status FROM doramas WHERE id = ?", (d_id,)).fetchone()
    eps = con.execute("SELECT COUNT(*) FROM episodes WHERE dorama_id = ?", (d_id,)).fetchone()[0]
    con.close()
    print(f"Updated Code 483: {row} | Uploaded eps: {eps}")

if __name__ == '__main__':
    asyncio.run(main())
