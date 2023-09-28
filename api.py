import discord
import return_object
import time
import message_parser
from logger import get_logger
import send_msg

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
    parsed_message = message_parser.parse(message)
    message_id = await send_msg.send_message(parsed_message["text"], _channel_id)

    return return_object.get(0, message_id=message_id, time=time.time())

api_list = {
    "send_message": send_message
}