from typing import Callable
import uvicorn_server
import call_action
import json
import fastapi
from logger import get_logger

BASE_CONNECTION_CONFIG = {
    "host": "0.0.0.0",
    "port": 8080,
    "access_token": None,
    "event_enabled": False,
    "event_buffer_size": 0
}
logger = get_logger()


async def create_http_server(_config: dict) -> None:
    """
    创建 HTTP 服务器

    Args:
        config (dict): 连接配置
    """
    config = BASE_CONNECTION_CONFIG.copy()
    config.update(_config)
    app = fastapi.FastAPI()
    app.add_route("/", get_connection_handler(config), ["post"])
    await uvicorn_server.run(app, config["port"], config["host"])

def get_connection_handler(config: dict) -> Callable:
    """
    获取连接相应器

    Args:
        config (dict): 连接配置
    """
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
        return fastapi.responses.JSONResponse(await call_action.on_call_action(**json.loads(await request.body())))

    return handle_http_connection

def verify_access_token(request: fastapi.Request, access_token: str) -> bool:
    """
    鉴权

    Args:
        request (fastapi.Request): 请求信息
        access_token (str): access_token

    Returns:
        bool: 是否通过验证
    """
    if "Authorization" in request.headers.keys():
        return request.headers["Authorization"] == f"Bearer {access_token}"
    return request.query_params.get("access_token") == access_token

