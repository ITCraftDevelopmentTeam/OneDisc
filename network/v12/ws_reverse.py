import json
import utils.event as event
import call_action
import asyncio
import traceback
from utils.config import config as system_config
from utils.logger import get_logger
from version import VERSION

import websockets.client
import websockets.exceptions

BASE_CONFIG = {
    "url": "",
    "access_token": None,
    "reconnect_interval": 5000
}
logger = get_logger()


class WebSocketClient:

    def __init__(self, config: dict) -> None:
        self.config = BASE_CONFIG.copy()
        self.config.update(config)

    async def connect(self) -> None:
        logger.info(f"正在连接到 WebSocket 服务器：{self.config['url']}")
        self.websocket = await websockets.client.connect(
            self.config["url"],
            user_agent_header=f"OneBot/12 (discord) OneDisc/{VERSION}",
            extra_headers=self.get_headers(),
            max_size=system_config["system"].get("max_message_size", 2**20),
        )
        logger.info(f"已连接到 WebSocket 服务器：{self.config['url']}")
        await self.send(event.get_event_object(
            "meta",
            "connect",
            "",
            params={
                "version": dict(impl="onedisc", version=VERSION, onebot_version="12")
            }
        ))

    async def setup_receive_loop(self) -> None:
        while not hasattr(self, "reconnect_task"):
            try:
                await self.receive_loop()
            except Exception:
                logger.warning(f"接收任务异常退出：{traceback.format_exc()}")
                await asyncio.sleep(self.config["reconnect_interval"] / 1000)
                logger.info("正在重启接收任务")

    async def receive_loop(self) -> None:
        recv_data = json.loads(await self.websocket.recv())
        logger.debug(recv_data)
        await self.send(await call_action.on_call_action(**recv_data))

    async def push_event(self, event: dict) -> None:
        if not hasattr(self, "reconnect_task"):
            await self.send(event)

    async def send(self, data: dict) -> None:
        logger.debug(str(data))
        try:
            await self.websocket.send(json.dumps(data))
        except websockets.exceptions.ConnectionClosedError as e:
            logger.warning(f"WebSocket 连接已断开：{e}")
            await self.reconnect()
            await self.send(data)
        except Exception:
            logger.error(f"发送消息时出现错误：{traceback.format_exc()}")

    async def reconnect(self) -> None:
        if hasattr(self, "reconnect_task"):
            await self.reconnect_task
        else:
            self.reconnect_task = asyncio.create_task(self._reconnect())
            await self.reconnect_task
            del self.reconnect_task
            asyncio.create_task(self.setup_receive_loop())


    async def _reconnect(self) -> None:
        while True:
            try:
                await self.connect()
            except Exception as e:
                logger.error(f"连接 WebSocket 时发生错误：{e}")
                await asyncio.sleep(self.config['reconnect_interval'] * 0.001)
                continue
            break
    
    def get_headers(self) -> dict:
        headers = {
            "Sec-WebSocket-Protocol": "12.onedisc"
        }
        if self.config.get("access_token"):
            headers["Authorization"] = f"Bearer {self.config['access_token']}"
        return headers
