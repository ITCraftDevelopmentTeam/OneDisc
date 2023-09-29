import asyncio
import sys
from typing import List
import fastapi
import uvicorn


class Server(uvicorn.Server):

    async def run(self, sockets: List | None = None) -> None:
        asyncio.create_task(self.serve(sockets))

    async def serve(self, sockets: List | None = None) -> None:
        await super().serve(sockets)
        sys.exit()

async def run(app: fastapi.FastAPI, port: int, host: str = "0.0.0.0", **params):
    """
    在现有事件循环启动 Uvicorn 服务器

    Args:
        app (fastapi.FastAPI): APP
        port (int): 端口
        host (str, optional): Host. Defaults to "0.0.0.0".
    """
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_config=None,
        **params
    )
    server = Server(config)
    await server.run()