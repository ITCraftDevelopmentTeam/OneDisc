"""转发消息自动合并（forward merge）单元测试：无状态 + REST 上下文重建"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

import discord

from utils import forward_merge as fm

NOW = datetime(2026, 8, 14, 7, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def reset_state():
    fm._first_records.clear()
    yield
    fm._first_records.clear()


def make_msg(
    mid,
    cid=2001,
    author=("1001", "Alice"),
    ref_type=discord.MessageReferenceType.forward,
    content="",
    snapshot=None,
    guild=True,
    created_at=NOW,
):
    ref = (
        SimpleNamespace(type=ref_type, message_id=123, channel_id=cid)
        if ref_type is not None
        else None
    )
    snapshots = []
    if snapshot is not None:
        snapshots = [
            SimpleNamespace(
                message=SimpleNamespace(
                    content=snapshot.get("content", "快照内容"),
                    attachments=snapshot.get("attachments", []),
                    author=SimpleNamespace(
                        id=snapshot.get("user_id", 9999),
                        name=snapshot.get("nickname", "原作者"),
                    ),
                )
            )
        ]
    return SimpleNamespace(
        id=mid,
        channel=SimpleNamespace(id=cid),
        author=SimpleNamespace(id=author[0], name=author[1]),
        content=content,
        attachments=[],
        reference=ref,
        message_snapshots=snapshots,
        guild=SimpleNamespace(id=111) if guild else None,
        created_at=created_at,
    )


def msg_json(mid, ts, author="1001", ref_type=1, content="", snapshot=None):
    """REST 返回的消息 JSON"""
    ref = {"type": ref_type, "message_id": 123, "channel_id": 2001} if ref_type is not None else None
    snapshots = []
    if snapshot is not None:
        snapshots = [
            {
                "message": {
                    "content": snapshot.get("content", "快照内容"),
                    "attachments": snapshot.get("attachments", []),
                    "author": {
                        "id": str(snapshot.get("user_id", 9999)),
                        "username": snapshot.get("nickname", "原作者"),
                    },
                }
            }
        ]
    return {
        "id": str(mid),
        "channel_id": "2001",
        "author": {"id": str(author), "username": f"用户{author}"},
        "content": content,
        "attachments": [],
        "message_reference": ref,
        "message_snapshots": snapshots,
        "timestamp": ts.isoformat(),
    }


def patch_config(**system):
    merged = {
        **fm.config["system"],
        "merge_forward": True,
        "merge_forward_interval": 500,
        **system,
    }
    return patch.dict(fm.config, {"system": merged})


# ---------- is_forward_message ----------

def test_is_forward_forward类型():
    assert fm.is_forward_message(make_msg(1, ref_type=discord.MessageReferenceType.forward))


def test_is_forward_reply类型():
    assert not fm.is_forward_message(make_msg(2, ref_type=discord.MessageReferenceType.default))


def test_is_forward_无reference():
    assert not fm.is_forward_message(make_msg(3, ref_type=None))


# ---------- build/parse forward id ----------

def test_forward_id_编码解码():
    fid = fm.build_forward_id(2001, 12345)
    assert fid == "2001_12345"
    assert fm.parse_forward_id(fid) == (2001, 12345)


def test_forward_id_非法返回None():
    assert fm.parse_forward_id("no_such_id") is None
    assert fm.parse_forward_id("") is None


# ---------- handle_forward_message ----------

def test_handle_第一条上报forward段():
    with patch_config(), patch("utils.event.new_event") as new_event:
        assert fm.handle_forward_message(make_msg(10)) is True
        assert new_event.called
        seg = new_event.call_args.kwargs["message"][0]
        assert seg["type"] == "forward" and seg["data"]["id"] == "2001_10"


def test_handle_窗口内第二条被吸收():
    with patch_config(), patch("utils.event.new_event") as new_event:
        fm.handle_forward_message(make_msg(10))
        r = fm.handle_forward_message(make_msg(11, created_at=NOW + timedelta(milliseconds=300)))
        assert r is True
        assert new_event.call_count == 1


def test_handle_超窗口消息开新窗口():
    with patch_config(), patch("utils.event.new_event") as new_event:
        fm.handle_forward_message(make_msg(10))
        r = fm.handle_forward_message(make_msg(12, created_at=NOW + timedelta(milliseconds=600)))
        assert r is True
        assert new_event.call_count == 2
        assert new_event.call_args.kwargs["message"][0]["data"]["id"] == "2001_12"


def test_handle_不同发送者独立窗口():
    with patch_config(), patch("utils.event.new_event") as new_event:
        fm.handle_forward_message(make_msg(10))
        r = fm.handle_forward_message(make_msg(13, author=("2002", "Bob")))
        assert r is True
        assert new_event.call_count == 2


def test_handle_开关关闭不处理():
    with patch_config(merge_forward=False), patch("utils.event.new_event") as new_event:
        assert fm.handle_forward_message(make_msg(20)) is False
        assert not new_event.called


def test_handle_非转发消息不处理():
    with patch_config(), patch("utils.event.new_event") as new_event:
        assert fm.handle_forward_message(make_msg(21, ref_type=None)) is False
        assert not new_event.called


# ---------- get_forward（REST 上下文重建） ----------

async def test_get_forward_窗口筛选重建():
    messages = [
        msg_json(100, NOW, snapshot={"content": "原始内容", "user_id": 9999, "nickname": "原作者"}),
        msg_json(101, NOW + timedelta(milliseconds=300), snapshot={"content": "第二条", "user_id": 8888, "nickname": "二号"}),
        msg_json(102, NOW + timedelta(seconds=1), snapshot={"content": "超窗", "user_id": 7777}),
        msg_json(103, NOW + timedelta(milliseconds=200), ref_type=0, content="回复"),
        msg_json(104, NOW + timedelta(milliseconds=200), author="2002", snapshot={"content": "别人"}),
        msg_json(105, NOW + timedelta(milliseconds=200), ref_type=None, content="普通"),
    ]
    with patch_config(), patch.object(
        fm.discord_api, "call", new=AsyncMock(return_value=messages)
    ) as call_mock:
        nodes = await fm.get_forward("2001_100")
        assert nodes is not None and len(nodes) == 2
        assert nodes[0]["user_id"] == "9999" and nodes[1]["user_id"] == "8888"
        assert nodes[0]["nickname"] == "原作者"
        assert nodes[0]["content"][0]["data"]["text"] == "原始内容"
        assert call_mock.await_args.args[1] == "/channels/2001/messages"
        assert call_mock.await_args.kwargs["params"]["around"] == "100"


async def test_get_forward_rest异常返回None():
    with patch_config(), patch.object(
        fm.discord_api, "call", new=AsyncMock(side_effect=Exception("网络错误"))
    ):
        assert await fm.get_forward("2001_100") is None


async def test_get_forward_第一条缺失返回None():
    with patch_config(), patch.object(
        fm.discord_api, "call", new=AsyncMock(return_value=[msg_json(999, NOW)])
    ):
        assert await fm.get_forward("2001_100") is None


async def test_get_forward_非法id不调REST():
    with patch_config(), patch.object(
        fm.discord_api, "call", new=AsyncMock()
    ) as call_mock:
        assert await fm.get_forward("no_such_id") is None
        assert not call_mock.called


# ---------- 翻页：最后一条仍在窗口内且全部符合 → after 继续拉 ----------

async def test_get_forward_翻页合并():
    with patch_config(), patch.object(
        fm.discord_api, "call", new=AsyncMock(side_effect=[[
            msg_json(101, NOW + timedelta(milliseconds=300), snapshot={"content": "第二", "user_id": 8888}),
            msg_json(100, NOW, snapshot={"content": "原始内容", "user_id": 9999, "nickname": "原作者"}),
        ], [
            msg_json(103, NOW + timedelta(milliseconds=600), snapshot={"content": "超窗", "user_id": 9999}),
            msg_json(102, NOW + timedelta(milliseconds=400), snapshot={"content": "第三", "user_id": 7777}),
        ]])
    ) as call_mock:
        nodes = await fm.get_forward("2001_100")
        assert nodes is not None and len(nodes) == 3
        assert [n["user_id"] for n in nodes] == ["9999", "8888", "7777"]
        assert call_mock.await_count == 2
        assert call_mock.await_args.kwargs["params"] == {"after": "101", "limit": "100"}


async def test_get_forward_超窗即停不翻页():
    with patch_config(), patch.object(
        fm.discord_api, "call", new=AsyncMock(return_value=[
            msg_json(102, NOW + timedelta(milliseconds=600), snapshot={"content": "超窗"}),
            msg_json(101, NOW + timedelta(milliseconds=300), snapshot={"content": "第二"}),
            msg_json(100, NOW, snapshot={"content": "原始内容", "user_id": 9999}),
        ])
    ) as call_mock:
        nodes = await fm.get_forward("2001_100")
        assert nodes is not None and len(nodes) == 2
        assert call_mock.await_count == 1


async def test_get_forward_序列中断不翻页():
    with patch_config(), patch.object(
        fm.discord_api, "call", new=AsyncMock(return_value=[
            msg_json(101, NOW + timedelta(milliseconds=300), author="2002", snapshot={"content": "别人"}),
            msg_json(100, NOW, snapshot={"content": "原始内容", "user_id": 9999}),
        ])
    ) as call_mock:
        nodes = await fm.get_forward("2001_100")
        assert nodes is not None and len(nodes) == 1
        assert call_mock.await_count == 1
