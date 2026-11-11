import asyncio
import os
import shutil
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, "E:/Agent/Drama Bot")
import database as db

async def main():
    # 1. Poster setup
    mdl_p = "E:/Agent/Drama Bot/posters/code_502_mdl.jpg"
    wiki_p = "E:/Agent/Drama Bot/posters/code_502_wiki.jpg"
    final_p = "E:/Agent/Drama Bot/posters/code_502.jpg"
    if os.path.exists(mdl_p):
        shutil.move(mdl_p, final_p)
    if os.path.exists(wiki_p):
        os.remove(wiki_p)

    # 2. Insert or update Dorama Code 502
    con = sqlite3.connect("E:/Agent/Drama Bot/doramas.db")
    cur = con.cursor()

    c502 = 502
    t502 = "Nanyang jumbog‘i (Archives: The Nanyang Mystery)"
    slug502 = "nanyang-jumbogi"
    genre502 = "Detektiv, Sarguzasht, Jangari, Sirli"
    year502 = 2026
    desc502 = (
        "Voqealar XX asr boshlarida Nanyang dengizi hududida yuz beradi. «Janubiy arxivlar» maxfiy byurosi agentlari "
        "Chjan Xayyan va Chjan Xaysya sirli qotilliklar hamda «Shafaq o‘ti» nomli zaharli o‘simlik bilan bog‘liq xavfli fitnani "
        "tergov qilishadi. Barcha dahshatli izlar ularni ochiq dengizdagi sirli va ulkan «Nanyang» kemasiga olib boradi."
    )
    poster502 = "posters/code_502.jpg"
    total502 = 33
    status502 = "Ongoing"
    country502 = "Xitoy"
    actors502 = "Zhang Xincheng (Chjan Sinchen), Ding Yuxi (Din Yuyusi), Jiang Peiyao, Fu Xinbo"
    cat502 = "china"
    aliases502 = "Nanyang jumbog'i, Nanyang jumbogi, Nanyang jumbog‘i, Archives: The Nanyang Mystery, Southern Archives, Janubiy arxivlar, 南部档案, Zhang Xincheng, Ding Yuxi"

    cur.execute("SELECT id FROM doramas WHERE code = ?", (c502,))
    ex = cur.fetchone()
    if ex:
        d_id = ex[0]
        cur.execute("""
            UPDATE doramas SET title=?, slug=?, genre=?, year=?, description=?, poster_url=?,
            total_episodes=?, status=?, country=?, actors=?, category=?, aliases=?
            WHERE id=?
        """, (t502, slug502, genre502, year502, desc502, poster502, total502, status502, country502, actors502, cat502, aliases502, d_id))
    else:
        cur.execute("""
            INSERT INTO doramas (code, title, slug, genre, year, description, poster_url, total_episodes, status, country, actors, category, aliases)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (c502, t502, slug502, genre502, year502, desc502, poster502, total502, status502, country502, actors502, cat502, aliases502))
        d_id = cur.lastrowid
    con.commit()
    con.close()

    # 3. Add Episodes 1..10 -> 5313..5322 via db.add_episode (guardrails active)
    for ep in range(1, 11):
        msg_id = 5312 + ep  # 1->5313 ... 10->5322
        await db.add_episode(dorama_id=d_id, episode_number=ep, channel_message_id=msg_id, quality='720p')

    # Restore planned total_episodes=33 and Ongoing
    con = sqlite3.connect("E:/Agent/Drama Bot/doramas.db")
    con.execute("UPDATE doramas SET total_episodes = 33, status = 'Ongoing' WHERE id = ?", (d_id,))
    con.commit()
    eps = con.execute("SELECT episode_number, channel_message_id FROM episodes WHERE dorama_id = ? ORDER BY episode_number", (d_id,)).fetchall()
    con.close()
    print(f"Code 502 created (id={d_id}): {len(eps)}/33 eps -> {eps[0]} .. {eps[-1]}")

if __name__ == '__main__':
    asyncio.run(main())
