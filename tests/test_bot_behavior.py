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

    async def test_existing_suggestion_gets_immediate_reply(self):
        message = SimpleNamespace(text="Mening idolim mening boshlig‘im", caption=None,
                                  from_user=SimpleNamespace(id=42, username=None, first_name="Test"),
                                  answer=AsyncMock())
        state = SimpleNamespace(clear=AsyncMock())
        drama = {"id": 301, "code": 301, "title": "Mening idolim mening boshlig'im (My Bias, My Boss)"}
        with patch.object(bot.db, "add_dorama_suggestion", AsyncMock(return_value=21)), \
             patch.object(bot.db, "search_doramas", AsyncMock(return_value=[drama])), \
             patch.object(bot, "send_dorama_exists_notification", AsyncMock()) as notify:
            await bot.process_dorama_suggestion(message, state, SimpleNamespace())
            notify.assert_awaited_once_with(unittest.mock.ANY, 42, 21, drama)
            message.answer.assert_not_awaited()
