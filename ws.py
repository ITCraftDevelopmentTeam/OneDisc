import fastapi
import call_action
import json
import uvicorn_server
from logger import get_logger
from http_server import verify_access_token

logger = get_logger()
BASE_CONFIG = {
    "host": "0.0.0.0",
    "port": 5700,
    "access_token": None
}


class WebSocketServer:

    def __init__(self, config: dict) -> None:
        """
        Init a WebSocket server

        Args:
            config (dict): Server config
        """
        self.config = BASE_CONFIG.copy()
        self.config.update(config)
        self.app = fastapi.FastAPI()
        self.app.add_websocket_route("/", self.handle_ws_connect)
        
    async def start_server(self) -> None:
        await uvicorn_server.run(self.app, self.config["port"], self.config["host"])

    async def handle_ws_connect(self, websocket: fastapi.WebSocket) -> None:
        if self.config["access_token"] and not verify_access_token(websocket, self.config["access_token"]):
            raise fastapi.HTTPException(fastapi.status.HTTP_401_UNAUTHORIZED)
        await websocket.accept()
        self.websocket = websocket
        while True:
            recv_data = await websocket.receive_json()
            logger.debug(recv_data)
            await self.websocket.send_json(call_action.on_call_action(**recv_data))

    async def push_event(self, event: dict) -> None:
        await self.websocket.send_json(event)
        