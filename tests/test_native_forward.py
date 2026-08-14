"""can_native_forward 判定逻辑单元测试（无需真实 Discord）"""
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock

import discord

from utils import native_forward as nf


def msg(**kw):
    base = dict(
        id=1001,
        type=discord.MessageType.default,
        poll=None,
        reference=None,
        channel=SimpleNamespace(id=2001),
        guild=SimpleNamespace(id=111),
    )
    base.update(kw)
    return SimpleNamespace(**base)


class FakeSession:
    def __init__(self, record):
        self.record = record

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        pass

    async def get(self, model, id_):
        return self.record


def patch_env(cached=None, db_record=None, target_guild=SimpleNamespace(id=111), api_get=None):
    from contextlib import ExitStack

    sess = FakeSession(db_record)
    stack = ExitStack()
    stack.enter_context(patch.object(nf, "client", SimpleNamespace(
        cached_messages=cached or [],
        get_channel=lambda cid: SimpleNamespace(guild=target_guild),
    )))
    stack.enter_context(patch.object(nf, "get_session", lambda: sess))
    stack.enter_context(patch.object(nf.discord_api, "call", AsyncMock(return_value=api_get)))
    return stack


async def test_内联内容节点整体回退():
    with patch_env():
        r = await nf.can_native_forward(
            [{"type": "node", "data": {"user_id": 1, "nickname": "x", "content": "hi"}}], 3001)
        assert r is None


async def test_引用节点cache与db均无记录回退():
    with patch_env(cached=[], db_record=None):
        r = await nf.can_native_forward([{"type": "node", "data": {"message_id": 999}}], 3001)
        assert r is None


async def test_cache命中但类型不可转发回退():
    with patch_env(cached=[msg(id=1001, type=discord.MessageType.pins_add)]):
        r = await nf.can_native_forward([{"type": "node", "data": {"message_id": 1001}}], 3001)
        assert r is None


async def test_cache命中类型可转发返回refs():
    with patch_env(cached=[msg(id=1001)]):
        r = await nf.can_native_forward([{"type": "node", "data": {"message_id": 1001}}], 3001)
        assert r == [{"message_id": 1001, "channel_id": 2001}]


async def test_转发消息本身不能再转发():
    with patch_env(cached=[msg(id=1001, reference=SimpleNamespace(type=discord.MessageReferenceType.forward))]):
        r = await nf.can_native_forward([{"type": "node", "data": {"message_id": 1001}}], 3001)
        assert r is None


async def test_数量超阈值回退():
    with patch.object(nf, "config", {**nf.config, "system": {**nf.config["system"], "native_forward_max_nodes": 1}}):
        with patch_env(cached=[msg(id=1001), msg(id=1002)]):
            r = await nf.can_native_forward(
                [{"type": "node", "data": {"message_id": 1001}},
                 {"type": "node", "data": {"message_id": 1002}}], 3001)
            assert r is None
            # 阈值 1 但只有 1 条 → 放行
            r = await nf.can_native_forward([{"type": "node", "data": {"message_id": 1001}}], 3001)
            assert r == [{"message_id": 1001, "channel_id": 2001}]


async def test_跨服务器回退():
    with patch_env(cached=[msg(id=1001, guild=SimpleNamespace(id=999))], target_guild=SimpleNamespace(id=111)):
        r = await nf.can_native_forward([{"type": "node", "data": {"message_id": 1001}}], 3001)
        assert r is None


async def test_db命中且rest预检通过返回refs():
    with patch_env(db_record=SimpleNamespace(channel=2001), api_get={"type": 0, "guild_id": 111}):
        r = await nf.can_native_forward([{"type": "node", "data": {"message_id": 1001}}], 3001)
        assert r == [{"message_id": 1001, "channel_id": 2001}]


async def test_db命中但预检类型不可转发回退():
    with patch_env(db_record=SimpleNamespace(channel=2001), api_get={"type": 6, "guild_id": 111}):
        r = await nf.can_native_forward([{"type": "node", "data": {"message_id": 1001}}], 3001)
        assert r is None


async def test_db命中但预检消息不存在回退():
    with patch_env(db_record=SimpleNamespace(channel=2001), api_get={"code": 10008, "message": "Unknown Message"}):
        r = await nf.can_native_forward([{"type": "node", "data": {"message_id": 1001}}], 3001)
        assert r is None


async def test_混合节点整体回退():
    with patch_env(cached=[msg(id=1001)]):
        r = await nf.can_native_forward(
            [{"type": "node", "data": {"message_id": 1001}},
             {"type": "node", "data": {"user_id": 1, "nickname": "x", "content": "hi"}}], 3001)
        assert r is None


async def test_非node结构回退():
    with patch_env():
        r = await nf.can_native_forward([{"type": "text", "data": {"text": "hi"}}], 3001)
        assert r is None
