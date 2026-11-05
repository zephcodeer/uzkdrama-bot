import asyncio
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import aiosqlite
import database


class VipOrderTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_paths = database.DB_PATH, database.USER_DB_PATH
        database.DB_PATH = Path(self.tmp.name) / 'catalog.db'
        database.USER_DB_PATH = Path(self.tmp.name) / 'users.db'
        await database.init_db()
        self.plans = {'1m': {'days': 30}, 'life': {'days': 3650}}

    async def asyncTearDown(self):
        database.DB_PATH, database.USER_DB_PATH = self.old_paths
        self.tmp.cleanup()

    async def test_renewal_adds_remaining_days_and_lifetime_stays_lifetime(self):
        await database.grant_vip(10, 20)
        await database.grant_vip(10, 30)
        user = await database.get_user(10)
        self.assertGreater(datetime.fromisoformat(user['vip_until']), datetime.now() + timedelta(days=49))
        await database.grant_vip(10, 3650)
        await database.grant_vip(10, 30)
        self.assertIsNone((await database.get_user(10))['vip_until'])

    async def test_order_is_atomic_and_cannot_be_approved_twice(self):
        order = await database.create_vip_order(12, '1m', 9000)
        results = await asyncio.gather(database.resolve_vip_order(order, True, self.plans), database.resolve_vip_order(order, True, self.plans))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual((await database.get_vip_order(order))['status'], 'approved')
        user = await database.get_user(12)
        self.assertLess(datetime.fromisoformat(user['vip_until']), datetime.now() + timedelta(days=31))

    async def test_rejected_order_cannot_be_approved(self):
        order = await database.create_vip_order(13, '1m', 9000)
        self.assertIsNotNone(await database.resolve_vip_order(order, False, self.plans))
        self.assertIsNone(await database.resolve_vip_order(order, True, self.plans))
        self.assertIsNone(await database.get_user(13))

    async def test_receipt_plan_survives_new_connection(self):
        await database.set_pending_receipt(14, '1m')
        self.assertEqual(await database.get_pending_receipt(14), '1m')
        await database.set_pending_receipt(14, None)
        self.assertIsNone(await database.get_pending_receipt(14))


if __name__ == '__main__':
    unittest.main()
