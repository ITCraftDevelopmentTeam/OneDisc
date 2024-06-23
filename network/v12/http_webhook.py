import httpx
import call_action
import json
from utils.logger import get_logger
from version import VERSION

BASE_CONFIG = {"url": None, "access_token": None, "timeout": 0}
logger = get_logger()


class HttpWebhook:

    def __init__(self, config: dict) -> None:
        """
        新建 HTTP Webhook 连接

        Args:
            config (dict): 连接配置
        """
        self.config = BASE_CONFIG.copy()
        self.config.update(config)

    async def push_event(self, event: dict) -> None:
        logger.debug(f"正在向 {self.config['url']} 推送事件")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config["url"],
                content=json.dumps(event),
                headers=self.get_headers(),
                timeout=self.config.get("timeout") or httpx.USE_CLIENT_DEFAULT,
            )
        await self.handle_content(response)

    async def handle_content(self, response: httpx.Response) -> None:
        if response.status_code == 200:
            if (
                response.headers.get("Content-Type", "application/json")
                == "application/json"
            ):
                content = json.loads(await response.aread())
                for item in content:
                    await self.execute_content(item)
            else:
                logger.warning(
                    f'不支持的 Content-Type: {response.headers.get("Content-Type", "application/json")}'
                )
        elif response.status_code == 204:
            return
        logger.error(
            f"向 {self.config['url']} 推送事件时发生错误：不正确的状态码：{response.status_code}"
        )

    async def execute_content(self, content_item: dict) -> None:
        try:
            await call_action.on_call_action(**content_item)
        except Exception as e:
            logger.error(f"调用 {content_item['action']} 时出现错误：{e}")

    async def on_event(self, event: dict) -> None:
        try:
            await self.push_event(event)
        except Exception as e:
            logger.warning(f"向 {self.config['url']} 推送事件时发生错误：{e}")

    def get_headers(self) -> dict[str, str]:
        """
        获取请求头

        Returns:
            dict[str, str]: 请求头
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"OneBot/12 (discord) OneDisc/{VERSION}",
            "X-OneBot-Version": "12",
            "X-Impl": "onedisc",
        }
        if self.config.get("access_token"):
            headers["Authorization"] = f"Bearer {self.config['access_token']}"
        return headers
