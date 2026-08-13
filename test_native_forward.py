"""can_native_forward 判定逻辑单元测试（无需真实 Discord）"""
import asyncio
import sys
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock

import discord

sys.path.insert(0, "/vol2/@apphome/trim.openclaw/data/workspace/onedisc-dev")

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


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


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


results = []


def check(name, cond):
    results.append((name, cond))
    print(f"{'✅' if cond else '❌'} {name}")


# --- 1. 内联内容节点 → 整体回退 ---
with patch_env():
    r = run(nf.can_native_forward(
        [{"type": "node", "data": {"user_id": 1, "nickname": "x", "content": "hi"}}], 3001))
    check("内联节点 → None", r is None)

# --- 2. 引用节点 cache/DB 均无记录 → 回退 ---
with patch_env(cached=[], db_record=None):
    r = run(nf.can_native_forward([{"type": "node", "data": {"message_id": 999}}], 3001))
    check("channel 无法解析 → None", r is None)

# --- 3. cache 命中但类型不可转发（pins_add）→ 回退 ---
with patch_env(cached=[msg(id=1001, type=discord.MessageType.pins_add)]):
    r = run(nf.can_native_forward([{"type": "node", "data": {"message_id": 1001}}], 3001))
    check("不可转发类型 → None", r is None)

# --- 4. cache 命中、类型可转发 → 返回 refs ---
with patch_env(cached=[msg(id=1001)]):
    r = run(nf.can_native_forward([{"type": "node", "data": {"message_id": 1001}}], 3001))
    check("正常引用 → refs", r == [{"message_id": 1001, "channel_id": 2001}])

# --- 5. 转发消息本身（reference.type==forward）→ 回退 ---
with patch_env(cached=[msg(id=1001, reference=SimpleNamespace(type=discord.MessageReferenceType.forward))]):
    r = run(nf.can_native_forward([{"type": "node", "data": {"message_id": 1001}}], 3001))
    check("转发消息不能再转发 → None", r is None)

# --- 6. 数量超阈值 → 回退 ---
with patch.object(nf, "config", {**nf.config, "system": {**nf.config["system"], "native_forward_max_nodes": 1}}):
    with patch_env(cached=[msg(id=1001), msg(id=1002)]):
        r = run(nf.can_native_forward(
            [{"type": "node", "data": {"message_id": 1001}},
             {"type": "node", "data": {"message_id": 1002}}], 3001))
        check("超阈值 → None", r is None)
        # 阈值 1 但只有 1 条 → 放行
        r = run(nf.can_native_forward([{"type": "node", "data": {"message_id": 1001}}], 3001))
        check("未超阈值 → refs", r == [{"message_id": 1001, "channel_id": 2001}])

# --- 7. 跨服务器（cache 命中 guild 不同）→ 回退 ---
with patch_env(cached=[msg(id=1001, guild=SimpleNamespace(id=999))], target_guild=SimpleNamespace(id=111)):
    r = run(nf.can_native_forward([{"type": "node", "data": {"message_id": 1001}}], 3001))
    check("跨服务器 → None", r is None)

# --- 8. DB 命中 + REST 预检通过 → refs ---
with patch_env(db_record=SimpleNamespace(channel=2001), api_get={"type": 0, "guild_id": 111}):
    r = run(nf.can_native_forward([{"type": "node", "data": {"message_id": 1001}}], 3001))
    check("DB+预检通过 → refs", r == [{"message_id": 1001, "channel_id": 2001}])

# --- 9. DB 命中 + 预检失败（不可转发类型 6=pins_add）→ 回退 ---
with patch_env(db_record=SimpleNamespace(channel=2001), api_get={"type": 6, "guild_id": 111}):
    r = run(nf.can_native_forward([{"type": "node", "data": {"message_id": 1001}}], 3001))
    check("DB+预检类型不可转发 → None", r is None)

# --- 10. DB 命中 + 预检错误响应（消息不存在）→ 回退 ---
with patch_env(db_record=SimpleNamespace(channel=2001), api_get={"code": 10008, "message": "Unknown Message"}):
    r = run(nf.can_native_forward([{"type": "node", "data": {"message_id": 1001}}], 3001))
    check("DB+预检消息不存在 → None", r is None)

# --- 11. 混合：一条正常 + 一条内联 → 整体回退 ---
with patch_env(cached=[msg(id=1001)]):
    r = run(nf.can_native_forward(
        [{"type": "node", "data": {"message_id": 1001}},
         {"type": "node", "data": {"user_id": 1, "nickname": "x", "content": "hi"}}], 3001))
    check("混合节点 → None", r is None)

# --- 12. 非 node 结构 → 回退 ---
with patch_env():
    r = run(nf.can_native_forward([{"type": "text", "data": {"text": "hi"}}], 3001))
    check("非 node 结构 → None", r is None)

failed = [n for n, c in results if not c]
print(f"\n共 {len(results)} 例，失败 {len(failed)} 例")
sys.exit(1 if failed else 0)
