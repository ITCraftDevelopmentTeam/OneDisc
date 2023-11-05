from config import config
from client import client
from logger import get_logger, init_logger
from version import VERSION, SUB_VER

init_logger(config["system"].get("logger", {"level": 20}))
logger = get_logger()
logger.info("OneDisc (By: IT Craft Development Team)")
logger.info(f"当前版本：{VERSION}.{SUB_VER}")

# 导入插件
import discord_event
import file
import basic_actions_v12
import basic_api_v11

client.run(config["account_token"], log_handler=None)

