import event_12_to_11
import event
from http_server import verify_access_token
from logger import get_logger
import uvicorn_server
import fastapi
import call_action

logger = get_logger()
BASE_CONFIG = {
    "host": "0.0.0.0",
    "port": 6700,
    "access_token": None
}

class WebSocket4OB11:

    def __init__(self, config: dict) -> None:
        self.config = BASE_CONFIG | config
        self.clients_on_event_route = []
        self.app = fastapi.FastAPI()
        self.app.add_websocket_route("/", self.handle_root_route)
        self.app.add_websocket_route("/event", self.handle_event_route)
        self.app.add_websocket_route("/api", self.handle_api_route)

    async def start(self) -> None:
        await uvicorn_server.run(
            self.app, 
            host=self.config["host"], 
            port=self.config["port"]
        )
        
    
    async def handle_event_route(self, websocket: fastapi.WebSocket) -> None:
        if not verify_access_token(websocket, self.config["access_token"]):
            if "Authorization" in websocket.headers.keys() or websocket.query_params.get("access_token"):
                await websocket.close(403, "Invalid access token")
            else:
                await websocket.close(401, "Missing access token")
            return
        await websocket.accept()
        self.clients_on_event_route.append(websocket)
        await websocket.send_json(event_12_to_11.translate_event(event.get_event_object(
            "meta",
            "lifecycle",
            "connect"
        )))

    async def handle_api_route(self, websocket: fastapi.WebSocket) -> None:
        if not verify_access_token(websocket, self.config["access_token"]):
            if "Authorization" in websocket.headers.keys() or websocket.query_params.get("access_token"):
                await websocket.close(403, "Invalid access token")
            else:
                await websocket.close(401, "Missing access token")
            return
        await websocket.accept()
        while True:
            resp_data = await call_action.on_call_action(
                **(await websocket.receive_json()),
                protocol_version=11
            )
            resp_data["retcode"] = {
                10001: 1400,
                10002: 1404
            }.get(resp_data["retcode"], resp_data["retcode"])
            await websocket.send_json(resp_data)

    async def handle_root_route(self, websocket: fastapi.WebSocket) -> None:
        if not verify_access_token(websocket, self.config["access_token"]):
            if "Authorization" in websocket.headers.keys() or websocket.query_params.get("access_token"):
                await websocket.close(403, "Invalid access token")
            else:
                await websocket.close(401, "Missing access token")
            return
        await websocket.accept()
        self.clients_on_event_route.append(websocket)
        while True:
            resp_data = await call_action.on_call_action(
                **(await websocket.receive_json()),
                protocol_version=12
            )
            resp_data["retcode"] = {
                10001: 1400,
                10002: 1404
            }.get(resp_data["retcode"], resp_data["retcode"])
            await websocket.send_json(resp_data)

    async def push_event(self, _event: dict) -> None:
        event = event_12_to_11.translate_event(_event)
        for client in self.clients_on_event_route:
            try:
                await client.send_json(event)
            except Exception as e:
                logger.error(f"向 {client} 推送事件时出现错误：{e}")
                await client.close()
                self.clients_on_event_route.remove(client)
