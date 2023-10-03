import discord
from version import VERSION
from typing import Callable
import return_object
import time
import message_parser
from logger import get_logger

client: discord.Client
config: dict
logger = get_logger()


def init(_client: discord.Client, _config: dict) -> None:
    """
    初始化API

    Args:
        client (discord.Client): Discord客户端
        config (dict): 全局配置
    """
    global client, config
    client = _client
    config = _config


async def send_message(
        detail_type: str,
        message: list,
        user_id: str | None = None,
        group_id: str | None = None,
        guild_id: str | None = None,
        channel_id: str | None = None,
        **params
) -> dict:
    """
    发送消息

    Args:
        detail_type (str): 发送的类型，为`private`、`group`或`channel`
        message (list): 消息内容
        user_id (str | None, optional): 用户ID. Defaults to None.
        group_id (str | None, optional): 群ID. Defaults to None..
        guild_id (str | None, optional): 群组ID. Defaults to None..
        channel_id (str | None, optional): 频道ID. Defaults to None.

    Returns:
        dict: 返回数据
    """
    match detail_type:
        case "group":
            _channel_id = group_id
        case "private":
            _channel_id = user_id
        case "channel":
            _channel_id = channel_id
        case _:
            logger.warning("无效的消息类型")
            return return_object.get(10003)
    if not _channel_id:
        logger.warning("无效的频道号")
        return return_object.get(10003)

    if not (channel := client.get_channel(int(_channel_id))):
        logger.warning(f"频道 {group_id} 不存在")
        return return_object.get(35001, "频道（群号）不存在")
    parsed_message = message_parser.parse_message(message)
    msg = await channel.send(**parsed_message) # type: ignore
    message_id = msg.id

    return return_object.get(0, message_id=message_id, time=time.time())


async def get_supported_actions() -> dict:
    """
    获取支持的动作列表

    Returns:
        dict: 响应数据
    """
    return {
        "status": "ok",
        "retcode": 0,
        "data": list(action_list.keys()),
        "message": ""
    }


async def get_status() -> dict:
    return return_object.get(
        0, good=True,
        bots=[{
            "self": {
                "platform": "discord",
                "user_id": str(client.user.id)
            },
            "online": client.is_ready()
        }])


async def get_version() -> dict:
    return return_object.get(0, impl="onedisc", version=VERSION, onebot_version="12")


async def delete_message(message_id: str) -> dict:
    for message in client.cached_messages[::-1]:
        if str(message.id) == message_id:
            try:
                await message.delete()
            except discord.Forbidden:
                return return_object.get(34001, "权限错误")
            except discord.NotFound:
                return return_object.get(35002, "消息已被撤回")
            break
    else:
        return return_object.get(35002, "消息不存在")
    return return_object.get(0)
            
async def get_self_info() -> dict:
    return return_object.get(
        0,
        user_id=str(client.user.id),
        user_name=client.user.name,
        user_displayname=""
    )

async def get_user_info(user_id: str) -> dict:
    if not (user := client.get_user(int(user_id))):
        return return_object.get(35003, "用户不存在")
    return return_object.get(
        0,
        user_id=str(user.id),
        user_name=user.name,
        user_displayname=user.display_name,
        user_remark=""
    )


async def get_friend_list() -> dict:
    return return_object._get(0, [])


async def get_group_info(group_id: str) -> dict:
    if not (channel := client.get_channel(int(group_id))):
        return return_object.get(35001, "频道不存在")
    return return_object.get(
        0,
        group_id=str(channel.id),
        group_name=channel.name
    )

async def get_group_list() -> dict:
    channel_list = []
    for channel in client.get_all_channels():
        channel_list.append({
            "group_id": str(channel.id),
            "group_name": channel.name
        })
    return return_object._get(0, channel_list)

async def get_group_member_info(group_id: str, user_id: str) -> dict:
    if not (channel := client.get_channel(int(group_id))):
        return return_object.get(35001, "频道不存在")
    for member in channel.members:
        if str(member.id) == user_id:
            user = member
            break
    else:
        return return_object.get(35003, "未找到用户")
    return return_object.get(
        0, 
        user_id=str(user.id),
        user_name=user.name,
        user_displayname=user.nick
    )

async def get_group_member_list(group_id: str) -> dict:
    if not (channel := client.get_channel(int(group_id))):
        return return_object.get(35001, "频道不存在")
    member_list = []
    for user in channel.members:
        member_list.append({
            "user_id": str(user.id),
            "user_name": user.name,
            "user_displayname": user.nick
        })
    return return_object._get(0, member_list)

async def set_group_name(group_id: str, group_name: str) -> dict:
    return return_object.get(10002, "不支持机器人修改频道名")

async def leave_group(group_id: str) -> dict:
    if not (channel := client.get_channel(int(group_id))):
        return return_object.get(35001, "频道不存在")
    await channel.leave()
    return return_object.get(0)

async def get_guild_info(guild_id: str) -> dict:
    if not (guild := client.get_guild(int(guild_id))):
        return return_object.get(35004, "服务器不存在")
    return return_object.get(
        0,
        guild_id=str(guild.id),
        guild_name=guild.name
    )

async def get_guild_list() -> dict:
    guild_list = []
    for guild in client.guilds:
        guild_list.append({
            "guild_id": str(guild.id),
            "guild_name": guild.name
        })
    return return_object._get(0, guild_list)

async def set_guild_name(guild_id: str, guild_name: str) -> dict:
    return return_object.get(10002, "不支持机器人修改群组名")

async def get_guild_member_info(guild_id: str, user_id: str) -> dict:
    if not (guild := client.get_guild(int(guild_id))):
        return return_object.get(35004, "服务器不存在")
    for member in guild.members:
        if str(member.id) == user_id:
            user = member
            break
    else:
        return return_object.get(35003, "未找到用户")
    return return_object.get(
        0, 
        user_id=str(user.id),
        user_name=user.name,
        user_displayname=user.nick
    )

async def get_guild_member_list(guild_id: str) -> dict:
    if not (guild := client.get_guild(int(guild_id))):
        return return_object.get(35004, "服务器不存在")
    member_list = []
    for user in guild.members:
        member_list.append({
            "user_id": str(user.id),
            "user_name": user.name,
            "user_displayname": user.nick
        })
    return return_object._get(0, member_list)

async def leave_guild(guild_id: str) -> dict:
    if not (guild := client.get_guild(int(guild_id))):
        return return_object.get(35004, "服务器不存在")
    await guild.leave()
    return return_object.get(0)

def _parse_channel_action_data(_data: dict) -> dict:
    data = _data.copy()
    for key, value in list(_data.items()):
        if isinstance(value, list):
            for i in range(len(value)):
                if isinstance(value[i], dict):
                    data[key][i] = _parse_channel_action_data(value[i])
        if "group" in key:
            data[key.replace("group", "channel")] = data.pop(key)
    return data

async def get_channel_list(guild_id: str, joined_only: bool = False) -> dict:
    if not (guild := client.get_guild(int(guild_id))):
        return return_object.get(35004, "服务器不存在")
    channel_list = []
    for channel in guild.channels:
        if joined_only:
            try:
                await guild.fetch_channel(channel.id)
            except discord.Forbidden:
                continue
        channel_list.append({
            "channel_id": str(channel.id),
            "channel_name": channel.name
        })
    return return_object._get(0, channel_list)


async def set_channel_name(guild_id: str, channel_id: str, channel_name: str) -> dict:
    return return_object.get(10002, "不支持机器人修改频道名")

async def get_channel_member_info(guild_id: str, channel_id: str, user_id: str) -> dict:
    return _parse_channel_action_data(await get_group_member_info(channel_id, user_id))

async def get_channel_member_list(guild_id: str, channel_id: str) -> dict:
    return _parse_channel_action_data(await get_group_member_list(channel_id))

async def leave_channel(guild_id: str, channel_id: str) -> dict:
    return _parse_channel_action_data(await leave_group(channel_id))


action_list = {
    "send_message": send_message,
    "get_supported_actions": get_supported_actions,
    "get_status": get_status,
    "get_version": get_version,
    "delete_msg": delete_message,
    "get_self_info": get_self_info,
    "get_user_info": get_user_info,
    "get_friend_list": get_friend_list,
    "get_group_info": get_group_info,
    "get_group_list": get_group_list,
    "get_group_member_info": get_group_member_info,
    "get_group_member_list": get_group_member_list,
    "set_group_name": set_group_name,
    "leave_group": leave_group,
    "get_guild_info": get_guild_info,
    "get_guild_list": get_guild_list,
    "set_guild_name": set_guild_name,
    "get_guild_member_info": get_guild_member_info,
    "get_guild_member_list": get_guild_member_list,
    "leave_guild": leave_guild,
    "get_channel_list": get_channel_list,
    "set_channel_name": set_channel_name,
    "get_channel_member_info": get_channel_member_info,
    "get_channel_member_list": get_channel_member_list,
    "leave_channel": leave_channel
}


def register_extra_action(name: str) -> Callable:
    """
    Register extra action
    """
    def decorator(func: Callable) -> None:
        action_list[name] = func
    return decorator
