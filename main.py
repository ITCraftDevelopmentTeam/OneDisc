from config import get_config
from logger import get_logger, init_logger
import discord
import api
from connection import init_connections
import send_msg

CONFIG = get_config()
VERSION = "0.1.0"

init_logger(CONFIG["system"]["logger"])
logger = get_logger()
logger.info("OneDisc (By This-is-XiaoDeng)")
logger.info(f"当前版本：{VERSION}")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents, proxy=CONFIG["system"]["proxy"])

@client.event
async def on_ready() -> None:
    api.init(client, CONFIG)
    send_msg.init(CONFIG)
    logger.info(f"成功登陆到 {client.user}")
    init_connections(CONFIG["servers"])

client.run(CONFIG["account_token"], log_handler=None)

