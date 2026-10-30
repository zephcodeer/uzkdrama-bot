import sqlite3
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = r"E:\Agent\Drama Bot"
DB_PATH = os.path.join(BASE_DIR, "doramas.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Dorama 121 ni olish
    c.execute("SELECT id, code, title FROM doramas WHERE code = 121")
    row = c.fetchone()
    if not row:
        print("XATO: Code 121 topilmadi!")
        return
        
    dorama_id = row[0]
    print(f"Topildi: id={dorama_id}, code=121, title='{row[2]}'")
    
    # 20 ta qism xabarlari: 3371 dan 3390 gacha
    episodes_map = []
    for ep in range(1, 21):
        msg_id = 3370 + ep
        episodes_map.append((ep, msg_id))
        
    # Eski qismlarni tozalash (agar bo'lsa)
    c.execute("DELETE FROM episodes WHERE dorama_id = ?", (dorama_id,))
    
    for ep_num, msg_id in episodes_map:
        c.execute("""
            INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality, file_id)
            VALUES (?, ?, ?, ?, ?)
        """, (dorama_id, ep_num, msg_id, "1080p", None))
        
    # Jami qismlar sonini 20 ga yangilash
    c.execute("UPDATE doramas SET total_episodes = 20, status = 'Tugallangan' WHERE id = ?", (dorama_id,))
    
    conn.commit()
    
    c.execute("SELECT COUNT(*) FROM episodes WHERE dorama_id = ?", (dorama_id,))
    cnt = c.fetchone()[0]
    print(f"Muvaffaqiyatli saqlandi! Dorama 121 uchun {cnt} ta qism kiritildi.")
    
    c.execute("SELECT COUNT(*) FROM doramas")
    tot_d = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM episodes")
    tot_e = c.fetchone()[0]
    print(f"Bazada jami: {tot_d} ta dorama, {tot_e} ta qism mavjud.")
    conn.close()

if __name__ == "__main__":
    main()
