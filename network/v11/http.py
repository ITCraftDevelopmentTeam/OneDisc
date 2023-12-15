from network.authentication import verify_access_token
import uvicorn_server
import fastapi
import call_action

BASE_CONFIG = {
    "host": "0.0.0.0",
    "port": 5700,
    "access_token": None
}

class HttpServer:

    def __init__(self, config: dict) -> None:
        self.config = BASE_CONFIG | config
        self.app = fastapi.FastAPI()
        self.app.add_route("/{action}", self.handle_request, ["GET", "POST"])

    async def start_server(self) -> None:
        await uvicorn_server.run(self.app, host=self.config["host"], port=self.config["port"])

    async def handle_request(self, request: fastapi.Request) -> fastapi.responses.JSONResponse:
        if not verify_access_token(request, self.config["access_token"]):
            if "Authorization" in request.headers.keys() or request.query_params.get("access_token"):
                raise fastapi.HTTPException(status_code=403, detail="Forbidden")
            else:
                raise fastapi.HTTPException(status_code=401, detail="Unauthorized")
        match request.method:
            case "GET":
                params = dict(request.query_params)
                if "access_token" in params.keys():
                    del params["access_token"]
            case "POST":
                params: dict = await request.json()
            case _:
                raise fastapi.HTTPException(
                    status_code=405,
                    detail=f"Method {request.method} not allowed"
                )

        content = await call_action.on_call_action(
            request.url.path[1:],
            params,
            params.get("echo"),
            11
        )
        self.check_retcode(content["retcode"])

        return fastapi.responses.JSONResponse(
            content
        )
    
    async def push_event(self, event: dict) -> None:
        pass

    @staticmethod
    def check_retcode(retcode: int) -> None:
        if retcode == 10002:
            raise fastapi.HTTPException(status_code=404, detail=f"API not found")
