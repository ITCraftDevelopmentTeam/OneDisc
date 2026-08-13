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
        logger.warning(
            f"调用 Discord API 时出现错误（{self.code}）：\n{json.dumps(self.data, indent=4)}"
        )


async def call(method: str, path: str, data: dict | None = None, **params) -> dict:
    async with httpx.AsyncClient(
        # httpx >= 0.28 已将 proxies 参数改名为 proxy
        proxy=config["system"].get("proxy"),
        base_url="https://discord.com/api/v10",
    ) as client:
        response = await client.request(
            method,
            path,
            # Discord API 需要 JSON 编码（httpx 的 data= 会发表单格式）
            json=data,
            headers={"Authorization": f"Bot {config['account_token']}"},
            **params,
        )
    if response.status_code == 400:
        raise DiscordApiException(response.json())
    elif response.status_code == 204:
        return {"code": 204}
    return response.json()
