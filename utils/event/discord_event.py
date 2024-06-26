from utils.client import client, tree
from utils.config import config
from network import init_connections
import utils.event.heartbeat_event as heartbeat_event
import utils.message.v12.parser as parser
import utils.event as event
import discord
from discord import Object
import asyncio
from ..db import commit_message, init_database
from utils.update_checker import check_update
from actions.v12.basic import get_status
from actions.v11.basic import get_role

from utils.logger import get_logger, print_message_delete_log, print_message_log

logger = get_logger()


@client.event
async def on_ready() -> None:
    logger.info(f"成功登陆到 {client.user}")
    for guild in config["system"].get("sync_guilds", []):
        await tree.sync(guild=Object(id=int(guild)))
    if config["system"].get("sync_globally", False):
        await tree.sync()
    await init_connections(config["servers"])
    asyncio.create_task(
        heartbeat_event.setup_heartbeat_event(config["system"].get("heartbeat", {}))
    )
    logger.info(config["system"].get("started_text", "OneDisc 已成功启动"))
    event.new_event("meta", "status_update", status=(await get_status())["data"])
    if config["system"].get("check_update", True):
        asyncio.create_task(check_update())
    await init_database()


@client.event
async def on_message(message: discord.Message) -> None:
    if (
        (
            message.author == client.user
            and config["system"].get("ignore_self_events", True)
        )
        or message.author.bot
        and config["system"].get("ignore_bot_event")
    ):
        return
    print_message_log(message)
    await commit_message(
        message.id, message.channel.id, int(message.created_at.timestamp())
    )
    if message.guild and config["system"].get("enable_channel_event"):
        event.new_event(
            _type="message",
            detail_type="channel",
            _time=message.created_at.timestamp(),
            message_id=str(message.id),
            message=parser.parse_string(message.content, message),
            alt_message=message.content,
            guild_id=str(message.guild.id),
            channel_id=str(message.channel.id),
            user_id=str(message.author.id),
        )
    elif message.guild:
        event.new_event(
            _type="message",
            detail_type="group",
            _time=message.created_at.timestamp(),
            message_id=str(message.id),
            message=parser.parse_string(message.content, message),
            alt_message=message.content,
            group_id=str(message.channel.id),
            user_id=str(message.author.id),
        )
    else:
        event.new_event(
            _type="message",
            detail_type="private",
            _time=message.created_at.timestamp(),
            message_id=str(message.id),
            message=parser.parse_string(message.content, message),
            alt_message=message.content,
            user_id=str(message.author.id),
        )


@client.event
async def on_message_delete(message: discord.Message) -> None:
    if (
        message.author == client.user
        and config["system"].get("ignore_self_events", True)
    ) or (message.author.bot and config["system"].get("ignore_bot_event")):
        return
    print_message_delete_log(message)
    if message.guild and config["system"].get("enable_channel_event"):
        event.new_event(
            _type="notice",
            detail_type="channel_message_delete",
            sub_type=(
                ""
                if config["system"].get("use_empty_for_unsupported_subtype", True)
                else "recall"
            ),
            message_id=str(message.id),
            user_id=str(message.author.id),
            channel_id=str(message.channel.id),
            guild_id=str(message.guild.id),
            operator_id=str(message.author.id),
        )
    elif message.guild:
        event.new_event(
            _type="notice",
            detail_type="group_message_delete",
            sub_type=(
                ""
                if config["system"].get("use_empty_for_unsupported_subtype", True)
                else "recall"
            ),
            message_id=str(message.id),
            user_id=str(message.author.id),
            group_id=str(message.channel.id),
            operator_id=str(message.author.id),
        )
    else:
        event.new_event(
            _type="notice",
            detail_type="private_message_delete",
            message_id=str(message.id),
            user_id=str(message.author.id),
        )


@client.event
async def on_member_join(member: discord.Member) -> None:
    logger.info(
        f"用户 {member.name} ({member.id}) 加入了服务器 {member.guild.name} ({member.guild.id})"
    )
    if config["system"].get("enable_channel_event"):
        event.new_event(
            _type="notice",
            detail_type="guild_member_increase",
            sub_type="join",
            guild_id=str(member.guild.id),
            user_id=str(member.id),
            operator_id=str(member.id),
        )


@client.event
async def on_member_remove(member: discord.Member) -> None:
    if member.bot and config["system"].get("ignore_bot_event"):
        return
    logger.info(
        f"用户 {member.name} ({member.id}) 离开了服务器 {member.guild.name} ({member.guild.id})"
    )
    if config["system"].get("enable_channel_event"):
        event.new_event(
            _type="notice",
            detail_type="guild_member_decrease",
            sub_type="leave",
            guild_id=str(member.guild.id),
            user_id=str(member.id),
            operator_id=str(member.id),
        )


@client.event
async def on_guild_channel_create(
    channel: discord.TextChannel | discord.VoiceChannel | discord.CategoryChannel,
):
    logger.info(
        f"新的频道 {channel.name} ({channel.id}) 在 {channel.guild.name} ({channel.guild.id}) 上创建"
    )
    if config["system"].get("enable_channel_event"):
        event.new_event(
            _type="notice",
            detail_type="channel_create",
            guild_id=str(channel.guild.id),
            channel_id=str(channel.id),
            operator_id="-1",
        )


@client.event
async def on_guild_channel_delete(
    channel: discord.TextChannel | discord.VoiceChannel | discord.CategoryChannel,
):
    logger.info(
        f"频道 {channel.name} ({channel.id}) 在 {channel.guild.name} ({channel.guild.id}) 上被删除"
    )
    if config["system"].get("enable_channel_event"):
        event.new_event(
            _type="notice",
            detail_type="channel_delete",
            guild_id=str(channel.guild.id),
            channel_id=str(channel.id),
            operator_id="-1",  # 暂时使用 -1，因为不直接知道删除该频道的用户
        )


@client.event
async def on_member_update(before: discord.Member, after: discord.Member) -> None:
    # 这是一个 OneBot V11 事件
    if not config["system"].get("enable_group_admin", True):
        return
    match get_role(before), get_role(after):
        case "member", "admin":
            logger.info(
                f"{after.name} ({after.id}) 被设为服务器 {after.guild.name} ({after.guild.id}) 的管理员"
            )
            sub_type = "set"
        case "admin", "member":
            sub_type = "unset"
        case _:
            return
    if config["system"].get("guild_id_for_group_admin"):
        event.new_event("notice", "group_admin", sub_type, group_id=after.guild.id)
    else:
        for channel in after.guild.channels:
            if (not isinstance(channel, discord.TextChannel)) and config["system"].get(
                "group_admin_text_channel"
            ):
                continue
            event.new_event(
                "notice",
                "group_admin",
                sub_type,
                group_id=channel.id,
                guild_id=after.guild.id,
            )


logger.info("事件响应器注册完成！")
