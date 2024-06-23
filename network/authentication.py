import fastapi


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
    if "Authorization" in request.headers.keys():
        return request.headers["Authorization"] == f"Bearer {access_token}"
    return request.query_params.get("access_token") == access_token
