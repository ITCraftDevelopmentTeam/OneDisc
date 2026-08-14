"""缓存目录 / DB 默认路径 / reply 三层解析 / 过期清理 单元测试（无需真实 Discord）"""
import json
import os
import time
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock

import discord

from utils import cache
from utils import db
from utils.message.v12 import parser


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


def patch_parser_env(cached, db_record, api_get=None):
    from contextlib import ExitStack

    stack = ExitStack()
    stack.enter_context(patch.object(parser, "client", SimpleNamespace(cached_messages=cached)))
    stack.enter_context(patch.object(parser, "get_session", lambda: FakeSession(db_record)))
    stack.enter_context(patch.object(parser.discord_api, "call", AsyncMock(return_value=api_get)))
    return stack


# ---------- reply 三层解析 ----------

async def test_reply_cached命中返回原消息对象():
    with patch_parser_env([make_msg(1001, 2001)], None):
        r = await parser._resolve_reply(1001, 3001)
        assert getattr(r, "id", None) == 1001


async def test_reply_db命中返回MessageReference():
    with patch_parser_env([], SimpleNamespace(channel=2001)):
        r = await parser._resolve_reply(1001, None)
        assert isinstance(r, discord.MessageReference) and r.channel_id == 2001


async def test_reply_rest预检成功返回MessageReference():
    with patch_parser_env([], None, api_get={}):
        r = await parser._resolve_reply(1001, 3001)
        assert isinstance(r, discord.MessageReference) and r.channel_id == 3001


async def test_reply_全miss返回None():
    async def boom(*a, **k):
        raise RuntimeError("404")

    with patch_parser_env([], None), patch.object(parser.discord_api, "call", boom):
        r = await parser._resolve_reply(1001, 3001)
        assert r is None


async def test_parse_message_reply段生成reference():
    with patch_parser_env([], SimpleNamespace(channel=2001)):
        data = await parser.parse_message([{"type": "reply", "data": {"message_id": "1001"}}])
        assert data.get("reference") is not None and data["reference"].channel_id == 2001


# ---------- DB 默认路径 ----------

def test_db_url_未配置拼接缓存目录():
    with patch.dict(db.config, {"system": {"cache_dir": "/tmp/onedisc_test_cache", "database": None}}):
        url = db._resolve_db_url()
        assert url.endswith("onedisc.db") and "onedisc_test_cache" in url


def test_db_url_显式配置原样使用():
    with patch.dict(db.config, {"system": {"cache_dir": ".cache", "database": "sqlite+aiosqlite:///:memory:"}}):
        assert db._resolve_db_url() == "sqlite+aiosqlite:///:memory:"


# ---------- 过期清理 ----------

async def test_clean_files_ttl删除过期保留新文件(tmp_path):
    files = tmp_path / "files"
    files.mkdir()
    old = files / "old.bin"
    new = files / "new.bin"
    old.write_bytes(b"x")
    new.write_bytes(b"x")
    os_old = str(old)
    os_new = str(new)
    os_utime_old = os_old
    os.utime(os_old, (time.time() - 100, time.time() - 100))
    node = tmp_path / "node.123"
    node.write_bytes(b"x")
    os.utime(str(node), (time.time() - 100, time.time() - 100))
    with patch.object(cache, "get_cache_dir", lambda: str(tmp_path)), patch.object(
        cache, "cache_config", lambda: {"files_ttl": 1, "url_cache_ttl": 0, "db_ttl": 0}
    ):
        await cache.clean_expired()
    assert not os.path.exists(os_old)
    assert os.path.exists(os_new)
    assert not os.path.exists(str(node))


async def test_clean_ttl为0不过期不清理(tmp_path):
    files = tmp_path / "files"
    files.mkdir()
    old = files / "old.bin"
    old.write_bytes(b"x")
    os.utime(str(old), (time.time() - 10000, time.time() - 10000))
    with patch.object(cache, "get_cache_dir", lambda: str(tmp_path)), patch.object(
        cache, "cache_config", lambda: {"files_ttl": 0, "url_cache_ttl": 0, "db_ttl": 0}
    ):
        await cache.clean_expired()
    assert os.path.exists(str(old))


async def test_clean_url_cache_ttl删过期留新留旧格式(tmp_path):
    url_path = tmp_path / "cached_url.json"
    url_path.write_text(
        json.dumps(
            {
                "old": {"name": "a", "url": "u", "time": int(time.time()) - 100},
                "new": {"name": "b", "url": "u", "time": int(time.time())},
                "legacy": {"name": "c", "url": "u"},
            }
        ),
        encoding="utf-8",
    )
    with patch.object(cache, "cached_url_path", lambda: str(url_path)), patch.object(
        cache, "cache_config", lambda: {"files_ttl": 0, "url_cache_ttl": 10, "db_ttl": 0}
    ):
        await cache.clean_expired()
    data = json.loads(url_path.read_text(encoding="utf-8"))
    assert "old" not in data
    assert "new" in data
    assert "legacy" in data
