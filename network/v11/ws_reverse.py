from typing import Callable, Literal
from utils.config import config as system_config
from utils.client import client
import utils.translator as translator
import websockets
import json
import json
import call_action
import asyncio
import traceback
import websockets.client
import websockets.exceptions
from utils.logger import get_logger

# from version import VERSION

BASE_CONFIG = {
    "url": None,
    "api_url": None,
    "event_url": None,
    "reconnect_interval": 3000,
    "use_universal_client": False,
    "access_token": None,
}
logger = get_logger()


class WebSocketClient:

    def __init__(self, config: dict) -> None:
        self.config = BASE_CONFIG | config
        if not self.config["use_universal_client"]:
            self.config["api_url"] = self.config["api_url"] or self.config["url"]
            self.config["event_url"] = self.config["event_url"] or self.config["url"]
        # 重连必须串行：并发的 reconnect() 若各自建立连接，会让下游服务器同时保留多条连接。
        self.reconnect_lock = asyncio.Lock()

        self.role: Literal["API", "Universal", "Event"]
        self.ws: websockets.client.WebSocketClientProtocol | None = None

    def is_ready(self) -> bool:
        return self.ws is not None and self.ws.open

    def get_url(self) -> str:
        return (
            self.config["url"]
            if self.config["use_universal_client"]
            else self.config[f"{self.role.lower()}_url"]
        )

    def get_headers(self) -> dict:
        return {"X-Self-ID": client.user.id, "X-Client-Role": self.role} | (
            {"Authorization": f'Bearer {self.config["access_token"]}'}
            if self.config["access_token"]
            else {}
        )

    async def create_connection(self) -> None:
        self.ws = await websockets.client.connect(
            self.get_url(),
            max_size=system_config["system"].get("max_message_size", 2**20),
            extra_headers=self.get_headers(),
        )

    async def connect(self) -> None:
        while True:
            try:
                logger.info(
                    f"正在尝试连接反向 WebSocket {self.role} 服务器: {self.get_url()}"
                )
                await self.create_connection()
                break
            except Exception:
                logger.warning(
                    f"连接到反向 WebSocket {self.role} 时出现错误: {traceback.format_exc()}"
                )
                await asyncio.sleep(self.config["reconnect_interval"] / 1000)
        logger.info(f"成功连接到反向 WebSocket {self.role} 服务器: {self.get_url()}")

    async def reconnect(self) -> None:
        # 同一时间只允许一个重连流程，避免多个任务各自建立连接（重复连接）。
        async with self.reconnect_lock:
            # 等锁期间可能已经有别的任务重连成功，直接复用。
            if self.is_ready():
                return

            # 先关闭旧连接，避免下游服务器保留旧连接拒绝新连接。
            # 旧连接关闭后 self.ws 才会被 connect() 重新赋值。
            old_ws = self.ws
            self.ws = None
            if old_ws is not None:
                try:
                    await old_ws.close()
                except Exception:
                    pass  # 忽略关闭时的错误

            await self.connect()

    async def send(self, data: dict) -> None:
        try:
            await self.ws.send(json.dumps(data))
        except websockets.exceptions.ConnectionClosedError:
            logger.warning(
                f"从反向 WebSocket {self.role} 断开连接: {traceback.format_exc()}"
            )
            await self.reconnect()
            await self.send(data)


class APIClient(WebSocketClient):

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.role = "API"

    async def handle_api_requests(self) -> None:
        while True:
            await self.receive_api_request()

    async def receive_api_request(self) -> None:
        try:
            await self.send(
                translator.translate_action_response(
                    await call_action.on_call_action(
                        **(await self.get_api_request()), protocol_version=11
                    )
                )
            )
        except websockets.exceptions.ConnectionClosedError:
            logger.warning(f"从 {self.get_url()} 断开连接: {traceback.format_exc()}")
            await self.reconnect()

    async def get_api_request(self) -> dict:
        try:
            return json.loads(await self.ws.recv())
        except websockets.exceptions.ConnectionClosed:
            logger.warning(
                f"从反向 WebSocket {self.role} 断开连接: {traceback.format_exc()}"
            )
            await self.reconnect()
            return await self.get_api_request()
        except AttributeError:
            await self.reconnect()
            return await self.get_api_request()


class EventClient(WebSocketClient):

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.role = "Event"

    async def push_event(self, event: dict) -> None:
        if not self.is_ready():
            await self.reconnect()
        try:
            await self.ws.send(json.dumps(await translator.translate_event(event)))
        except websockets.exceptions.ConnectionClosedError:
            logger.warning(
                f"从反向 WebSocket {self.role} 断开连接: {traceback.format_exc()}"
            )
            await self.reconnect()
            # 重连后重试发送
            try:
                await self.ws.send(json.dumps(await translator.translate_event(event)))
            except Exception:
                logger.error(
                    f"重连后发送事件失败: {traceback.format_exc()}"
                )


class UniversalClient(APIClient, EventClient):

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.role = "Universal"


async def init_websocket_reverse_connection(config: dict) -> Callable:
    config = BASE_CONFIG | config
    if config["use_universal_client"]:
        client = UniversalClient(config)
        asyncio.create_task(client.reconnect())
        asyncio.create_task(client.handle_api_requests())
        return client.push_event
    else:
        api_client = APIClient(config)
        asyncio.create_task(api_client.reconnect())
        asyncio.create_task(api_client.handle_api_requests())
        event_client = EventClient(config)
        asyncio.create_task(event_client.reconnect())
        return event_client.push_event
