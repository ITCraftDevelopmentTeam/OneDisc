from actions import action_list
from typing import Callable
from utils.type_checker import check_request_params
import utils.return_object as return_object 
from utils.type_checker import BadParam
from utils.logger import get_logger
import traceback
from utils.message.v12.parser import UnsupportedSegment, BadSegmentData
import random
from utils.config import config

logger = get_logger()

def get_action_function(action: str, protocol_version: int) -> Callable | None:
    """
    获取动作函数

    Args:
        action (str): 动作/接口名
        protocol_version (int): 协议版本 11/12

    Returns:
        Callable: 动作执行函数
    """
    if config["system"].get("action_isolation"):
        return action_list[f"v{protocol_version}"].get(action)
    if action in action_list.get(f"v{protocol_version}", {}).keys():
        return action_list[f"v{protocol_version}"][action]
    for actions in action_list.values():
        if action in actions.keys():
            return actions[action]
    return None


async def on_call_action(action: str, params: dict, echo: str | None = None, protocol_version: int = 12, **_) -> dict:
    logger.debug(f"请求执行动作：{action} ({params=}, {echo=}, {protocol_version=})")
    if config['system'].get("allow_strike") and random.random() <= 0.1:
        return return_object.get(36000, "I am tried.")
    if not (action_function := get_action_function(action, protocol_version)):
        return return_object.get(10002, f"未定义的动作：{action}")
    if not (params_checking_result := check_request_params(action_function, params))[0]:
        return params_checking_result[1]
    try:
        return_data = await action_function(**params)
    except UnsupportedSegment as e:
        return return_object.get(10005, str(e))
    except BadSegmentData as e:
        return return_object.get(10006, str(e))
    except BadParam as e:
        return return_object.get(10003, str(e))
    except Exception as e:
        logger.error(traceback.format_exc())
        return_data = return_object.get(20002, str(e))
    if not (isinstance(return_data, dict) or 0 <= return_data.get("retcode", -1) <= 90000):
        return_data = return_object.get(20001)
    if echo:
        return_data["echo"] = echo
    logger.debug(return_data)
    return return_data
