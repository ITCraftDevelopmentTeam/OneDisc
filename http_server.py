from typing import Callable
import uvicorn_server
import call_action
import json
import fastapi
import return_object
from logger import get_logger

BASE_CONNECTION_CONFIG = {
    "host": "0.0.0.0",
    "port": 8080,
    "access_token": None,
    "event_enabled": False,
    "event_buffer_size": 0
}
logger = get_logger()


async def create_http_server(_config: dict) -> Callable:
    """
    创建 HTTP 服务器

    Args:
        config (dict): 连接配置
    """
    config = BASE_CONNECTION_CONFIG.copy()
    config.update(_config)
    app = fastapi.FastAPI()
    app.add_route("/", (tmp := get_connection_handler(config))[0], ["post"])
    await uvicorn_server.run(app, config["port"], config["host"])
    return tmp[1]

def get_connection_handler(config: dict) -> tuple[Callable, Callable]:
    """
    初始化连接触发器

    Args:
        config (dict): 服务器配置

    Raises:
        fastapi.HTTPException: 鉴权错误

    Returns:
        tuple[Callable, Callable]: 第一项为`fastapi`的`route`，第二项为`add_event_func`
    """
    event_list = []
    
    async def on_call_action(body: bytes) -> dict:
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            return return_object.get(10001, str(e))
        if data["action"] == "get_latest_events":
            obj =  {
                "status": "ok",
                "retcode": 0,
                "data": event_list[-data["params"].get("limit", len(event_list)):],
                "message": "",
            }
            if data.get("echo"):
                obj["echo"] = data["echo"]
            return obj
        else:
            return await call_action.on_call_action(**data)

    async def handle_http_connection(request: fastapi.Request) -> fastapi.responses.JSONResponse:
        """
        处理 HTTP 请求

        Args:
            request (fastapi.Request): 请求信息

        Returns:
            dict: 返回值
        """
        logger.debug(request)
        if config["access_token"] and not verify_access_token(request, config["access_token"]):
            raise fastapi.HTTPException(fastapi.status.HTTP_401_UNAUTHORIZED)
        logger.debug(await request.body())
        return fastapi.responses.JSONResponse(await on_call_action(await request.body()))
    
    async def add_event(data: dict) -> None:
        nonlocal event_list
        if config["event_enabled"]:
            event_list.append(data)
            event_list = event_list[-config["event_buffer_size"]:]

    return handle_http_connection, add_event

def verify_access_token(request: fastapi.Request | fastapi.WebSocket, access_token: str) -> bool:
    """
    鉴权

    Args:
        request (fastapi.Request | fastapi.WebSocket): 请求信息
        access_token (str): access_token

    Returns:
        bool: 是否通过验证
    """
    if "Authorization" in request.headers.keys():
        return request.headers["Authorization"] == f"Bearer {access_token}"
    return request.query_params.get("access_token") == access_token

