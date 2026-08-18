"""Discord 转发消息自动合并为 OneBot V11 合并转发（forward）

机制：同一频道同一发送者的「转发」消息（message_reference.type == forward），
在 merge_forward_interval（默认 500ms）窗口内自动合并：
- 第一条到达时立即上报一条 forward 段消息，id 编码为「频道id_消息id」
- 窗口内后续满足条件的转发消息被吸收（不单独上报）
- 框架收到 forward 段后调用 get_forward_msg 动作，用 id 解码出第一条消息，
  通过 Discord REST API（GET /channels/{cid}/messages?around=）拉取上下文，
  按「同作者 + forward 类型 + 窗口时间范围」重建完整合并列表
  实现完全无状态：不依赖内存暂存，进程重启后依然可用

可通过 system.merge_forward（默认 true）开关，system.merge_forward_interval
（毫秒，默认 500）调节窗口时长。
"""
from datetime import datetime, timedelta, timezone
import discord
from utils.config import config
from utils.logger import get_logger
from utils import discord_api
import utils.message.v11.parser as parser

logger = get_logger()

# (channel_id, author_id) → {"first_id": int, "first_created_at": datetime}
# 仅用于实时拦截窗口，条目随新第一条覆盖，不会无限增长
_first_records: dict[tuple[int, int], dict] = {}

# Discord message_reference.type：1 = 转发，0 = 引用回复
FORWARD_REFERENCE_TYPE = 1


def _interval_ms() -> int:
    return int(config["system"].get("merge_forward_interval", 500))


def is_forward_message(message: discord.Message) -> bool:
    """是否为 Discord 的「转发」消息（区别于引用回复）"""
    return bool(message.reference) and (
        message.reference.type == discord.MessageReferenceType.forward
    )


def build_forward_id(channel_id: int, message_id: int) -> str:
    """第一条消息的转发 id：编码频道与消息，可无状态重建"""
    return f"{channel_id}_{message_id}"


def parse_forward_id(forward_id: str) -> tuple[int, int] | None:
    """解码转发 id 为（频道 id，消息 id），非法返回 None"""
    try:
        channel_id, message_id = forward_id.split("_", 1)
        return int(channel_id), int(message_id)
    except (ValueError, AttributeError):
        return None


def handle_forward_message(message: discord.Message) -> bool:
    """
    处理转发消息。返回 True 表示已被合并转发流程接管
    （第一条已上报 forward 段消息，后续消息被吸收），调用方不应再单独上报
    """
    if not is_forward_message(message):
        return False
    if not config["system"].get("merge_forward", True):
        return False

    key = (message.channel.id, message.author.id)
    record = _first_records.get(key)
    if record is not None and (
        message.created_at - record["first_created_at"]
    ).total_seconds() * 1000 <= _interval_ms():
        # 窗口内：吸收进合并列表，不单独上报
        logger.debug(f"转发消息 {message.id} 已并入合并转发 {record['first_id']}")
        return True

    # 新第一条：记录窗口基准，上报 forward 段
    _first_records[key] = {
        "first_id": message.id,
        "first_created_at": message.created_at,
    }
    _report_forward_message(
        message, build_forward_id(message.channel.id, message.id)
    )
    logger.info(
        f"开启合并转发 {build_forward_id(message.channel.id, message.id)}"
        f"（频道 {message.channel.id}，发送者 {message.author.id}）"
    )
    return True


def _report_forward_message(message: discord.Message, forward_id: str) -> None:
    """上报一条 forward 段消息事件（与普通消息上报相同的频道类型分支）"""
    from utils import event

    message_array = [{"type": "forward", "data": {"id": forward_id}}]
    common = {
        "_type": "message",
        "_time": message.created_at.timestamp(),
        "message_id": str(message.id),
        "message": message_array,
        "alt_message": forward_id,
        "user_id": str(message.author.id),
    }
    if message.guild and config["system"].get("enable_channel_event"):
        event.new_event(
            detail_type="channel",
            guild_id=str(message.guild.id),
            channel_id=str(message.channel.id),
            **common,
        )
    elif message.guild:
        event.new_event(
            detail_type="group",
            group_id=str(message.channel.id),
            **common,
        )
    else:
        event.new_event(detail_type="private", **common)


def _is_forward_data(data: dict) -> bool:
    """Discord 消息 JSON 是否为转发消息"""
    reference = data.get("message_reference")
    return bool(reference) and reference.get("type") == FORWARD_REFERENCE_TYPE


def _parse_timestamp(timestamp: str | None) -> datetime | None:
    if not timestamp:
        return None
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None


# 翻页上限，防止异常情况下无限拉取
MAX_PAGES = 10


async def _fetch_merge_messages(
    channel_id: int, message_id: int
) -> list[dict] | None:
    """
    以第一条消息为起点拉取上下文：第一页用 around（含第一条），
    若最新一条仍在窗口内且窗口内消息全部符合条件，则用 after 继续向前翻页，
    直到窗口结束、序列中断或拉不到更多。失败返回 None
    """
    collected: list[dict] = []
    cursor = str(message_id)
    first_page = True
    for _ in range(MAX_PAGES):
        params = {
            "around" if first_page else "after": cursor,
            "limit": "100",
        }
        try:
            data = await discord_api.call(
                "GET", f"/channels/{channel_id}/messages", params=params
            )
        except Exception:
            logger.warning(f"获取合并转发上下文失败（频道 {channel_id}，消息 {cursor}）")
            return None
        if not isinstance(data, list):
            logger.warning(f"获取合并转发上下文返回异常（频道 {channel_id}）")
            return None
        collected.extend(data)
        first_page = False

        first = next(
            (m for m in collected if str(m.get("id")) == str(message_id)), None
        )
        if first is None:
            logger.warning(f"合并转发第一条消息 {message_id} 不在返回上下文中")
            return None
        first_time = _parse_timestamp(first.get("timestamp"))
        if first_time is None:
            return None
        author_id = str(first.get("author", {}).get("id"))
        window_end = first_time + timedelta(milliseconds=_interval_ms())

        # 拉取结果中最新的一条（Discord 消息 API 按时间倒序，即列表首条）
        newest = max(
            collected,
            key=lambda m: _parse_timestamp(m.get("timestamp")) or first_time,
        )
        newest_time = _parse_timestamp(newest.get("timestamp"))
        if newest_time is None or newest_time > window_end:
            # 最后一条已超出窗口：窗口内消息已完整，停止
            break
        # 窗口内所有消息都符合条件（同作者转发）才继续：序列中断则停止
        in_window = [
            m
            for m in collected
            if first_time <= _parse_timestamp(m.get("timestamp")) <= window_end
        ]
        if not in_window or not all(
            _is_forward_data(m)
            and str(m.get("author", {}).get("id")) == author_id
            for m in in_window
        ):
            break
        if str(newest.get("id")) == cursor:
            # 翻页没有拉到更新的消息，停止
            break
        # 最后一条仍在窗口内且全部符合：从它继续向前拉取
        cursor = str(newest.get("id"))
    return collected


def _data_to_node(data: dict) -> dict:
    """Discord 消息 JSON → v11 node 节点（显示快照中的原作者与内容）"""
    snapshot = None
    snapshots = data.get("message_snapshots")
    if snapshots:
        snapshot = snapshots[0].get("message")
    source = snapshot or data
    author = source.get("author", {})
    segments = parser.parse_string_to_array(source.get("content") or "")
    for attachment in source.get("attachments", []):
        content_type = attachment.get("content_type", "") or ""
        if content_type.startswith("image"):
            segments.append(
                {"type": "image", "data": {"file": attachment.get("url", "")}}
            )
        elif content_type.startswith("video"):
            segments.append(
                {"type": "video", "data": {"file": attachment.get("url", "")}}
            )
    return {
        "user_id": author.get("id"),
        "nickname": author.get("username") or str(author.get("id")),
        "content": segments,
    }


async def get_forward(forward_id: str) -> list[dict] | None:
    """
    按 id 取合并转发节点列表（get_forward_msg 动作使用）。
    通过第一条消息调 Discord REST API 拉取上下文重建，失败或不存在返回 None
    """
    parsed = parse_forward_id(forward_id)
    if parsed is None:
        return None
    channel_id, message_id = parsed
    collected = await _fetch_merge_messages(channel_id, message_id)
    if collected is None:
        return None

    first = next(
        (message for message in collected if str(message.get("id")) == str(message_id)),
        None,
    )
    if first is None:
        return None
    first_time = _parse_timestamp(first.get("timestamp"))
    if first_time is None:
        return None
    author_id = str(first.get("author", {}).get("id"))
    window = timedelta(milliseconds=_interval_ms())
    merged = [
        message
        for message in collected
        if _is_forward_data(message)
        and str(message.get("author", {}).get("id")) == author_id
        and first_time
        <= _parse_timestamp(message.get("timestamp"))
        <= first_time + window
    ]
    merged.sort(key=lambda message: message["timestamp"])
    return [_data_to_node(message) for message in merged]
