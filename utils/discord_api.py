import json
import httpx
from .config import config
from .logger import get_logger

logger = get_logger()

class DiscordApiException(Exception):
    def __init__(self, data: dict) -> None:
        super().__init__(data)
        self.code = data["code"]
        self.message = data["message"]
        self.data = data
        logger.warning(f"调用 Discord API 时出现错误（{self.code}）：\n{json.dumps(self.data, indent=4)}")

async def call(method: str, path: str, data: dict | None = None, **params) -> dict:
    async with httpx.AsyncClient(proxies=config["system"].get("proxy")) as client:
        response = await client.request(
            method,
            f"https://discord.com/api/v10{path}",
            data=data,
            headers={"Authorization": f"Bot {config['account_token']}"},
            **params
        )
    if response.status_code == 400:
        raise DiscordApiException(response.json())
    return response.json()
