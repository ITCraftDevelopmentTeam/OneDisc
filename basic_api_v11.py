import basic_actions_v12
from api import register_action
from discord.abc import PrivateChannel
from discord.channel import CategoryChannel, ForumChannel
from logger import get_logger
import translator
import message_parser_v11
import return_object
from config import config
from client import client
import message_parser_v11
import version

logger = get_logger()

@register_action("v11")
async def send_group_msg(
    group_id: int,
    message: str | list[dict],
    auto_escape: bool = False
) -> dict:
    if isinstance(message, str) and not auto_escape:
        message = message_parser_v11.parse_text(message)
    elif isinstance(message, str):
        message = [{
            "type": "text",
            "data": {
                "text": message
            }
        }]
    return translator.translate_action_response(
        await basic_actions_v12.send_message(
            "group",
            translator.translate_message_array(message),
            group_id = str(group_id)
        )
    )



@register_action("v11")
async def send_msg(
    message: str | list,
    message_type: str,
    group_id: int | None = None,
    user_id: int | None = None,
    auto_escape: bool = False
) -> dict:
    if isinstance(message, str) and not auto_escape:
        message = message_parser_v11.parse_text(message)
    elif isinstance(message, str):
        message = [{
            "type": "text",
            "data": {
                "text": message
            }
        }]
    return translator.translate_action_response(
        await basic_actions_v12.send_message(
            message_type,
            translator.translate_message_array(message),
            group_id=str(group_id),
            user_id=str(user_id)
        )
    )


@register_action("v11")
async def delete_message(message_id: int) -> dict:
    return await basic_actions_v12.delete_message(str(message_id))

@register_action("v11")
async def get_stranger_info(
    user_id: int,
    no_cache: bool = False
) -> dict:
    # resp_data = translator.translate_action_response(
        # await basic_actions_v12.get_user_info(
            # str(user_id)
        # )
    # )
    # resp_data["data"]["nickname"] = resp_data["data"].get("user_name", "")
    # resp_data["data"]["sex"] = "unknown"
    return translator.translate_action_response(
        await basic_actions_v12.get_user_info(
            str(user_id)
        )
    )


@register_action("v11")
async def get_login_info() -> dict:
    return translator.translate_action_response(
        await basic_actions_v12.get_self_info()
    )

@register_action("v11")
async def get_msg(message_id: int) -> dict:
    for msg in client.cached_messages:
        if msg.id == message_id:
            return return_object.get(
                0,
                time=-1,
                message_type="normal",
                message_id=msg.id,
                real_id=msg.id,
                sender={
                    "user_id": msg.author.id,
                    "nickname": msg.author.name,
                    "card": msg.author.display_name,
                    "sex": "unknown"
                },
                message=message_parser_v11.parse_text(msg.content)
            )
    return return_object.get(
        1404,
        "消息不存在！"
    )

@register_action("v11")
async def set_group_kick(group_id: int, user_id: int, reason: str | None = None, reject_add_request: bool = False) -> dict:
    if not (group := client.get_channel(group_id)):
        return return_object.get(1400, f"不存在的频道：{group_id}")
    if isinstance(group, PrivateChannel | ForumChannel | CategoryChannel):
        return return_object.get(1400, f"不支持的操作：从 {type(group)} 中移除 {user_id}")
    for user in group.members:
        if user.id == user_id:
            await user.kick(reason=reason)  # type: ignore
            logger.info(f"已将 {user.name} ({user.id}) 从频道 {group.name} 中移除") # type: ignore
            return return_object.get(0)
    return return_object.get(1400, f"未找到用户：{user_id} （在 {group.id} 中）")


@register_action("v11")
async def set_group_ban(group_id: int, user_id: int, duration: int = 1800, reason: str | None = None) -> dict:
    if not (group := client.get_channel(group_id)):
        return return_object.get(1400, f"不存在的频道：{group_id}")
    if isinstance(group, PrivateChannel | ForumChannel | CategoryChannel):
        return return_object.get(1400, f"不支持的操作：从 {type(group)} 中禁言 {user_id}")
    for user in group.members:
        if user.id == user_id:
            await user.ban(delete_message_seconds=duration, reason=reason)  # type: ignore
            logger.info(f"已将 {user.name} ({user.id}) 从频道 {group.name} 中移除") # type: ignore
            return return_object.get(0)
    return return_object.get(1400, f"未找到用户：{user_id} （在 {group.id} 中）")


@register_action("v11")
async def set_group_leave(group_id: int, is_dismiss: bool = False) -> dict:
    return translator.translate_action_response(await basic_actions_v12.leave_group(str(group_id)))


@register_action("v11")
async def get_friend_list() -> dict:
    return return_object._get(0, [])

@register_action("v11")
async def get_group_info(group_id: int, no_cache: bool = False) -> dict:
    if not (channel := client.get_channel(group_id)):
        return return_object.get(1400, "频道不存在")
    return return_object.get(
        0,
        group_id=channel.id,
        group_name=channel.name if hasattr(channel, "name") else "",        # type: ignore
        member_count=channel.member_count if hasattr(channel, "member_count") else -1,      # type: ignore
        max_member_count=config["system"].get("default_max_member_count", -1)
    )

@register_action("v11")
async def get_group_list() -> dict:
    channel_list = []
    for channel in client.get_all_channels():
        channel_list.append({
            "group_id": channel.id,
            "group_name": channel.name if hasattr(channel, "name") else "",
            "member_count": channel.member_count if hasattr(channel, "member_count") else "",        # type: ignore
            "max_member_count": config["system"].get("default_max_member_count", -1)
        })
    return return_object._get(0, channel_list)


@register_action("v11")
async def get_group_member_info(group_id: int, user_id: int, no_cache: bool = False) -> dict:
    if not (channel := client.get_channel(group_id)):
        return return_object.get(1400, f"不存在的频道：{group_id}")
    for member in channel.members:
        if member.id == user_id:
            user = member
            break
    else:
        return return_object.get(1400, f"不存在的用户（在 {channel.id} 中）：{user_id}")
    return return_object.get(
        0,
        group_id=channel.id,
        user_id=user.id,
        nickname=user.name,
        card=user.display_name,
        sex="unknown",
        join_time=int(user.joined_at.timestamp())
    )

@register_action("v11")
async def can_send_image() -> dict:
    return return_object.get(0, yes=True)


@register_action("v11")
async def can_send_record() -> dict:
    return return_object.get(0, yes=config["system"].get("can_send_record", False))


@register_action("v11")
async def get_status() -> dict:
    return return_object.get(0, online=client.is_ready() and not client.is_closed(), good=True)

@register_action("v11")
async def get_version_info() -> dict:
    return return_object.get(
        0,
        app_name="onedisc",
        app_version=version.VERSION,
        protocol_version="v11"
    )



