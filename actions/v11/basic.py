import asyncio
import sys
import httpx
import actions.v12.basic as basic
from actions import register_action
from discord.abc import PrivateChannel
import utils.node2image as node2image
from discord.channel import CategoryChannel, ForumChannel
from utils.logger import discord_api_failed, get_logger
import os
import utils.translator as translator
import utils.message.v11.parser as parser
import utils.return_object as return_object
from utils.config import config
from utils.client import client
import utils.message.v11.parser as parser
import version
import discord
import actions.v12.file as file
import os.path

logger = get_logger()

@register_action("v11")
async def send_group_msg(
    group_id: int,
    message: str | list[dict],
    auto_escape: bool = False
) -> dict:
    if isinstance(message, str) and not auto_escape:
        message = parser.parse_string_to_array(message)
    elif isinstance(message, str):
        message = [{
            "type": "text",
            "data": {
                "text": message
            }
        }]
    logger.debug(message)
    return translator.translate_action_response(
        await basic.send_message(
            "group",
            await translator.translate_message_array(message),
            group_id = str(group_id)
        )
    )

@register_action("v11")
async def set_group_name(group_id: int, group_name: str) -> dict:
    return await basic.set_group_name(str(group_id), group_name)

@register_action("v11")
async def send_private_msg(
    user_id: int,
    message: str | list[dict],
    auto_escape: bool = False
) -> dict:
    if isinstance(message, str) and not auto_escape:
        message = parser.parse_string_to_array(message)
    elif isinstance(message, str):
        message = [{
            "type": "text",
            "data": {
                "text": message
            }
        }]
    return translator.translate_action_response(
        await basic.send_message(
            "private",
            await translator.translate_message_array(message),
            user_id=str(user_id)
        )
    )




@register_action("v11")
async def delete_msg(message_id: int) -> dict:
    return await basic.delete_message(str(message_id))

def clean_node_cache() -> None:
    for file in os.listdir(".cache"):
        if file.startswith("node."):
            os.remove(os.path.join(".cache", file))

@register_action("v11")
async def clean_cache() -> dict:
    await file.clean_files()
    try:
        clean_node_cache()
    except Exception:
        pass
    return return_object.get(0)

@register_action("v11")
async def send_msg(
    message: str | list,
    message_type: str,
    group_id: int | None = None,
    user_id: int | None = None,
    auto_escape: bool = False
) -> dict:
    if isinstance(message, str) and not auto_escape:
        message = parser.parse_string_to_array(message)
    elif isinstance(message, str):
        message = [{
            "type": "text",
            "data": {
                "text": message
            }
        }]
    return translator.translate_action_response(
        await basic.send_message(
            message_type,
            await translator.translate_message_array(message),
            group_id=str(group_id),
            user_id=str(user_id)
        )
    )


@register_action("v11")
async def delete_message(message_id: int) -> dict:
    return await basic.delete_message(str(message_id))

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
        await basic.get_user_info(
            str(user_id)
        )
    )


@register_action("v11")
async def get_login_info() -> dict:
    return translator.translate_action_response(
        await basic.get_self_info()
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
                message=parser.parse_string_to_array(msg.content)
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
    if is_dismiss:
        async with httpx.AsyncClient(proxies=config["system"].get("proxy")) as client:
            response = await client.delete(
                f"https://discord.com/api/v10/channels/{group_id}",
                headers={"Authorization": f"Bot {config['account_token']}"}
            )
        if response.status_code == 400:
            return discord_api_failed(response)
        return return_object.get(0)
    return translator.translate_action_response(await basic.leave_group(str(group_id)))


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

def get_role(member: discord.Member) -> str:
    for role in member.roles:
        if role.permissions.administrator:
            return "admin"
    return "member"

@register_action("v11")
async def get_group_member_list(group_id: int, no_cache: bool = False) -> dict:
    if not (channel := client.get_channel(group_id)):
        return return_object.get(1400, f"不存在的频道：{group_id}")
    member_list = []
    for member in channel.members:
        member_list.append({
            "user_id": member.id,
            "nickname": member.name,
            "card": member.display_name,
            "join_time": int(member.joined_at.timestamp()),
            "sex": "unknown",
            "role": get_role(member)
        })
    return return_object._get(
        0,
        member_list
    )

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
        role=get_role(user),
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

@register_action("v11")
async def set_group_card(group_id: int, user_id: int, card: str) -> dict:
    try:
        client.get_channel(group_id).guild.get_member(user_id).edit(
            nick=card
        )
    except discord.Forbidden:
        return return_object.get(1400, "权限错误！")
    except AttributeError as e:
        return return_object.get(1400, f"不存在的群聊或用（{e}）")
    return return_object.get(0)


@register_action("v11")
async def send_group_forward_msg(group_id: int, messages: list) -> dict:
    path = node2image.node2image(messages)
    return await send_group_msg(
        group_id=group_id,
        message=[{
            "type": "image",
            "data": {
                "file": f"file://{os.path.abspath(path)}"
            }
        }]
    )

@register_action("v11")
async def send_private_forward_msg(user_id: int, messages: list) -> dict:
    path = node2image.node2image(messages)
    return await send_private_msg(
        user_id=user_id,
        message=[{
            "type": "image",
            "data": {
                "file": f"file://{os.path.abspath(path)}"
            }
        }]
    )

async def _restart() -> None:
    script = sys.argv[0]
    args = sys.argv[1:]
    sec = config['system'].get('restart_wait_time', 3)
    logger.warning(f"程序将在 {sec}s 后重启")
    await asyncio.sleep(sec)
    os.execv(sys.executable, [sys.executable] + [script] + args)


@register_action("v11")
async def set_restart() -> dict:
    asyncio.create_task(_restart())
    return {
        "status": "async",
        "retcode": 1,
        "data": None,
        "message": ""
    }

@register_action("v11")
async def set_group_admin(group_id: int, user_id: int, enable: bool = True) -> dict:
    if not (channel := client.get_channel(group_id)):
        return return_object.get(1400, f"不存在的群聊：{group_id}")
    for m in channel.members:
        if m.id == user_id:
            member = m
            break
    else:
        return return_object.get(1400, f"不存在的用户：{user_id}")
    overwrites = channel.overwrites
    overwrites[member] = discord.PermissionOverwrite(manage_channels=enable, manage_permissions=enable)
    await channel.edit(overwrites=overwrites)
    return return_object.get(0)