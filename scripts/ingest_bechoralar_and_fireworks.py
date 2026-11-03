import sqlite3
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
DB_PATH = r"E:\Agent\Drama Bot\doramas.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# -------------------------------------------------------------
# 1. Update Bechoralar (ID: 381, Code: 481)
# -------------------------------------------------------------
print("--- Updating Bechoralar (Code 481) ---")
bechoralar_eps = [
    (381, 43, 5106, '720p'),
    (381, 44, 5107, '720p'),
    (381, 45, 5108, '720p'),
    (381, 46, 5169, '720p')
]

for dorama_id, ep_num, msg_id, quality in bechoralar_eps:
    c.execute("""
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
            channel_message_id = excluded.channel_message_id,
            quality = excluded.quality
    """, (dorama_id, ep_num, msg_id, quality))
    print(f"Upserted Bechoralar Ep {ep_num} -> Msg {msg_id}")

c.execute("UPDATE doramas SET total_episodes = 46, status = 'Ongoing' WHERE id = 381")
print("Bechoralar updated to 46 episodes.")

# -------------------------------------------------------------
# 2. Ingest Yuragim otashinlari (ID: 385, Code: 485)
# -------------------------------------------------------------
print("\n--- Ingesting Yuragim otashinlari (Code 485) ---")
c.execute("SELECT id, code, title FROM doramas WHERE code = 485 OR slug = 'yuragim-otashinlari-fireworks-of-my-heart'")
row = c.fetchone()
if row:
    print(f"Already exists: {row}")
else:
    c.execute("""
        INSERT INTO doramas (
            id, code, title, slug, genre, year, description, poster_url, 
            total_episodes, status, country, actors, aliases, category
        ) VALUES (
            385, 485,
            'Yuragim otashinlari (Fireworks of My Heart)',
            'yuragim-otashinlari-fireworks-of-my-heart',
            'Romantika, Tibbiyot, Drama, Qutqaruv xizmati',
            2023,
            'Yong''in xavfsizligi boshlig''i Song Yan va tez tibbiy yordam shifokori Xu Qin bolalikdagi sevgililar bo''lib, oilaviy qarshiliklar sabab 10 yil oldin ayrilgan edi. Yillar o''tib, hayot va o''lim chegarasidagi qutqaruv xizmatida qayta uchrashib, bir-birlarining dillarini davolaydilar va muhabbatlarini qayta tiklaydilar.',
            'posters/yuragim-otashinlari-fireworks-of-my-heart.jpg',
            40,
            'Completed',
            'Xitoy',
            'Yang Yang, Wang Churan, Wei Daxun, Wang Yanlin, Zhang Binbin',
            'Yuragim otashinlari, Otashin qalblar, Moy signalniy ogon, Мой сигнальный огонь, Fireworks of My Heart, Wo De Ren Jian Yan Huo, 我的人间烟火, Fireworks, Otashin',
            'china'
        )
    """)
    print("Inserted Dorama ID 385 (Code 485)")

# Episodes 1 to 40
# 1-27: 5127 to 5153
# 28-40: 5154 to 5166
fireworks_eps = []
for i in range(1, 41):
    msg_id = 5127 + (i - 1)
    quality = '1080p'
    fireworks_eps.append((385, i, msg_id, quality))

for dorama_id, ep_num, msg_id, quality in fireworks_eps:
    c.execute("""
        INSERT INTO episodes (dorama_id, episode_number, channel_message_id, quality)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(dorama_id, episode_number) DO UPDATE SET
            channel_message_id = excluded.channel_message_id,
            quality = excluded.quality
    """, (dorama_id, ep_num, msg_id, quality))

print(f"Upserted all {len(fireworks_eps)} episodes (1 to 40) for Fireworks of My Heart.")

conn.commit()

# Verification
print("\n--- Verification ---")
c.execute("SELECT id, code, title, total_episodes, status FROM doramas WHERE code IN (481, 485)")
for d in c.fetchall():
    print(d)

c.execute("SELECT COUNT(*) FROM episodes WHERE dorama_id = 381")
print(f"Bechoralar episodes count in DB: {c.fetchone()[0]}")

c.execute("SELECT COUNT(*) FROM episodes WHERE dorama_id = 385")
print(f"Fireworks of My Heart episodes count in DB: {c.fetchone()[0]}")

conn.close()
