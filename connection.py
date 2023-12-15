from http_server import HTTPServer
import asyncio
from http_webhook import HttpWebhookConnect
from http_server_v11 import HTTPServer4OB11
from http_post_v11 import HTTPPost4OB11
from ws_v11 import WebSocket4OB11
from ws_reverse_v11 import init_websocket_reverse_connection
from logger import get_logger
from ws import WebSocketServer
from ws_reverse import WebSocketClient

logger = get_logger()
connections = []


async def init_connections(connection_list: list[dict]) -> None:
    logger.debug(connection_list)
    for obc_config in connection_list:
        logger.debug(obc_config)

        if "type" not in obc_config:
            logger.error(f"无效的连接配置：{obc_config}")
            continue

        match obc_config["type"], obc_config.get("protocol_version", 12):

            case "http", 12:
                connections.append({
                    "type": "http",
                    "config": obc_config,
                    "object": (tmp := HTTPServer(obc_config)),
                    "add_event_func": tmp.push_event
                })
                await tmp.start_server()
                del tmp
            
            case "http-webhook", 12:
                connections.append({
                    "type": "http-webhook",
                    "config": obc_config,
                    "object": (tmp := HttpWebhookConnect(obc_config)),
                    "add_event_func": tmp.on_event
                })
                del tmp
            
            case "ws", 12:
                connections.append({
                    "type": "ws",
                    "config": obc_config,
                    "object": (tmp := WebSocketServer(obc_config)),
                    "add_event_func": tmp.push_event
                })
                await tmp.start_server()
                del tmp
            
            case "ws-reverse", 12:
                connections.append({
                    "type": "ws-reverse",
                    "config": obc_config,
                    "object": (tmp := WebSocketClient(obc_config)),
                    "add_event_func": tmp.push_event
                })
                asyncio.create_task(tmp.reconnect())
                del tmp
            
            
            case "http", 11:
                connections.append({
                    "type": "http",
                    "config": obc_config,
                    "object": (tmp := HTTPServer4OB11(obc_config)),
                    "add_event_func": tmp.push_event
                })
                await tmp.start_server()
                del tmp
            

            case "http-post", 11:
                connections.append({
                    "type": "http-post",
                    "config": obc_config,
                    "object": (tmp := HTTPPost4OB11(obc_config)),
                    "add_event_func": tmp.push_event
                })
                del tmp
            

            case "ws", 11:
                connections.append({
                    "type": "ws",
                    "config": obc_config,
                    "object": (tmp := WebSocket4OB11(obc_config)),
                    "add_event_func": tmp.push_event
                })
                await tmp.start()
                del tmp
            
            case "ws-reverse", 11:
                connections.append({
                    "type": "ws-reverse",
                    "config": obc_config,
                    "object": None,
                    "add_event_func": init_websocket_reverse_connection(obc_config)
                })

            case _:
                logger.warning(f"无效的连接类型或协议版本，已忽略: {obc_config['type']} (协议版本: {obc_config.get('protocol_version', 12)}")
