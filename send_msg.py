import httpx
import json
from logger import get_logger

TOKEN: str
logger = get_logger()


def init(_config: dict) -> None:
    """
    初始化发送消息接口

    Args:
        config (dict): 全局配置
    """
    global TOKEN
    TOKEN = _config["account_token"]

async def send_message(content,channel):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=f"https://discord.com/api/channels/{channel}/messages",
            headers={
                "Authorization": f"Bot {TOKEN}",
                "User-Agent": "DiscordBot"
            },
            data={
                "content": content
            }
        )
        logger.debug(recv := response.read())
        return json.loads(recv)["id"]