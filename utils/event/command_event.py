from datetime import datetime
from typing import Optional
from ..config import config
from utils.logger import get_logger
from discord import Guild, User
from utils.message.v12 import parser
from .. import event

logger = get_logger()


def print_command_log(
        guild: Optional[Guild],
        channel_id: int,
        author: User,
        content: str
) -> None:
    try:
        logger.info(f"[服务器：{guild.name} ({guild.id})] 频道 {channel_id} 中 {author.name} ({author.id}) 使用了指令: {content}")
    except AttributeError:
        logger.info(f"{author.name}({author.id}) 使用了指令: {content}")

async def on_command(
        guild: Optional[Guild],
        created_at: datetime,
        content: str,
        channel_id: int,
        author: User
) -> None:
    print_command_log(guild, channel_id, author, content)
    if guild and config["system"].get("enable_channel_event"):
        event.new_event(
            _type="message",
            detail_type="channel",
            _time=created_at.timestamp(),
            message_id="-1",
            message=parser.parse_string(content),
            alt_message=content,
            guild_id=str(guild.id),
            channel_id=str(channel_id),
            user_id=str(author.id)
        )
    elif guild:
        event.new_event(
            _type="message",
            detail_type="group",
            _time=created_at.timestamp(),
            message_id="-1",
            message=parser.parse_string(content),
            alt_message=content,
            group_id=str(channel_id),
            user_id=str(author.id)
        )
    else:
        event.new_event(
            _type="message",
            detail_type="private",
            _time=created_at.timestamp(),
            message_id="-1",
            message=parser.parse_string(content),
            alt_message=content,
            user_id=str(author.id)
        )
