#!python3

from utils.config import config
from utils.client import client
from utils.logger import get_logger, init_logger
from version import VERSION, SUB_VER

init_logger(config["system"].get("logger", {"level": 20}))
logger = get_logger()
logger.info("OneDisc (By: IT Craft Development Team)")
logger.info(f"当前版本：{VERSION}.{SUB_VER}")

# 导入插件
import utils.event.discord_event as discord_event
import actions.v12.file as file
import actions.v12.basic as basic
import actions.v11.basic as basic

client.run(config["account_token"], log_handler=None)

