from config import config
import message_parser
import file as _file
import event
import asyncio
import heartbeat_event
from logger import get_logger, init_logger, print_message_delete_log, print_message_log
import discord
import discord.http
import message_parser
import api
from connection import init_connections
from version import VERSION

init_logger(config["system"].get("logger", {"level": 20}))
logger = get_logger()
logger.info("OneDisc (By: IT Craft Development Team)")
logger.info(f"当前版本：{VERSION}")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
discord.http.disable_ssl = config["system"].get("disable_ssl", False)

client = discord.Client(intents=intents, proxy=config["system"]["proxy"])

@client.event
async def on_ready() -> None:
    logger.info(f"成功登陆到 {client.user}")
    message_parser.init(client)
    api.init(client)
    event.init(str(client.user.id))     # type: ignore
    await init_connections(config["servers"])
    asyncio.create_task(heartbeat_event.setup_heartbeat_event(config["system"].get("heartbeat", {})))
    logger.info(config["system"].get("started_text", "OneDisc 已成功启动"))


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author == client.user and config["system"].get("ignore_self_events", True):
        return
    print_message_log(message)
    if message.guild and config["system"].get("enable_channel_event"):
        event.new_event(
            _type="message",
            detail_type="channel",
            _time=message.created_at.timestamp(),
            message_id=str(message.id),
            message=message_parser.parse_string(message.content),
            alt_message="",
            guild_id=str(message.guild.id),
            channel_id=str(message.channel.id),
            user_id=message.author.id
        )
    elif message.guild:
        event.new_event(
            _type="message",
            detail_type="group",
            _time=message.created_at.timestamp(),
            message_id=str(message.id),
            message=message_parser.parse_string(message.content),
            alt_message="",
            group_id=str(message.channel.id),
            user_id=message.author.id
        )
    else:
        event.new_event(
            _type="message",
            detail_type="private",
            _time=message.created_at.timestamp(),
            message_id=str(message.id),
            message=message_parser.parse_string(message.content),
            alt_message="",
            user_id=message.author.id
        )

@client.event
async def on_message_delete(message: discord.Message) -> None:
    if message.author == client.user and config["system"].get("ignore_self_events", True):
        return
    print_message_delete_log(message)
    if message.guild and config["system"].get("enable_channel_event"):
        event.new_event(
            _type="notice",
            detail_type="channel_message_delete",
            sub_type="" if config["system"].get("use_empty_for_unsupported_subtype", True) else "recall",
            message_id=str(message.id),
            user_id=str(message.author.id),
            channel_id=str(message.channel.id),
            guild_id=str(message.guild.id),
            operator_id=str(message.author.id)
        )
    elif message.guild:
        event.new_event(
            _type="notice",
            detail_type="group_message_delete",
            sub_type="" if config["system"].get("use_empty_for_unsupported_subtype", True) else "recall",
            message_id=str(message.id),
            user_id=str(message.author.id),
            group_id=str(message.channel.id),
            operator_id=str(message.author.id)
        )
    else:
        event.new_event(
            _type="notice",
            detail_type="private_message_delete",
            message_id=str(message.id),
            user_id=str(message.author.id)
        )

@client.event
async def on_member_join(member: discord.Member) -> None:
    logger.info(f"用户 {member.name} ({member.id}) 加入了服务器 {member.guild.name} ({member.guild.id})")
    if config["system"].get("enable_channel_event"):
        event.new_event(
            _type="notice",
            detail_type="guild_member_increase",
            sub_type="join",
            guild_id=str(member.guild.id),
            user_id=str(member.id),
            operator_id=str(member.id)
        )

@client.event
async def on_member_remove(member: discord.Member) -> None:
    logger.info(f"用户 {member.name} ({member.id}) 离开了服务器 {member.guild.name} ({member.guild.id})")
    if config["system"].get("enable_channel_event"):
        event.new_event(
            _type="notice",
            detail_type="guild_member_decrease",
            sub_type="leave",
            guild_id=str(member.guild.id),
            user_id=str(member.id),
            operator_id=str(member.id)
        )

@client.event
async def on_guild_channel_create(channel: discord.TextChannel | discord.VoiceChannel | discord.CategoryChannel):
    logger.info(f"新的频道 {channel.name} ({channel.id}) 在 {channel.guild.name} ({channel.guild.id}) 上创建")
    if config["system"].get("enable_channel_event"):
        event.new_event(
            _type="notice",
            detail_type="channel_create",
            guild_id=str(channel.guild.id),
            channel_id=str(channel.id),
            operator_id="-1"
        )


@client.event
async def on_guild_channel_delete(channel: discord.TextChannel | discord.VoiceChannel | discord.CategoryChannel):
    logger.info(f"频道 {channel.name} ({channel.id}) 在 {channel.guild.name} ({channel.guild.id}) 上被删除")
    if config["system"].get("enable_channel_event"):
        event.new_event(
            _type="notice",
            detail_type="channel_delete",
            guild_id=str(channel.guild.id),
            channel_id=str(channel.id),
            operator_id="-1"  # 暂时使用 -1，因为不直接知道删除该频道的用户
        )


client.run(config["account_token"], log_handler=None)

