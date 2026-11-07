import asyncio
import unittest
import sqlite3
import os
import sys

# Set up paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import database as db

class TestCatalogIntegrity(unittest.TestCase):

    def test_database_cross_collisions_zero(self):
        """Bazada bitta ham turli doramalar o'rtasidagi cross-dorama to'qnashuv bo'lmasligi shart."""
        con = sqlite3.connect(db.DB_PATH)
        cur = con.cursor()
        cur.execute('''
            SELECT COUNT(*)
            FROM episodes e1
            JOIN episodes e2 ON e1.channel_message_id = e2.channel_message_id AND e1.dorama_id < e2.dorama_id
        ''')
        cross_count = cur.fetchone()[0]
        con.close()
        self.assertEqual(cross_count, 0, f"Kross-dorama to'qnashuvlari 0 bo'lishi kerak, lekin {cross_count} ta topildi!")

    def test_code_242_mapping(self):
        """242-dorama (Yuragimni quvvatla) 10 ta qismi to'liq to'g'ri storage xabarlariga biriktirilganligini tekshirish."""
        con = sqlite3.connect(db.DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT id, title, total_episodes, status FROM doramas WHERE code=242")
        d = cur.fetchone()
        self.assertIsNotNone(d, "Code 242 bazadan topilmadi!")
        d_id, title, total_eps, status = d
        self.assertEqual(total_eps, 10)
        self.assertEqual(status, 'Tugallangan')

        cur.execute("SELECT episode_number, channel_message_id FROM episodes WHERE dorama_id=? ORDER BY episode_number", (d_id,))
        eps = dict(cur.fetchall())
        con.close()

        expected = {
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
        for ep_num, expected_msg in expected.items():
            self.assertEqual(eps.get(ep_num), expected_msg, f"242-dorama {ep_num}-qismi msg {expected_msg} bo'lishi kerak, lekin {eps.get(ep_num)}!")

    def test_code_214_ghost_safe(self):
        """214-dorama (Gyeonwoo va pari) bazada 0 ta qism va 'Tez kunda' holatida bo'lishi shart."""
        con = sqlite3.connect(db.DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT id, total_episodes, status FROM doramas WHERE code=214")
        d = cur.fetchone()
        self.assertIsNotNone(d)
        d_id, total_eps, status = d
        self.assertEqual(total_eps, 0)
        self.assertEqual(status, 'Tez kunda')

        cur.execute("SELECT COUNT(*) FROM episodes WHERE dorama_id=?", (d_id,))
        count = cur.fetchone()[0]
        con.close()
        self.assertEqual(count, 0)

    def test_code_316_to_329_offsets(self):
        """316 dan 329 gacha bo'lgan doramalar +100 siljishsiz to'g'ri xabarlarga ega bo'lishini tekshirish."""
        con = sqlite3.connect(db.DB_PATH)
        cur = con.cursor()
        
        # Tekshiramiz: Code 316 1-qismi 2781 bo'lishi kerak (2881 emas)
        cur.execute("""
            SELECT e.channel_message_id 
            FROM episodes e 
            JOIN doramas d ON e.dorama_id = d.id 
            WHERE d.code=316 AND e.episode_number=1
        """)
        msg_316_1 = cur.fetchone()[0]
        self.assertEqual(msg_316_1, 2781)

        # Code 322 (Falling Into Your Smile) 1-qismi 2879 bo'lishi kerak (2979 emas)
        cur.execute("""
            SELECT e.channel_message_id 
            FROM episodes e 
            JOIN doramas d ON e.dorama_id = d.id 
            WHERE d.code=322 AND e.episode_number=1
        """)
        msg_322_1 = cur.fetchone()[0]
        self.assertEqual(msg_322_1, 2879)

        # Code 329 (Zomvivor) 1-qismi 3065 bo'lishi kerak
        cur.execute("""
            SELECT e.channel_message_id 
            FROM episodes e 
            JOIN doramas d ON e.dorama_id = d.id 
            WHERE d.code=329 AND e.episode_number=1
        """)
        msg_329_1 = cur.fetchone()[0]
        self.assertEqual(msg_329_1, 3065)
        con.close()

    def test_collision_guard_async(self):
        """add_episode orqali boshqa doramaga tegishli xabarni qo'shish bloklanishini tekshirish."""
        async def run_async():
            # Code 242 ning 1-qismi 1858 xabari. Uni boshqa dorama (masalan id=99999)ga qo'shmoqchi bo'lsak, ValueError otishi kerak!
            collision = await db.check_channel_message_collision(1858, 99999)
            self.assertIsNotNone(collision)
            self.assertEqual(collision['code'], 242)

            # O'sha dorama o'ziga biriktirsa (masalan combined episode), ruxsat berilishi kerak
            same_collision = await db.check_channel_message_collision(1858, collision['dorama_id'])
            self.assertIsNone(same_collision)

            # add_episode chaqirilganda ValueError chiqishi shart
            with self.assertRaises(ValueError):
                await db.add_episode(dorama_id=99999, episode_number=99, channel_message_id=1858)

        asyncio.run(run_async())


if __name__ == '__main__':
    unittest.main()
