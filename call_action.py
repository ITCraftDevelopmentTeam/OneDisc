from api import action_list
import return_object 
from checker import BadParam
from logger import get_logger
import traceback
from message_parser import UnsupportedSegment, BadSegmentData
import random
from config import config

logger = get_logger()

async def on_call_action(action: str, params: dict, echo: str | None = None, **_) -> dict:
    logger.debug(f"请求执行动作：{action} ({params=}, {echo=})")
    if config['system'].get("allow_strike") and random.random() <= 0.1:
        return return_object.get(36000, "I am tried.")
    if action not in action_list.keys():
        return return_object.get(10002, "action not found")
    try:
        return_data = await action_list[action](**params)
    except UnsupportedSegment as e:
        return return_object.get(10005, str(e))
    except BadSegmentData as e:
        return return_object.get(10006, str(e))
    except BadParam as e:
        return return_object.get(10003, str(e))
    except TypeError as e:
        if "got an unexpected keyword argument" in str(e):
            return return_object.get(10004, str(e))
        else:
            logger.error(traceback.format_exc())
            return_data = return_object.get(20002, str(e))
    except Exception as e:
        logger.error(traceback.format_exc())
        return_data = return_object.get(20002, str(e))
    if echo:
        return_data["echo"] = echo
    logger.debug(return_data)
    return return_data
