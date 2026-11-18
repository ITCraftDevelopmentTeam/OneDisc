"""on_ready 重复触发时不得重复初始化（避免反向 WS 重复连接、重复心跳任务）"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

import utils.event.discord_event as discord_event


@pytest.fixture
def patched_on_ready(monkeypatch):
    monkeypatch.setattr(discord_event, "_initialized", False, raising=False)
    monkeypatch.setattr(
        discord_event, "client", SimpleNamespace(user=SimpleNamespace(name="bot"))
    )
    monkeypatch.setattr(discord_event, "tree", SimpleNamespace(sync=AsyncMock()))

    init_connections = AsyncMock()
    monkeypatch.setattr(discord_event, "init_connections", init_connections)
    monkeypatch.setattr(
        discord_event.heartbeat_event, "setup_heartbeat_event", AsyncMock()
    )
    monkeypatch.setattr(
        discord_event, "get_status", AsyncMock(return_value={"data": {}})
    )
    monkeypatch.setattr(discord_event, "init_database", AsyncMock())
    monkeypatch.setattr(discord_event, "start_cleanup_loop", AsyncMock())
    monkeypatch.setattr(discord_event.event, "new_event", Mock())
    return SimpleNamespace(
        init_connections=init_connections,
        init_database=discord_event.init_database,
    )


async def test_on_ready_runs_initialization_only_once(patched_on_ready):
    await discord_event.on_ready()
    # discord.py 在 RESUME 失败后会重新派发 READY，on_ready 会再次触发
    await discord_event.on_ready()
    await discord_event.on_ready()

    patched_on_ready.init_connections.assert_awaited_once()
    patched_on_ready.init_database.assert_awaited_once()
