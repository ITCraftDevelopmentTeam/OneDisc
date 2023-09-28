def get(code: int, message: str = "", **params) -> dict:
    """
    获取 OneBot 动作响应

    Args:
        code (int): 返回码 

    Returns:
        dict: 返回数据
    """
    return {
        "status": "ok" if code == 0 else "failed",
        "retcode": code,
        "data": params,
        "message": message
    }