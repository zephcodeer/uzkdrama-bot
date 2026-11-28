import asyncio
import os
import sys
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, "E:/Agent/Drama Bot")
import config
from telethon import TelegramClient

async def main():
    client = TelegramClient(os.path.join(config.BASE_DIR, 'temp_cmd'), config.API_ID, config.API_HASH)
    await client.connect()
    
    # Check messages 6064..6072
    msg_ids = list(range(6064, 6073))
    print(f"Checking messages {msg_ids[0]}..{msg_ids[-1]}...")
    msgs = await client.get_messages(config.STORAGE_CHANNEL_ID, ids=msg_ids)
    
    msg_info = {}
    for m in msgs:
        if not m:
            continue
        size = getattr(m.file, 'size', 0) if m.file else 0
        dur = getattr(m.file, 'duration', 0) if m.file else 0
        cap = (m.message or '').replace('\n', ' ')[:70]
        msg_info[m.id] = {'size': size, 'dur': dur, 'cap': cap}
        print(f"Msg {m.id}: dur={dur}s, size={size}, cap='{cap}'")
        
    await client.disconnect()

    # Now fix database
    conn = sqlite3.connect('E:/Agent/Drama Bot/doramas.db')
    cur = conn.cursor()
    
    # 1. Restore Yovuz va badavlat 2-fasl (code 453)
    cur.execute("SELECT id, code, title FROM doramas WHERE code=453")
    yvb = cur.fetchone()
    if yvb:
        yvb_id = yvb[0]
        cur.execute("UPDATE episodes SET channel_message_id=4725 WHERE dorama_id=? AND episode_number=2", (yvb_id,))
        print(f"Restored code 453 ep 2 to msg 4725")

    # 2. Check if Giper pichoq already exists
    cur.execute("SELECT id, code, title FROM doramas WHERE title LIKE '%Giper%' OR title LIKE '%Hyper%'")
    gp = cur.fetchone()
    if gp:
        gp_id = gp[0]
        gp_code = gp[1]
        print(f"Found existing Giper pichoq: ID={gp_id}, Code={gp_code}, Title={gp[2]}")
        # update title if needed
        cur.execute("UPDATE doramas SET code=669, title='Giper pichoq (Hyper Knife)', total_episodes=8, status='Tugallangan', category='korea', year=2025 WHERE id=?", (gp_id,))
        gp_code = 669
    else:
        # Create Giper pichoq with code 669
        cur.execute("""
            INSERT INTO doramas (code, title, aliases, year, country, genre, description, total_episodes, status, category, slug)
            VALUES (669, 'Giper pichoq (Hyper Knife)', 'Hyper Knife, Giper pichoq', 2025, 'Janubiy Koreya', 'Tibbiy, Triller, Kriminal', 
                    'Iqtidorli jarroh qiz va uning sobiq ustozi o''rtasidagi shafqatsiz kurash.', 8, 'Tugallangan', 'korea', 'giper-pichoq')
        """)
        gp_id = cur.lastrowid
        gp_code = 669
        print(f"Created new dorama Giper pichoq: ID={gp_id}, Code={gp_code}")

    # 3. Add episodes 1..8
    # Map: ep 1 -> 6064, ep 2 -> 6065, ..., ep 8 -> 6071
    for ep_num in range(1, 9):
        mid = 6063 + ep_num
        fsize = msg_info.get(mid, {}).get('size', 0)
        cur.execute("""
            INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_id, file_size, quality)
            VALUES (?, ?, ?, '', ?, '720p')
            ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
                channel_message_id = excluded.channel_message_id,
                file_size = excluded.file_size,
                quality = '720p',
                file_id = ''
        """, (gp_id, ep_num, mid, fsize))
        print(f"  Giper pichoq Ep {ep_num}: msg={mid}, size={fsize}")

    cur.execute("UPDATE doramas SET total_episodes=8, status='Tugallangan' WHERE id=?", (gp_id,))
    conn.commit()

    # Verify
    cur.execute("SELECT episode_number, channel_message_id FROM episodes WHERE dorama_id=? ORDER BY episode_number", (gp_id,))
    rows = cur.fetchall()
    print(f"Giper pichoq total episodes in DB: {len(rows)} -> {rows}")

    conn.close()

if __name__ == '__main__':
    asyncio.run(main())
