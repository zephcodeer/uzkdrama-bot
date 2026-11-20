import json
import sqlite3
from pathlib import Path

DB_PATH = Path(r"E:\Agent\Drama Bot\doramas.db")
MAP_PATH = Path(r"E:\Agent\Drama Bot\scripts\alien2_storage_map.json")

def apply_updates():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    print("Applying Refiner Database Updates...")
    
    # 1. Doktor X , Oq Mafia (Code 101)
    c.execute("""
        UPDATE doramas
        SET total_episodes = 12,
            status = 'Tugallangan',
            country = 'Janubiy Koreya',
            category = 'korea',
            actors = 'Kim Ji-won, Lee Jung-eun, Son Hyun-joo, Kim Woo-seok',
            aliases = 'Doktor X, Doctor X, Oq Mafia, Doktor X Oq Mafia, Doctor X White Mafia, Doctor X: Mafia in White, 닥터X : 하얀 마피아의 시대'
        WHERE code = 101
    """)
    print("1. Updated Code 101 (Doktor X , Oq Mafia): status='Tugallangan', total_episodes=12, country='Janubiy Koreya'")

    # 2. Bechoralar (Code 481, ID 381)
    c.execute("SELECT id FROM doramas WHERE code = 481")
    row = c.fetchone()
    if row:
        d_id = row[0]
        bechoralar_eps = [
            (57, 5870, '720p', 312685363),
            (58, 5871, '720p', 430859878),
            (59, 5872, '720p', 400660889),
            (60, 5873, '720p', 317928243),
        ]
        for ep_num, msg_id, qual, sz in bechoralar_eps:
            c.execute("""
                INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality, file_size)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
                    channel_message_id = excluded.channel_message_id,
                    quality = excluded.quality,
                    file_size = excluded.file_size
            """, (d_id, ep_num, msg_id, qual, sz))
        c.execute("""
            UPDATE doramas
            SET total_episodes = 60,
                status = 'Ongoing'
            WHERE id = ?
        """, (d_id,))
        print(f"2. Updated Code 481 (Bechoralar): Ingested eps 57..60, total_episodes=60, status='Ongoing'")

    # 3. Mening sevgilim o'zga sayyoralik 2 (Code 538, ID 438)
    c.execute("SELECT id FROM doramas WHERE code = 538")
    row = c.fetchone()
    if row:
        d_id = row[0]
        # Ingest 30 episodes
        if MAP_PATH.exists():
            with open(MAP_PATH, "r", encoding="utf-8") as f:
                alien_data = json.load(f)
            for item in alien_data:
                ep_num = item["episode_number"]
                msg_id = item["storage_msg_id"]
                sz = item.get("size", 0)
                c.execute("""
                    INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality, file_size)
                    VALUES (?, ?, ?, '1080p', ?)
                    ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
                        channel_message_id = excluded.channel_message_id,
                        quality = excluded.quality,
                        file_size = excluded.file_size
                """, (d_id, ep_num, msg_id, sz))
            print(f"3a. Ingested {len(alien_data)} episodes for Code 538 into episodes table.")
        
        c.execute("""
            UPDATE doramas
            SET title = 'Mening sevgilim o''zga sayyoralik 2',
                year = 2022,
                genre = 'Romantika, Komediya, Fantastika, Yoshlar',
                country = 'Xitoy',
                category = 'china',
                total_episodes = 30,
                status = 'Tugallangan',
                actors = 'Wan Peng, Bie Thassapak Hsu, Wang You Jun, Chen Yi Xin',
                description = 'Chai Xiao Qi va Fang Leng o''z sevgilari yo''lidagi to''siqlarni yengib, to''y arafasida turganlarida, Kapeya sayyorasidan Xiao Qi ning xotirasini o''chirish uchun kelgan dushman uning sevgisini yo''qotmoqchi bo''ladi. Fang Leng sevgilisining xotiralarini qaytarish uchun kurashadi.',
                poster_url = 'posters/code_538.jpg',
                aliases = 'My Girlfriend is an Alien 2, Mening sevgilim o''zga sayyoralik 2, 外星女生柴小七2, O''zga sayyoralik sevgilim 2'
            WHERE id = ?
        """, (d_id,))
        print("3b. Updated Code 538 (Mening sevgilim o'zga sayyoralik 2) metadata and status='Tugallangan'")

    # 4. Gullash ortidagi halokat (Code 537, ID 437)
    c.execute("SELECT id FROM doramas WHERE code = 537")
    row = c.fetchone()
    if row:
        d_id = row[0]
        gullash_eps = [
            (1, 5874, '1080p', 300312166),
            (2, 5875, '1080p', 396152012),
            (3, 5876, '1080p', 323065610),
            (4, 5877, '1080p', 292657561),
            (5, 5878, '1080p', 343407001),
            (6, 5879, '1080p', 348227993),
        ]
        for ep_num, msg_id, qual, sz in gullash_eps:
            c.execute("""
                INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality, file_size)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
                    channel_message_id = excluded.channel_message_id,
                    quality = excluded.quality,
                    file_size = excluded.file_size
            """, (d_id, ep_num, msg_id, qual, sz))
        print(f"4a. Ingested {len(gullash_eps)} episodes for Code 537.")
        
        c.execute("""
            UPDATE doramas
            SET title = 'Gullash ortidagi halokat',
                slug = 'gullash-ortidagi-halokat',
                year = 2024,
                genre = 'Tarixiy, Romantika, Biznes, Drama, Melodrama',
                country = 'Xitoy',
                category = 'china',
                total_episodes = 40,
                status = 'Ongoing',
                actors = 'Zhang Jingyi, Hu Yitian, Wu Xize, Lu Yuxiao',
                description = 'Hua xonadoni kutilmagan fitna qurboni bo''lib, mol-mulki musodara qilinib erkaklari surgun etilgach, nochor qolgan xonadonni qutqarish uchun jasur qiz Hua Zhi tadbirkorlik qilib oilani oyoqqa turg''azadi. U sirli sarkarda Gu Yanxi bilan fitnalarga qarshi kurashadi.',
                poster_url = 'posters/code_537.jpg',
                aliases = 'Gullash Ortidagi Halokat Yohud Gullash Kuchi, Blossoms in Adversity, Xi Hua Zhi, 惜花芷, Gullash ortidagi halokat'
            WHERE id = ?
        """, (d_id,))
        print("4b. Updated Code 537 (Gullash ortidagi halokat) metadata, total_episodes=40, status='Ongoing'")

    # 5. Buyuk fitnachi (Code 517)
    c.execute("""
        UPDATE doramas
        SET total_episodes = 16,
            status = 'Ongoing',
            aliases = 'Buyuk fitnachi, The Great Seducer, Tempted, 위대한 유혹자, Buyuk fitnachi uzbek tilida'
        WHERE code = 517
    """)
    print("5. Updated Code 517 (Buyuk fitnachi): total_episodes=16, status='Ongoing'")

    # 6. Taqdir tig'lari (Code 508)
    c.execute("""
        UPDATE doramas
        SET total_episodes = 34,
            status = 'Ongoing',
            country = 'Xitoy',
            category = 'china',
            genre = 'Fentezi, Tarixiy, Mistika, Sarguzasht, Romantika',
            aliases = 'Taqdir tig''lari, Taqdir tiglari, Fangs of Fortune, Da Meng Gui Li, 大梦归离, Taqdir tig''lari uzbek tilida'
        WHERE code = 508
    """)
    print("6. Updated Code 508 (Taqdir tig'lari): total_episodes=34, status='Ongoing', country='Xitoy', category='china'")

    conn.commit()
    conn.close()
    print("All Refiner DB updates committed successfully!")

if __name__ == "__main__":
    apply_updates()
