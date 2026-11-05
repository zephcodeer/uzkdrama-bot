import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import bot


class BotBehaviorTests(unittest.IsolatedAsyncioTestCase):
    async def test_membership_failure_does_not_grant_access(self):
        client = SimpleNamespace(get_chat_member=AsyncMock(side_effect=RuntimeError('unavailable')))
        with patch.object(bot.db, 'is_vip', AsyncMock(return_value=False)):
            self.assertFalse(await bot.is_user_channel_member(client, 999999999))

    async def test_restricted_nonmember_is_not_admitted(self):
        client = SimpleNamespace(get_chat_member=AsyncMock(return_value=SimpleNamespace(status='restricted', is_member=False)))
        with patch.object(bot.db, 'is_vip', AsyncMock(return_value=False)):
            self.assertFalse(await bot.is_user_channel_member(client, 999999999))

    async def test_failed_video_is_not_counted_as_watched(self):
        client = SimpleNamespace(copy_message=AsyncMock(side_effect=RuntimeError('delivery failed')), send_message=AsyncMock(), get_me=AsyncMock(return_value=SimpleNamespace(username='test')))
        episode = {'episode_number': 1, 'channel_message_id': 1, 'quality': '720p'}
        with patch.object(bot, 'is_user_channel_member', AsyncMock(return_value=True)), \
             patch.object(bot.db, 'get_episode', AsyncMock(return_value=episode)), \
             patch.object(bot.db, 'is_user_unlocked', AsyncMock(return_value=(True, 'free', 0, 0))), \
             patch.object(bot.db, 'get_dorama_by_id', AsyncMock(return_value={'title': 'Test'})), \
             patch.object(bot.db, 'get_episodes', AsyncMock(return_value=[episode])), \
             patch.object(bot.db, 'is_bookmarked', AsyncMock(return_value=False)), \
             patch.object(bot.db, 'increment_views', AsyncMock()) as views, \
             patch.object(bot.db, 'save_last_watched', AsyncMock()) as history:
            await bot.send_episode(12, 1, 1, client)
            views.assert_not_awaited()
            history.assert_not_awaited()
