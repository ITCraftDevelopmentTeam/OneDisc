from config import get_config
from config import config as _config
import message_parser
import file as _file
import event
import asyncio
import heartbeat_event
from logger import get_logger, init_logger
import discord
import aiohttp
import api
import ssl
import certifi
from connection import init_connections

CONFIG = get_config()
VERSION = "0.1.0"

init_logger(CONFIG["system"]["logger"])
logger = get_logger()
logger.info("OneDisc (By This-is-XiaoDeng)")
logger.info(f"当前版本：{VERSION}")

intents = discord.Intents.default()
intents.message_content = True

ssl_context = ssl.create_default_context(cafile=certifi.where())
connector = aiohttp.TCPConnector(ssl=ssl_context)
session = aiohttp.ClientSession(connector=connector)

client = discord.Client(http_session=session, intents=intents, proxy=CONFIG["system"]["proxy"])

_config = CONFIG


@client.event
async def on_ready() -> None:
    logger.info(f"成功登陆到 {client.user}")
    api.init(client, CONFIG)
    event.init(str(client.user.id))
    await init_connections(CONFIG["servers"])
    asyncio.create_task(heartbeat_event.setup_heartbeat_event(CONFIG["system"].get("heartbeat", {})))


def print_message_log(message: discord.Message) -> None:
    try:
        logger.info(f"[服务器：{message.guild.name} ({message.guild.id})] 来自 #{message.channel.name} ({message.channel.id}) 中 {message.author.name} ({message.author.id}) 的消息：{message.content} ({message.id})")
    except AttributeError:
        logger.info(f"来自 {message.author.name}({message.author.id}) 的消息：{message.content}")


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author == client.user and CONFIG["system"].get("ignore_self_message", True):
        return
    print_message_log(message)
    if message.guild and CONFIG["system"].get("enable_channel_event"):
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

client.run(CONFIG["account_token"], log_handler=None)

