import json
import logging
import httpx
import discord
import inspect

BASIC_CONFIG = {
    "level": 20,
    "datefmt": "%Y-%m-%d %H:%M:%S",
    "format": "[%(asctime)s][%(name)s / %(levelname)s]: %(message)s"
}


def init_logger(logger_config: dict) -> None:
    """
    初始化 Logging 配置

    Args:
        logger_config (dict): 配置（`config.json->system.logger`）
    """
    config = BASIC_CONFIG.copy()
    config.update(logger_config)
    logging.basicConfig(**config)

def get_logger(name: str | None = None) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name (str | None, optional): 名称，为`None`则为模块 `__name__`. Defaults to None.

    Returns:
        logging.Logger: 日志记录器
    """
    return logging.getLogger(name or inspect.getmodule(inspect.stack()[1][0]).__name__)

logger = get_logger()

def print_message_log(message: discord.Message) -> None:
    try:
        logger.info(f"[服务器：{message.guild.name} ({message.guild.id})] 来自 #{message.channel.name} ({message.channel.id}) 中 {message.author.name} ({message.author.id}) 的消息：{message.content} ({message.id})")
    except AttributeError:
        logger.info(f"来自 {message.author.name}({message.author.id}) 的消息：{message.content}")

def print_message_delete_log(message: discord.Message) -> None:
    try:
        logger.info(f"[服务器：{message.guild.name} ({message.guild.id})] #{message.channel.name} ({message.channel.id}) 中 {message.author.name} ({message.author.id}) 的消息 {message.id} 被撤回")
    except AttributeError:
        logger.info(f"{message.author.name}({message.author.id}) 撤回了消息：{message.content}")

# def discord_api_failed(response: httpx.Response) -> dict:
#     body = json.loads(response.read())
#     logger.warning(f"调用 Discord API 时出现错误（{body['code']}）：\n{json.dumps(body, indent=4)}")
#     return {
#         "status": "failed",
#         "retcode": 34002,
#         "data": None,
#         "message": body["message"]
#     }
