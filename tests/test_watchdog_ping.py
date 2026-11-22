import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from scripts.bot_failover_watchdog import ping_bot


def test_ping_accepts_exact_pong_and_removes_pair():
    bot = SimpleNamespace(id=123)
    sent = SimpleNamespace(id=10)
    pong = SimpleNamespace(id=11, out=False, sender_id=123, text="PONG_HEALTH_OK")
    client = SimpleNamespace(
        send_message=AsyncMock(return_value=sent),
        get_messages=AsyncMock(return_value=[pong]),
        delete_messages=AsyncMock(),
    )

    with patch("scripts.bot_failover_watchdog.asyncio.sleep", new_callable=AsyncMock):
        assert asyncio.run(ping_bot(client, bot)) is True

    client.get_messages.assert_awaited_with(bot, limit=5, min_id=10)
    client.delete_messages.assert_awaited_once_with(bot, [10, 11], revoke=True)


def test_ping_ignores_unrelated_bot_reply_and_removes_only_probe():
    bot = SimpleNamespace(id=123)
    sent = SimpleNamespace(id=10)
    unrelated = SimpleNamespace(id=11, out=False, sender_id=123, text="Your catalog is ready")
    client = SimpleNamespace(
        send_message=AsyncMock(return_value=sent),
        get_messages=AsyncMock(return_value=[unrelated]),
        delete_messages=AsyncMock(),
    )

    with patch("scripts.bot_failover_watchdog.asyncio.sleep", new_callable=AsyncMock):
        assert asyncio.run(ping_bot(client, bot)) is False

    client.delete_messages.assert_awaited_once_with(bot, [10], revoke=True)


def test_cleanup_failure_does_not_change_health_result():
    bot = SimpleNamespace(id=123)
    sent = SimpleNamespace(id=10)
    pong = SimpleNamespace(id=11, out=False, sender_id=123, text="PONG_HEALTH_OK")
    client = SimpleNamespace(
        send_message=AsyncMock(return_value=sent),
        get_messages=AsyncMock(return_value=[pong]),
        delete_messages=AsyncMock(side_effect=RuntimeError("temporary outage")),
    )

    with patch("scripts.bot_failover_watchdog.asyncio.sleep", new_callable=AsyncMock):
        assert asyncio.run(ping_bot(client, bot)) is True
