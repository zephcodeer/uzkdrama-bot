import asyncio
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, "E:/Agent/Drama Bot")
import database as db

async def main():
    d501 = await db.get_dorama_by_code(501)
    if not d501:
        sys.exit("Code 501 topilmadi!")

    d484 = await db.get_dorama_by_code(484)
    if not d484:
        sys.exit("Code 484 topilmadi!")

    # 1. Qo'shnim Franchesko (Code 501) - Ep 2 -> 5311
    await db.add_episode(
        dorama_id=d501['id'],
        episode_number=2,
        channel_message_id=5311,
        quality='1080p'
    )

    # 2. Erta bahor / Ilk bahor (Code 484) - Ep 23 -> 5312
    await db.add_episode(
        dorama_id=d484['id'],
        episode_number=23,
        channel_message_id=5312,
        quality='720p'
    )

    # Restore planned total_episodes metadata after add_episode updates count
    con = sqlite3.connect("E:/Agent/Drama Bot/doramas.db")
    con.execute("UPDATE doramas SET total_episodes = 4, status = 'Ongoing' WHERE id = ?", (d501['id'],))
    con.execute("UPDATE doramas SET total_episodes = 24, status = 'Tugallangan' WHERE id = ?", (d484['id'],))
    con.commit()

    eps501 = con.execute("SELECT episode_number, channel_message_id, quality FROM episodes WHERE dorama_id=? ORDER BY episode_number", (d501['id'],)).fetchall()
    eps484 = con.execute("SELECT episode_number, channel_message_id, quality FROM episodes WHERE dorama_id=? ORDER BY episode_number", (d484['id'],)).fetchall()
    con.close()

    print(f"Code 501 uploaded ({len(eps501)}/4): {eps501}")
    missing_484 = sorted(set(range(1, 25)) - {e[0] for e in eps484})
    print(f"Code 484 uploaded ({len(eps484)}/24): missing={missing_484}, ep23={next((e for e in eps484 if e[0]==23), None)}")

if __name__ == '__main__':
    asyncio.run(main())
