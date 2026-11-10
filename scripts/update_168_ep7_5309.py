import asyncio
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, "E:/Agent/Drama Bot")
import database as db

async def main():
    d = await db.get_dorama_by_code(168)
    if not d:
        sys.exit("Code 168 topilmadi!")
    d_id = d['id']

    await db.add_episode(
        dorama_id=d_id,
        episode_number=7,
        channel_message_id=5309,
        quality='1080p'
    )

    con = sqlite3.connect("E:/Agent/Drama Bot/doramas.db")
    con.execute("UPDATE doramas SET total_episodes = 16, status = 'Ongoing' WHERE id = ?", (d_id,))
    con.commit()
    row = con.execute("SELECT id, code, title, total_episodes, status FROM doramas WHERE id = ?", (d_id,)).fetchone()
    ep7 = con.execute("SELECT episode_number, channel_message_id, quality FROM episodes WHERE dorama_id = ? AND episode_number = 7", (d_id,)).fetchone()
    con.close()
    print(f"Updated Code 168: {row} | Ep 7: {ep7}")

if __name__ == '__main__':
    asyncio.run(main())
