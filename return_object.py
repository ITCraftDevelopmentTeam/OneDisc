from logger import get_logger

logger = get_logger()

def get(code: int = 0, _message: str = "", **data) -> dict:
    """
    获取 OneBot 动作响应

    Args:
        code (int): 返回码 

    Returns:
        dict: 返回数据
    """
    if code != 0:
        logger.warning(f"动作执行失败 ({code}): {_message}")
    return {
        "status": "ok" if code == 0 else "failed",
        "retcode": code,
        "data": data or None,
        "message": _message
    }

def _get(code: int, data, message: str = "") -> dict:
    """
    获取 OneBot 动作响应

    Args:
        code (int): 返回码 

    Returns:
        dict: 返回数据
    """
    if code != 0:
        logger.warning(f"动作执行失败 ({code}): {message}")
    return {
        "status": "ok" if code == 0 else "failed",
        "retcode": code,
        "data": data,
        "message": message
    }
