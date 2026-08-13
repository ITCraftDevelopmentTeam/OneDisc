"""转发消息自动合并（forward merge）单元测试：无状态 + REST 上下文重建"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.path.insert(0, "/vol2/@apphome/trim.openclaw/data/workspace/onedisc-dev")

import discord

from utils import forward_merge as fm


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


results = []


def check(name, cond):
    results.append((name, bool(cond)))
    print(f"{'✅' if cond else '❌'} {name}")


NOW = datetime(2026, 8, 14, 7, 0, 0, tzinfo=timezone.utc)


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


def reset():
    fm._first_records.clear()


# ---------- is_forward_message ----------
check(
    "is_forward: forward 类型 → True",
    fm.is_forward_message(make_msg(1, ref_type=discord.MessageReferenceType.forward)),
)
check(
    "is_forward: reply 类型 → False",
    not fm.is_forward_message(make_msg(2, ref_type=discord.MessageReferenceType.default)),
)
check("is_forward: 无 reference → False", not fm.is_forward_message(make_msg(3, ref_type=None)))

# ---------- build/parse forward id ----------
fid = fm.build_forward_id(2001, 12345)
check("build_forward_id 编码频道+消息", fid == "2001_12345")
check("parse_forward_id 解码正常", fm.parse_forward_id(fid) == (2001, 12345))
check("parse_forward_id 非法返回 None", fm.parse_forward_id("no_such_id") is None)
check("parse_forward_id 空串返回 None", fm.parse_forward_id("") is None)

# ---------- handle_forward_message ----------
reset()
with patch_config(), patch("utils.event.new_event") as new_event:
    r = fm.handle_forward_message(make_msg(10))
    check("handle: 第一条返回 True", r is True)
    check("handle: 第一条上报 forward 段", new_event.called)
    if new_event.called:
        kwargs = new_event.call_args.kwargs
        seg = kwargs["message"][0]
        check(
            "handle: 上报内容为 forward 段且 id=频道_消息",
            seg["type"] == "forward" and seg["data"]["id"] == "2001_10",
        )

    # 窗口内第二条（created_at +300ms）：吸收、不重复上报
    r2 = fm.handle_forward_message(make_msg(11, created_at=NOW + timedelta(milliseconds=300)))
    check("handle: 窗口内第二条被吸收返回 True", r2 is True)
    check("handle: 窗口内第二条不重复上报", new_event.call_count == 1)

    # 超过窗口（+600ms）：开新窗口并上报
    r3 = fm.handle_forward_message(make_msg(12, created_at=NOW + timedelta(milliseconds=600)))
    check("handle: 超窗口消息开新窗口", r3 is True and new_event.call_count == 2)
    check(
        "handle: 新窗口 id 用第二条消息",
        new_event.call_args.kwargs["message"][0]["data"]["id"] == "2001_12",
    )

    # 同频道不同发送者：各自独立窗口
    r4 = fm.handle_forward_message(make_msg(13, author=("2002", "Bob")))
    check("handle: 不同发送者开新窗口", r4 is True and new_event.call_count == 3)

reset()
with patch_config(merge_forward=False), patch("utils.event.new_event") as new_event:
    r5 = fm.handle_forward_message(make_msg(20))
    check("handle: merge_forward=false 不处理", r5 is False and not new_event.called)

with patch_config(), patch("utils.event.new_event") as new_event:
    r6 = fm.handle_forward_message(make_msg(21, ref_type=None))
    check("handle: 非转发消息不处理", r6 is False and not new_event.called)

# ---------- get_forward（REST 上下文重建） ----------
# 场景：第一条 100（t0），窗口内 101（+300ms）同作者转发；窗口外 102（+1s）同作者转发
# 应被排除：103（+200ms，reply 类型）、104（+200ms，不同作者转发）、105（+200ms，普通消息）
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
    nodes = run(fm.get_forward("2001_100"))
    check("get_forward: 重建出 2 个节点", nodes is not None and len(nodes) == 2)
    check("get_forward: 按时间升序（第一条在前）", nodes[0]["user_id"] == "9999" and nodes[1]["user_id"] == "8888")
    check(
        "get_forward: 节点用快照原作者/内容",
        nodes[0]["nickname"] == "原作者" and nodes[0]["content"][0]["data"]["text"] == "原始内容",
    )
    check(
        "get_forward: 调用 REST around 接口",
        call_mock.await_args.args[1] == "/channels/2001/messages"
        and call_mock.await_args.kwargs["params"]["around"] == "100",
    )

# REST 失败 → None
with patch_config(), patch.object(
    fm.discord_api, "call", new=AsyncMock(side_effect=Exception("网络错误"))
):
    check("get_forward: REST 异常返回 None", run(fm.get_forward("2001_100")) is None)

# 第一条不在上下文中 → None
with patch_config(), patch.object(
    fm.discord_api, "call", new=AsyncMock(return_value=[msg_json(999, NOW)])
):
    check("get_forward: 第一条缺失返回 None", run(fm.get_forward("2001_100")) is None)

# 非法 id → None（不调 REST）
with patch_config(), patch.object(
    fm.discord_api, "call", new=AsyncMock()
) as call_mock:
    check("get_forward: 非法 id 返回 None", run(fm.get_forward("no_such_id")) is None)
    check("get_forward: 非法 id 不调 REST", not call_mock.called)

# ---------- 翻页：最后一条仍在窗口内且全部符合 → after 继续拉 ----------
# 第一页（倒序）：101(+300ms) 100(t0)，最后一条 101 在窗口内且全部符合 → 翻页
# 第二页（after=101，倒序）：103(+600ms 超窗) 102(+400ms) → 停止
with patch_config(), patch.object(
    fm.discord_api, "call", new=AsyncMock(side_effect=[[
        msg_json(101, NOW + timedelta(milliseconds=300), snapshot={"content": "第二", "user_id": 8888}),
        msg_json(100, NOW, snapshot={"content": "原始内容", "user_id": 9999, "nickname": "原作者"}),
    ], [
        msg_json(103, NOW + timedelta(milliseconds=600), snapshot={"content": "超窗", "user_id": 9999}),
        msg_json(102, NOW + timedelta(milliseconds=400), snapshot={"content": "第三", "user_id": 7777}),
    ]])) as call_mock:

    nodes = run(fm.get_forward("2001_100"))
    check("翻页: 合并 3 条（100/101/102）", nodes is not None and len(nodes) == 3)
    check("翻页: 按时间升序", [n["user_id"] for n in nodes] == ["9999", "8888", "7777"])
    check("翻页: 共调用 2 次 REST", call_mock.await_count == 2)
    check(
        "翻页: 第二次用 after=最后一条(101)",
        call_mock.await_args.args[1] == "/channels/2001/messages"
        and call_mock.await_args.kwargs["params"] == {"after": "101", "limit": "100"},
    )

# 第一页最后一条已超窗 → 不翻页
with patch_config(), patch.object(
    fm.discord_api, "call", new=AsyncMock(return_value=[
        msg_json(102, NOW + timedelta(milliseconds=600), snapshot={"content": "超窗"}),
        msg_json(101, NOW + timedelta(milliseconds=300), snapshot={"content": "第二"}),
        msg_json(100, NOW, snapshot={"content": "原始内容", "user_id": 9999}),
    ])
) as call_mock:
    nodes = run(fm.get_forward("2001_100"))
    check("超窗即停: 合并 2 条", nodes is not None and len(nodes) == 2)
    check("超窗即停: 只调用 1 次 REST", call_mock.await_count == 1)

# 窗口内出现不符合条件的消息（不同作者转发）→ 不翻页，序列中断
with patch_config(), patch.object(
    fm.discord_api, "call", new=AsyncMock(return_value=[
        msg_json(101, NOW + timedelta(milliseconds=300), author="2002", snapshot={"content": "别人"}),
        msg_json(100, NOW, snapshot={"content": "原始内容", "user_id": 9999}),
    ])
) as call_mock:
    nodes = run(fm.get_forward("2001_100"))
    check("序列中断: 只合并第一条", nodes is not None and len(nodes) == 1)
    check("序列中断: 不翻页", call_mock.await_count == 1)

failed = [n for n, c in results if not c]
print(f"\n共 {len(results)} 例，失败 {len(failed)} 例")
sys.exit(1 if failed else 0)
