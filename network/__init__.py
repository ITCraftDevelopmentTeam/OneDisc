# from network.v12.http import HTTPServer
# import asyncio
# from network.v12.http_webhook import HttpWebhookConnect
# from network.v11.http import HTTPServer4OB11
# from network.v11.http_post import HTTPPost4OB11
# from network.v11.ws import WebSocket4OB11
# from network.v11.ws_reverse import init_websocket_reverse_connection
# from network.v12.ws import WebSocketServer
# from network.v12.ws_reverse import WebSocketClient

from sqlite3 import connect
from turtle import setup
from typing import Any, Callable, Coroutine, Union
import network.v12.http
import network.v12.http_webhook
import network.v12.ws
import network.v12.ws_reverse
import network.v11.http
import network.v11.http_post
import network.v11.ws
import network.v11.ws_reverse

from logger import get_logger

logger = get_logger()
connections = []

CONNECTION_TYPE = Union[
    network.v12.http.HttpServer,
    network.v12.http_webhook.HttpWebhook,
    network.v12.ws.WebSocketServer,
    network.v12.ws_reverse.WebSocketClient,
    network.v11.http.HttpServer,
    network.v11.http_post.HttpPost,
    network.v11.ws.WebSocket
]
async def start_connection(
        obj: CONNECTION_TYPE,
        setup_method: str | None = "start_server",
        event_handler_method: str = "push_event"
) -> Callable:
    if setup_method is not None:
        await getattr(obj, setup_method)()
    return getattr(obj, event_handler_method)

SUPPORTED_CONNECT_TYPES: dict[int, dict[str, Callable[[dict], Coroutine]]] = {
    12: {
        "http": lambda config: start_connection(
            network.v12.http.HttpServer(config),
            "start_server"
        ),
        "http-webhook": lambda config: start_connection(
            network.v12.http_webhook.HttpWebhook(config),
            None,
            "on_event"
        ),
        "ws": lambda config: start_connection(
            network.v12.ws.WebSocketServer(config),
            "start_server"
        ),
        "ws-reverse": lambda config: start_connection(
            network.v12.ws_reverse.WebSocketClient(config),
            "connect"
        )
    },
    11: {
        "http": lambda config: start_connection(
            network.v11.http.HttpServer(config),
            "start_server"
        ),
        "http-post": lambda config: start_connection(
            network.v11.http_post.HttpPost(config),
            None
        ),
        "ws": lambda config: start_connection(
            network.v11.ws.WebSocket(config),
            "start"
        ),
        "ws-reverse": network.v11.ws_reverse.init_websocket_reverse_connection
    }
}

async def get_connection_data(connection_config: dict) -> dict:
    setup_function = SUPPORTED_CONNECT_TYPES[
        connection_config.get("protocol_version", 12)
    ][connection_config["type"]](connection_config)
    return {
        "type": connection_config["type"],
        "config": connection_config,
        "add_event_func": await setup_function
    }

async def init_connections(connection_list: list[dict]) -> None:
    logger.debug(connection_list)
    for connection_config in connection_list:
        logger.debug(connection_config)

        if "type" not in connection_config:
            logger.error(f"无效的连接配置：{connection_config}")
            continue

        try:
            connection_data = await get_connection_data(connection_config)
        except KeyError as e:
            logger.warning(f"使用配置 {connection_config} 创建连接时出现错误: 无效的连接类型或协议版本: {e}")
        else:
            connections.append(connection_data)
