import fastapi


def get_bearer_token(
    request: fastapi.Request | fastapi.WebSocket,
) -> str | None:
    """
    大小写不敏感地获取 Authorization header 值

    uvicorn 按 ASGI 规范会把 header 名转为小写，但不同服务器/客户端可能保留
    原始大小写，因此逐项比较 key.lower() 最稳妥（starlette 的 get() 依赖内部
    存储大小写，两种场景下行为不一致）

    Args:
        request (fastapi.Request | fastapi.WebSocket): 请求信息

    Returns:
        str | None: Authorization header 值，不存在时为 None
    """
    for key, value in request.headers.items():
        if key.lower() == "authorization":
            return value
    return None


def verify_access_token(
    request: fastapi.Request | fastapi.WebSocket, access_token: str | None
) -> bool:
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
    authorization = get_bearer_token(request)
    if authorization is not None:
        return authorization == f"Bearer {access_token}"
    return request.query_params.get("access_token") == access_token
