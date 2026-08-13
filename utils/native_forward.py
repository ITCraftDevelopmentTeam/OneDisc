"""
Discord 原生转发支持（OneBot V11 合并转发）

Discord API 支持通过 message_reference(type=FORWARD) 转发历史消息，快照由服务端
生成，因此只需 message_id + channel_id 即可转发未被 discord.py 缓存的消息，
解决了「cached_messages 只覆盖内存中最近消息」的问题（channel 解析依赖
cached_messages 快查 + 本地数据库持久记录）。

本模块遵循「要么全部原生转发、要么整体回退」原则：can_native_forward() 对每个
node 做无损判定（引用型节点、channel 可解析、源消息可读、类型可转发、同服务器、
数量阈值），任一节点不满足即返回 None，调用方应整体回退 node2image 图片方案。
"""

from __future__ import annotations

import asyncio
from typing import Any

import discord

import utils.return_object as return_object
from utils import discord_api
from utils.client import client
from utils.config import config
from utils.db import get_session, Message
from utils.logger import get_logger

logger = get_logger()

# Discord 文档规定 FORWARD 仅支持基础消息类型：
# DEFAULT / REPLY / CHAT_INPUT_COMMAND / CONTEXT_MENU_COMMAND
_FORWARDABLE_TYPES = {
    discord.MessageType.default,
    discord.MessageType.reply,
    discord.MessageType.chat_input_command,
    discord.MessageType.context_menu_command,
}
# 对应 REST 响应中的 type 数值
_FORWARDABLE_TYPE_VALUES = {0, 19, 20, 23}

# 频道发送限流节奏：Discord 约 5 条 / 5 秒
_RATE_LIMIT_BATCH = 5
_RATE_LIMIT_SLEEP = 5.0


def _is_forwardable_message(message: discord.Message) -> bool:
    """检查 discord.Message 是否可被原生转发"""
    if message.type not in _FORWARDABLE_TYPES:
        return False
    if message.poll is not None:
        return False
    reference = message.reference
    if (
        reference is not None
        and reference.type == discord.MessageReferenceType.forward
    ):
        # 转发消息本身不能被再次转发
        return False
    return True


def _is_forwardable_api_message(data: dict) -> bool:
    """检查 REST 返回的消息数据是否可被原生转发"""
    if data.get("code") is not None:
        # 错误响应（消息不存在 / 无权限等）
        return False
    if data.get("type") not in _FORWARDABLE_TYPE_VALUES:
        return False
    if data.get("poll") is not None:
        return False
    reference = data.get("message_reference")
    if reference is not None and reference.get("type") == 1:
        # 转发消息本身不能被再次转发
        return False
    return True


async def _resolve_message(
    message_id: int,
) -> tuple[int | None, discord.Message | None]:
    """
    解析 message_id 对应的频道：cached_messages 快查 → 本地数据库

    Returns:
        (channel_id, cached_message)：缓存命中时返回消息对象，否则为 None
    """
    for message in client.cached_messages:
        if message.id == message_id:
            return message.channel.id, message
    async with get_session() as session:
        record = await session.get(Message, message_id)
    if record is not None:
        return record.channel, None
    return None, None


async def _precheck_api_message(
    channel_id: int, message_id: int, target_guild_id: int | None
) -> bool:
    """
    REST 预检：验证消息存在、可读、类型可转发、同服务器（只读，无副作用）

    必须在批量发送前完成，保证「要么全部原生、要么全部回退」的原子性
    """
    try:
        data = await discord_api.call(
            "GET", f"/channels/{channel_id}/messages/{message_id}"
        )
    except Exception:
        logger.warning(
            f"原生转发预检失败：无法读取消息 {message_id}（频道 {channel_id}）"
        )
        return False
    if not _is_forwardable_api_message(data):
        logger.warning(
            f"原生转发预检失败：消息 {message_id} 不可转发"
            f"（type={data.get('type')}）"
        )
        return False
    if target_guild_id is not None and data.get("guild_id") != target_guild_id:
        logger.warning(
            f"原生转发预检失败：消息 {message_id} 与目标不在同一服务器"
        )
        return False
    return True


async def can_native_forward(
    messages: list, target_channel_id: int
) -> list[dict] | None:
    """
    判断合并转发消息列表是否能够不折不扣地用原生 forward 发送

    Args:
        messages (list): OneBot V11 合并转发节点列表
        target_channel_id (int): 目标频道（群）ID

    Returns:
        list[dict] | None: 全部节点可转发时返回引用列表
        （[{"message_id": int, "channel_id": int}, ...]），
        任一节点需要降级时返回 None
    """
    max_nodes = config["system"].get("native_forward_max_nodes")
    if max_nodes is not None and len(messages) > int(max_nodes):
        logger.debug(
            f"合并转发节点数 {len(messages)} 超过阈值 {max_nodes}，回退图片方案"
        )
        return None

    target = client.get_channel(target_channel_id)
    target_guild_id = getattr(getattr(target, "guild", None), "id", None)

    refs: list[dict] = []
    for node in messages:
        if not isinstance(node, dict) or node.get("type") != "node":
            return None
        data = node.get("data") or {}
        message_id = data.get("message_id")
        if message_id is None:
            # 内联内容节点（user_id + nickname + content）无法原生转发
            return None
        try:
            message_id = int(message_id)
        except (TypeError, ValueError):
            return None

        channel_id, cached = await _resolve_message(message_id)
        if channel_id is None:
            logger.warning(
                f"原生转发：找不到消息 {message_id} 的频道"
                "（缓存与数据库均无记录），回退图片方案"
            )
            return None

        if cached is not None:
            if not _is_forwardable_message(cached):
                return None
            source_guild_id = getattr(getattr(cached, "guild", None), "id", None)
        else:
            if not await _precheck_api_message(
                channel_id, message_id, target_guild_id
            ):
                return None
            source_guild_id = None  # 服务器一致性已在预检中校验

        if (
            target_guild_id is not None
            and source_guild_id is not None
            and source_guild_id != target_guild_id
        ):
            # 跨服务器转发不受支持
            return None

        refs.append({"message_id": message_id, "channel_id": channel_id})
    return refs


async def send_native_forward(target_channel_id: int, refs: list[dict]) -> dict:
    """
    按引用列表批量发送原生转发，遵守频道发送限流（约 5 条 / 5 秒）

    Args:
        target_channel_id (int): 目标频道（群）ID
        refs (list[dict]): can_native_forward 返回的引用列表

    Returns:
        dict: OneBot 动作响应
    """
    if client.get_channel(target_channel_id) is None:
        return return_object.get(10003, "无效的频道号")
    for index, ref in enumerate(refs):
        if index > 0 and index % _RATE_LIMIT_BATCH == 0:
            await asyncio.sleep(_RATE_LIMIT_SLEEP)
        try:
            response: dict[str, Any] = await discord_api.call(
                "POST",
                f"/channels/{target_channel_id}/messages",
                {
                    "message_reference": {
                        "type": 1,  # MessageReferenceType.FORWARD
                        "message_id": str(ref["message_id"]),
                        "channel_id": str(ref["channel_id"]),
                    }
                },
            )
        except Exception as exc:
            logger.error(f"原生转发失败（已发送 {index} 条）：{exc}")
            return return_object.get(1400, f"原生转发失败：{exc}")
        if response.get("code") is not None:
            logger.error(f"原生转发失败（已发送 {index} 条）：{response}")
            return return_object.get(
                1400, f"原生转发失败：{response.get('message')}"
            )
    logger.info(f"原生转发完成，共 {len(refs)} 条")
    return return_object.get(0)
