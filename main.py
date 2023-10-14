from config import config
from client import client
from logger import get_logger, init_logger
from version import VERSION
import importlib
import traceback

init_logger(config["system"].get("logger", {"level": 20}))
logger = get_logger()
logger.info("OneDisc (By: IT Craft Development Team)")
logger.info(f"当前版本：{VERSION}")

plugins = [
    "discord_event",
    "file",
    "basic_actions_v12"
]
for plugin in plugins:
    try:
        importlib.import_module(plugin)
        logger.debug(f"成功加载插件：{plugin}")
    except Exception:
        logger.error(f"加载插件 {plugin} 失败，部分功能可能无法正常使用：{traceback.format_exc()}")

client.run(config["account_token"], log_handler=None)

