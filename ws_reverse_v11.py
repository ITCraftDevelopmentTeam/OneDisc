from client import client
import translator
import websockets
import json
import json
import event
import call_action
import asyncio
import traceback
import websockets.client
import websockets.exceptions
from logger import get_logger
from version import VERSION

BASE_CONFIG = {
    "url": None,
    "api_url": None,
    "event_url": None,
    "reconnect_interval": 3000,
    "use_universal_client": False,
    "access_token": None
}
logger = get_logger()


class WebSocketClient4OB11:

    def __init__(self, config: dict) -> None:
        self.config = BASE_CONFIG | config
        if not self.config["use_universal_client"]:
            self.config["api_url"] = self.config["api_url"] or self.config["url"]
            self.config["event_url"] = self.config["event_url"] or self.config["url"]
        self.reconnect_task = asyncio.create_task(self.connect())

    async def connect(self) -> None:
        if self.config["use_universal_client"]:
            self.api_ws = self.event_ws = await self.create_websocker_connection(
                self.config["url"], "Universal"
            )
        else:
            self.api_ws = await self.create_websocker_connection(
                self.config["api_url"], "API"
            )
            self.event_ws = await self.create_websocker_connection(
                self.config["event_url"], "Event"
            )
        try:
            del self.reconnect_task
        except Exception:
            pass
        await self.event_ws.send(json.dumps(
            translator.translate_event(event.get_event_object(
                "meta",
                "lifecycle",
                "connect"
        ))))
        asyncio.create_task(self.handle_api_requests())

    async def reconnect(self) -> None:
        if hasattr(self, "reconnect_task"):
            await self.reconnect_task
            return
        await self.close()
        self.reconnect_task = asyncio.create_task(self.connect())

    async def close(self) -> None:
        try:
            await self.api_ws.close()
        except Exception:
            pass
        try:
            await self.event_ws.close()
        except Exception:
            pass

    async def create_websocker_connection(self, url: str, role: str) -> websockets.client.WebSocketClientProtocol:
        while True:
            try:
                logger.info(f"正在连接到反向 WebSocket {role} 服务器：{url}")
                return await websockets.client.connect(
                    url, extra_headers=self.get_headers(role)
                )
            except Exception as e:
                logger.warning(f"连接到反向 WebSocket {role} 时出现错误：{e}")
                await asyncio.sleep(self.config["reconnect_interval"] / 1000)

    async def push_event(self, event: dict) -> None:
        try:
            await self.event_ws.send(
                json.dumps(
                    translator.translate_event(
                        event
                    )
                )
            )
        except Exception:
            if not hasattr(self, "event_ws"):
                logger.warning(f"推送事件时出现错误：{traceback.format_exc()}")
            await self.reconnect()
            await self.push_event(event)

    async def handle_api_requests(self) -> None:
        while True:
            try:
                recv_data = json.loads(await self.api_ws.recv())
                resp_data = await call_action.on_call_action(
                    **recv_data,
                    protocol_version=11
                )
                resp_data["retcode"] = {
                    10001: 1400,
                    10002: 1404
                }.get(resp_data["retcode"], resp_data["retcode"])
                await self.api_ws.send(json.dumps(resp_data))
            except Exception:
                logger.warning(f"处理 API 请求时出现错误：{traceback.format_exc()}")
                break
        await self.reconnect()


    def get_headers(self, role: str) -> dict:
        return {
            "X-Self-ID": client.user.id,
            "X-Client-Role": role
        } | ({"Authorization": f'Bearer {self.config["access_token"]}'} if self.config["access_token"] else {})