import sqlite3
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'doramas.db'
BACKUP_DIR = 'backups'
os.makedirs(BACKUP_DIR, exist_ok=True)

def run_fix():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    con.execute("PRAGMA foreign_keys = ON;")
    
    print("=== STARTING FORENSIC DATABASE CORRECTION ===")
    
    # 1. Fetch pre-state for changelog
    target_codes = [214, 242, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329]
    pre_state = {}
    for code in target_codes:
        cur.execute("SELECT id, title, total_episodes, status FROM doramas WHERE code=?", (code,))
        d = cur.fetchone()
        if d:
            cur.execute("SELECT episode_number, channel_message_id FROM episodes WHERE dorama_id=? ORDER BY episode_number", (d[0],))
            eps = cur.fetchall()
            pre_state[code] = {
                'id': d[0],
                'title': d[1],
                'total_episodes': d[2],
                'status': d[3],
                'episodes': eps
            }
            
    with open(os.path.join(BACKUP_DIR, 'pre_fix_forensic_state.json'), 'w', encoding='utf-8') as f:
        json.dump(pre_state, f, ensure_ascii=False, indent=2)
    print("Saved pre-fix state to backups/pre_fix_forensic_state.json")
    
    # 2. Begin transaction
    con.execute("BEGIN TRANSACTION;")
    try:
        # A. Fix Code 242: Yuragimni quvvatla (dorama_id=142)
        cur.execute("SELECT id FROM doramas WHERE code=242")
        d242_id = cur.fetchone()[0]
        code_242_mapping = {
            1: 1858,
            2: 1859,
            3: 1860,
            4: 1861,
            5: 1862,
            6: 1863,
            7: 1864,
            8: 3205,
            9: 5051,
            10: 5263
        }
        for ep_num, msg_id in code_242_mapping.items():
            cur.execute("""
                INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
                VALUES (?, ?, ?, '720p')
                ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
                channel_message_id = excluded.channel_message_id,
                quality = '720p'
            """, (d242_id, ep_num, msg_id))
        cur.execute("UPDATE doramas SET total_episodes=10, status='Tugallangan' WHERE id=?", (d242_id,))
        print(f"Fixed Code 242 (id={d242_id}): 10 episodes mapped (1858-1864, 3205, 5051, 5263).")

        # B. Fix Codes 316-328 (+100 offset shift back)
        offset_configs = [
            (316, 12, 2780),  # 2781..2792
            (317, 16, 2804),  # 2805..2820
            (318, 36, 2820),  # 2821..2856
            (319, 8,  2856),  # 2857..2864
            (320, 8,  2864),  # 2865..2872
            (321, 6,  2872),  # 2873..2878
            (322, 32, 2878),  # 2879..2910
            (323, 31, 2910),  # 2911..2941
            (324, 25, 2941),  # 2942..2966
            (325, 10, 2966),  # 2967..2976
            (326, 16, 2976),  # 2977..2992
            (327, 32, 2992),  # 2993..3024
            (328, 36, 3024),  # 3025..3060
        ]
        
        for code, count, base_msg in offset_configs:
            cur.execute("SELECT id FROM doramas WHERE code=?", (code,))
            row = cur.fetchone()
            if not row:
                print(f"Warning: Code {code} not found!")
                continue
            did = row[0]
            for ep_num in range(1, count + 1):
                real_msg = base_msg + ep_num
                cur.execute("""
                    INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
                    VALUES (?, ?, ?, '720p')
                    ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
                    channel_message_id = excluded.channel_message_id
                """, (did, ep_num, real_msg))
            cur.execute("UPDATE doramas SET total_episodes=?, status='Tugallangan' WHERE id=?", (count, did))
            print(f"Fixed Code {code} (id={did}): {count} episodes mapped to {base_msg+1}..{base_msg+count}.")

        # C. Fix Code 329 (Zomvivor - discrete message IDs)
        cur.execute("SELECT id FROM doramas WHERE code=329")
        d329_id = cur.fetchone()[0]
        code_329_mapping = {
            1: 3065,
            2: 3066,
            3: 3067,
            4: 3069, # 720p
            5: 3070, # 720p
            6: 3072, # 720p
            7: 3073  # 720p final
        }
        for ep_num, msg_id in code_329_mapping.items():
            cur.execute("""
                INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
                VALUES (?, ?, ?, '720p')
                ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
                channel_message_id = excluded.channel_message_id
            """, (d329_id, ep_num, msg_id))
        cur.execute("UPDATE doramas SET total_episodes=7, status='Tugallangan' WHERE id=?", (d329_id,))
        print(f"Fixed Code 329 (id={d329_id}): 7 episodes mapped to {list(code_329_mapping.values())}.")

        # D. Fix Code 214: Gyeonwoo va pari (ghost entry - not in storage channel)
        cur.execute("SELECT id FROM doramas WHERE code=214")
        row_214 = cur.fetchone()
        if row_214:
            d214_id = row_214[0]
            cur.execute("DELETE FROM episodes WHERE dorama_id=?", (d214_id,))
            cur.execute("UPDATE doramas SET total_episodes=0, status='Tez kunda' WHERE id=?", (d214_id,))
            print(f"Fixed Code 214 (id={d214_id}): deleted fake episodes, status set to 'Tez kunda' (0 eps).")

        # Check cross collisions
        cur.execute('''
            SELECT COUNT(*)
            FROM episodes e1
            JOIN episodes e2 ON e1.channel_message_id = e2.channel_message_id AND e1.dorama_id < e2.dorama_id
        ''')
        remaining_cross = cur.fetchone()[0]
        print(f"\nVerification: Remaining cross-dorama collisions in DB = {remaining_cross}")
        if remaining_cross != 0:
            raise RuntimeError(f"Still {remaining_cross} cross collisions remaining! Aborting commit.")

        con.commit()
        print("TRANSACTION COMMITTED SUCCESSFULLY!")

    except Exception as e:
        con.rollback()
        print(f"ERROR: Transaction rolled back: {e}")
        raise e
    finally:
        con.close()

if __name__ == '__main__':
    run_fix()
