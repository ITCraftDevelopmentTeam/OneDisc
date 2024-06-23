from utils.logger import get_logger
import asyncio
import utils.event as event
import actions.v11.quick_operation as quick_operation
import json
from utils.client import client
import httpx
import hmac
import utils.translator as translator

logger = get_logger()
BASE_CONFIG = {"url": None, "timeout": 0, "secret": None}


class HttpPost:

    def __init__(self, config: dict) -> None:
        """
        初始化一个 HTTP Post (OneBot V11) 连接

        Args:
            config (dict): 连接配置
        """
        self.config = BASE_CONFIG | config
        asyncio.create_task(
            self.push_event(event.get_event_object("meta", "lifecycle", "enable"))
        )

    def __del__(self) -> None:
        asyncio.create_task(
            self.push_event(event.get_event_object("meta", "lifecycle", "disable"))
        )

    async def push_event(self, _event: dict) -> None:
        """
        推送事件

        Args:
            event (dict): 事件
        """
        event = await translator.translate_event(_event)
        async with httpx.AsyncClient(timeout=self.config["timeout"]) as client:
            response = await client.post(
                self.config["url"],
                content=(content := json.dumps(event)),
                headers=self.get_headers(content),
            )
        if response.status_code == 204:
            return
        elif response.status_code == 200:
            content = response.json()
            logger.debug(f"收到快速操作请求：{content}")
            await quick_operation.handle_quick_operation(content, event)
        else:
            logger.warning(f"上报事件时发生错误：{response.status_code}")

    def get_headers(self, content: str) -> dict:
        headers = {
            "Content-Type": "application/json",
            "X-Self-ID": client.user.id,  # type: ignore
        }
        if self.config["secret"]:
            headers["X-Signature"] = (
                "sha1="
                + hmac.new(
                    self.config["secret"].encode("utf-8"),
                    content.encode("utf-8"),
                    "sha1",
                ).hexdigest()
            )
        return headers
