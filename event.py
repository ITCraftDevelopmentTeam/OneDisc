import uuid
import asyncio
import traceback
import connection
import time
from logger import get_logger

self_id: str
logger = get_logger()


def init(_self_id: str) -> None:
    """
    初始化

    Args:
        self_id (str): 机器人自身ID
    """
    global self_id
    self_id = _self_id


def new_event(
        _type: str,
        detail_type: str,
        sub_type: str = "",
        _time: float | None = None,
        **params
) -> None:
    event_object = {
        "id": str(uuid.uuid1()),
        "self": {
            "platform": "discord",
            "user_id": self_id,
        },
        "time": _time or time.time(),
        "type": _type,
        "detail_type": detail_type,
        "sub_type": sub_type
    }
    event_object.update(params)
    logger.debug(event_object)
    for conn in connection.connections:
        try:
            asyncio.create_task(conn["add_event_func"](event_object))
        except Exception:
            logger.error(f"在 {conn['type']} 广播事件失败：{traceback.format_exc()}")
    logger.debug("广播事件完成")