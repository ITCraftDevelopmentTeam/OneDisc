"""缓存目录 / DB 默认路径 / reply 三层解析 / 过期清理 单元测试（无需真实 Discord）"""
import asyncio
import json
import os
import shutil
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock

sys.path.insert(0, "/vol2/@apphome/trim.openclaw/data/workspace/onedisc-dev")

import discord

from utils import cache
from utils import db
from utils.message.v12 import parser


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


results = []


def check(name, cond):
    results.append((name, bool(cond)))
    print(f"{'✅' if cond else '❌'} {name}")


class FakeSession:
    def __init__(self, record):
        self.record = record

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        pass

    async def get(self, model, id_):
        return self.record


def make_msg(mid, cid):
    return SimpleNamespace(id=mid, channel=SimpleNamespace(id=cid))


# ---------- reply 三层解析 ----------

# 1. 第一层：cached_messages 命中 → 返回原消息对象
with patch.object(parser, "client", SimpleNamespace(cached_messages=[make_msg(1001, 2001)])), patch.object(
    parser, "get_session", lambda: FakeSession(None)
), patch.object(parser.discord_api, "call", AsyncMock()):
    r = run(parser._resolve_reply(1001, 3001))
    check("reply: cached 命中返回原消息对象", getattr(r, "id", None) == 1001)

# 2. 第二层：cached 空 + DB 命中 → MessageReference(channel=record.channel)
with patch.object(parser, "client", SimpleNamespace(cached_messages=[])), patch.object(
    parser, "get_session", lambda: FakeSession(SimpleNamespace(channel=2001))
), patch.object(parser.discord_api, "call", AsyncMock()):
    r = run(parser._resolve_reply(1001, None))
    check(
        "reply: DB 命中返回 MessageReference(channel=2001)",
        isinstance(r, discord.MessageReference) and r.channel_id == 2001,
    )

# 3. 第三层：cached/DB 空 + REST 预检成功 → MessageReference(channel=传入)
with patch.object(parser, "client", SimpleNamespace(cached_messages=[])), patch.object(
    parser, "get_session", lambda: FakeSession(None)
), patch.object(parser.discord_api, "call", AsyncMock(return_value={})):
    r = run(parser._resolve_reply(1001, 3001))
    check(
        "reply: REST 预检成功返回 MessageReference(channel=3001)",
        isinstance(r, discord.MessageReference) and r.channel_id == 3001,
    )

# 4. 全 miss（REST 抛异常）→ None
async def boom(*a, **k):
    raise RuntimeError("404")


with patch.object(parser, "client", SimpleNamespace(cached_messages=[])), patch.object(
    parser, "get_session", lambda: FakeSession(None)
), patch.object(parser.discord_api, "call", boom):
    r = run(parser._resolve_reply(1001, 3001))
    check("reply: 全 miss 返回 None", r is None)

# 5. parse_message 集成：reply 段 + DB 命中 → message_data["reference"]
with patch.object(parser, "client", SimpleNamespace(cached_messages=[])), patch.object(
    parser, "get_session", lambda: FakeSession(SimpleNamespace(channel=2001))
), patch.object(parser.discord_api, "call", AsyncMock()):
    data = run(parser.parse_message([{"type": "reply", "data": {"message_id": "1001"}}]))
    check(
        "parse_message: reply 段生成 reference(channel=2001)",
        data.get("reference") is not None and data["reference"].channel_id == 2001,
    )

# ---------- DB 默认路径 ----------

# 6. database 未配置 → 拼接缓存目录 + onedisc.db
with patch.dict(db.config, {"system": {"cache_dir": "/tmp/onedisc_test_cache", "database": None}}):
    url = db._resolve_db_url()
    check(
        "db_url: 默认拼接缓存目录/onedisc.db",
        url.endswith("onedisc.db") and "onedisc_test_cache" in url,
    )

# 7. database 显式配置 → 原样使用
with patch.dict(db.config, {"system": {"cache_dir": ".cache", "database": "sqlite+aiosqlite:///:memory:"}}):
    check(
        "db_url: 显式配置原样使用",
        db._resolve_db_url() == "sqlite+aiosqlite:///:memory:",
    )

# ---------- 过期清理 ----------

# 8. files_ttl=1：过期文件删除，新文件保留（files/ 目录 + node.* 节点文件）
tmp = tempfile.mkdtemp()
try:
    files = os.path.join(tmp, "files")
    os.makedirs(files)
    old = os.path.join(files, "old.bin")
    new = os.path.join(files, "new.bin")
    open(old, "w").write("x")
    open(new, "w").write("x")
    os.utime(old, (time.time() - 100, time.time() - 100))
    old_node = os.path.join(tmp, "node.123")
    open(old_node, "w").write("x")
    os.utime(old_node, (time.time() - 100, time.time() - 100))
    with patch.object(cache, "get_cache_dir", lambda: tmp), patch.object(
        cache, "cache_config", lambda: {"files_ttl": 1, "url_cache_ttl": 0, "db_ttl": 0}
    ):
        run(cache.clean_expired())
    check(
        "clean: files_ttl=1 删旧留新",
        not os.path.exists(old) and os.path.exists(new) and not os.path.exists(old_node),
    )
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# 9. TTL=0（默认）→ 不过期不清理
tmp = tempfile.mkdtemp()
try:
    files = os.path.join(tmp, "files")
    os.makedirs(files)
    old = os.path.join(files, "old.bin")
    open(old, "w").write("x")
    os.utime(old, (time.time() - 10000, time.time() - 10000))
    with patch.object(cache, "get_cache_dir", lambda: tmp), patch.object(
        cache, "cache_config", lambda: {"files_ttl": 0, "url_cache_ttl": 0, "db_ttl": 0}
    ):
        run(cache.clean_expired())
    check("clean: TTL=0 不过期不清理", os.path.exists(old))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# 10. url_cache_ttl：过期条目删除、未过期保留、无 time 字段的旧条目视为不过期
tmp = tempfile.mkdtemp()
try:
    url_path = os.path.join(tmp, "cached_url.json")
    json.dump(
        {
            "old": {"name": "a", "url": "u", "time": int(time.time()) - 100},
            "new": {"name": "b", "url": "u", "time": int(time.time())},
            "legacy": {"name": "c", "url": "u"},
        },
        open(url_path, "w"),
    )
    with patch.object(cache, "cached_url_path", lambda: url_path), patch.object(
        cache, "cache_config", lambda: {"files_ttl": 0, "url_cache_ttl": 10, "db_ttl": 0}
    ):
        run(cache.clean_expired())
    data = json.load(open(url_path))
    check(
        "clean: url_cache_ttl 删过期/留新/留旧格式条目",
        "old" not in data and "new" in data and "legacy" in data,
    )
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ---------- 清理 import 副作用（模块级创建的真实 .cache 目录） ----------
shutil.rmtree(".cache", ignore_errors=True)

failed = [n for n, c in results if not c]
print(f"\n共 {len(results)} 例，失败 {len(failed)} 例")
sys.exit(1 if failed else 0)
