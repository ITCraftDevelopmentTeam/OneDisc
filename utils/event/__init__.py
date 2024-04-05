import uuid
import asyncio
import traceback
import network as network
from utils.client import client
import time
from utils.logger import get_logger

logger = get_logger()


def get_event_object(
    _type: str,
    detail_type: str,
    sub_type: str = "",
    _time: float | None = None,
    params={},
) -> dict:
    event_object = {
        "id": str(uuid.uuid1()),
        "self": {
            "platform": "discord",
            "user_id": str(client.user.id),
        },
        "time": _time or time.time(),
        "type": _type,
        "detail_type": detail_type,
        "sub_type": sub_type,
    }
    event_object.update(params)
    logger.debug(event_object)
    return event_object


def new_event(
    _type: str,
    detail_type: str,
    sub_type: str = "",
    _time: float | None = None,
    **params,
) -> None:
    event_object = get_event_object(_type, detail_type, sub_type, _time, params)
    for conn in network.connections:
        try:
            asyncio.create_task(conn["add_event_func"](event_object))
        except Exception:
            logger.error(f"在 {conn['type']} 广播事件失败：{traceback.format_exc()}")
    logger.debug("广播事件完成")
