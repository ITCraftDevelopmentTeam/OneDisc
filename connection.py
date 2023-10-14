from http_server import HTTPServer
import asyncio
from http_webhook import HttpWebhookConnect
from logger import get_logger
from ws import WebSocketServer
from ws_reverse import WebSocketClient

logger = get_logger()
connections = []


async def init_connections(connection_list: list[dict]) -> None:
    for obc_config in connection_list:
        logger.debug(obc_config)
        match obc_config["type"]:
            case "http":
                connections.append({
                    "type": "http",
                    "config": obc_config,
                    "object": (tmp := HTTPServer(obc_config)),
                    "add_event_func": tmp.push_event
                })
                await tmp.start_server()
                del tmp
            case "http-webhook":
                connections.append({
                    "type": "http-webhook",
                    "config": obc_config,
                    "object": (tmp := HttpWebhookConnect(obc_config)),
                    "add_event_func": tmp.on_event
                })
                del tmp
            case "ws":
                connections.append({
                    "type": "ws",
                    "config": obc_config,
                    "object": (tmp := WebSocketServer(obc_config)),
                    "add_event_func": tmp.push_event
                })
                await tmp.start_server()
                del tmp
            case "ws-reverse":
                connections.append({
                    "type": "ws-reverse",
                    "config": obc_config,
                    "object": (tmp := WebSocketClient(obc_config)),
                    "add_event_func": tmp.push_event
                })
                asyncio.create_task(tmp.reconnect())
                del tmp
