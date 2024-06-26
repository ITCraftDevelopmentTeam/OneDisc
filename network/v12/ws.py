import fastapi
import call_action
import utils.event as event
from version import VERSION
import utils.uvicorn_server as uvicorn_server
from utils.logger import get_logger
from network.authentication import verify_access_token

logger = get_logger()
BASE_CONFIG = {"host": "0.0.0.0", "port": 5700, "access_token": None}


class WebSocketServer:

    def __init__(self, config: dict) -> None:
        """
        Init a WebSocket server

        Args:
            config (dict): Server config
        """
        self.config = BASE_CONFIG.copy()
        self.config.update(config)
        self.clients: list[fastapi.WebSocket] = []
        self.app = fastapi.FastAPI()
        self.app.add_websocket_route("/", self.handle_ws_connect)
        self.check_access_token()

    def check_access_token(self) -> None:
        if self.config["host"] == "0.0.0.0" or self.config["access_token"]:
            logger.warning(
                f'[{self.config["host"]}:{self.config["port"]}] 未配置 Access Token !'
            )

    async def start_server(self) -> None:
        await uvicorn_server.run(self.app, self.config["port"], self.config["host"])

    async def handle_ws_connect(self, websocket: fastapi.WebSocket) -> None:
        if self.config["access_token"] and not verify_access_token(
            websocket, self.config["access_token"]
        ):
            await websocket.close(fastapi.status.HTTP_401_UNAUTHORIZED)
            return
        await websocket.accept()
        self.clients.append(websocket)
        await websocket.send(
            event.get_event_object(
                "meta",
                "connect",
                "",
                params={
                    "version": dict(
                        impl="onedisc", version=VERSION, onebot_version="12"
                    )
                },
            )
        )
        while True:
            recv_data = await websocket.receive_json()
            logger.debug(recv_data)
            await websocket.send_json(call_action.on_call_action(**recv_data))

    async def push_event(self, event: dict) -> None:
        for websocket in self.clients:
            try:
                await websocket.send_json(event)
            except Exception as e:
                logger.error(f"在 {websocket} 推送事件失败：{e}")
                await websocket.close()
                self.clients.remove(websocket)
