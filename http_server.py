import asyncio
import uvicorn_server
import call_action
import json
import fastapi
import return_object
from logger import get_logger

BASE_CONFIG = {
    "host": "0.0.0.0",
    "port": 8080,
    "access_token": None,
    "event_enabled": False,
    "event_buffer_size": 0
}
logger = get_logger()

'''
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
'''

class HTTPServer:

    def __init__(self, config: dict) -> None:
        """
        初始化 HTTP 服务器

        Args:
            config (dict): 连接配置
        """
        self.config = BASE_CONFIG.copy()
        self.config.update(config)
        self.event_list = []

        if self.config["event_enabled"] and self.config["event_buffer_size"] <= 0:
            logger.warning("警告: 事件缓冲区大小配置不正确，可能导致内存泄露！")

        self.app = fastapi.FastAPI()
        self.app.add_route("/", self.handle_http_connection, ["post"])        

    async def start_server(self):
        await uvicorn_server.run(self.app, self.config["port"], self.config["host"])

    async def handle_http_connection(self, request: fastapi.Request) -> fastapi.responses.JSONResponse:
        """
        处理 HTTP 请求

        Args:
            request (fastapi.Request): 请求信息

        Returns:
            dict: 返回值
        """
        logger.debug(request)
        if verify_access_token(request, self.config["access_token"]):
            raise fastapi.HTTPException(fastapi.status.HTTP_401_UNAUTHORIZED)
        logger.debug(await request.body())
        return fastapi.responses.JSONResponse(await self.on_call_action(await request.body()))
    
    async def on_call_action(self, body: bytes) -> dict:
        """
        处理动作请求

        Args:
            body (bytes): 请求载荷

        Returns:
            dict: 返回内容
        """
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            return return_object.get(10001, str(e))
        if "action" not in data.keys():
            return return_object.get(10001, "action 字段不存在")
        if data["action"] == "get_latest_events":
            return await self.get_latest_events(**data["params"])
        return await call_action.on_call_action(**data)
    
    async def get_latest_events(self, limit: int = 0, timeout: int = 0, **_) -> dict:
        """
        获取最新事件

        Args:
            limit (int, optional): 最多获取条数，为 0 无限制. Defaults to 0.
            timeout (int, optional): 没有新事件时最多的等待时间，为 0 不等待. Defaults to 0.

        Returns:
            dict: 返回数据
        """
        retried = 0
        while not (events := self.event_list[-limit:]):
            await asyncio.sleep(1)
            retried += 1
            if retried >= timeout:
                break
        return return_object._get(0, events)

    async def push_event(self, event: dict) -> None:
        if self.config["event_enabled"]:
            self.event_list.append(event)
            self.event_list = self.event_list[-self.config["event_buffer_size"]:]




def verify_access_token(request: fastapi.Request | fastapi.WebSocket, access_token: str | None) -> bool:
    """
    鉴权

    Args:
        request (fastapi.Request | fastapi.WebSocket): 请求信息
        access_token (str): access_token

    Returns:
        bool: 是否通过验证
    """
    if access_token is None:
        return True
    if "Authorization" in request.headers.keys():
        return request.headers["Authorization"] == f"Bearer {access_token}"
    return request.query_params.get("access_token") == access_token

