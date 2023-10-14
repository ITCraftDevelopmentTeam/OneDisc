from api import action_list
from typing import Callable
import inspect
import return_object 
from checker import BadParam
from logger import get_logger
import traceback
from message_parser import UnsupportedSegment, BadSegmentData
import random
from config import config

logger = get_logger()

def check_params(func: Callable, params: dict) -> tuple[bool, dict]:
    """
    检查参数及类型类型

    Args:
        func (Callable): 动作函数
        params (dict): 实参列表

    Returns:
        tuple[bool] | tuple[bool, dict]: 检查结果
    """
    arg_spec = inspect.getfullargspec(func)
    for key in list(params.keys()):
        if key not in arg_spec.args:
            if config["system"].get("ignore_unneeded_args", True):
                logger.warning(f"参数 {key} 未在 {func.__name__} 中定义，已忽略")
                del params[key]
                continue
            else:
                return False, return_object.get(10004, f"参数 {key} 未在 {func.__name__} 中定义")
        if key in arg_spec.annotations.keys() and not isinstance(params[key], arg_spec.annotations[key]):
            if not config["system"].get("ignore_error_types"):
                return False, return_object.get(10001, f"参数 {key} ({type(params[key])}，应为 {arg_spec.annotations[key]}) 类型不正确")
            logger.warning(f"参数 {key} ({type(params[key])}，应为 {arg_spec.annotations[key]}) 类型不正确，已忽略")
    return True, {}
        

            


async def on_call_action(action: str, params: dict, echo: str | None = None, **_) -> dict:
    logger.debug(f"请求执行动作：{action} ({params=}, {echo=})")
    if config['system'].get("allow_strike") and random.random() <= 0.1:
        return return_object.get(36000, "I am tried.")
    if action not in action_list.keys():
        return return_object.get(10002, "action not found")
    if not (params_checking_result := check_params(action_list[action], params))[0]:
        return params_checking_result[1]
    try:
        return_data = await action_list[action](**params)
    except UnsupportedSegment as e:
        return return_object.get(10005, str(e))
    except BadSegmentData as e:
        return return_object.get(10006, str(e))
    except BadParam as e:
        return return_object.get(10003, str(e))
    # except TypeError as e:
    #     if "got an unexpected keyword argument" in str(e):
    #         return return_object.get(10004, str(e))
    #     else:
    #         logger.error(traceback.format_exc())
    #         return_data = return_object.get(20002, str(e))
    except Exception as e:
        logger.error(traceback.format_exc())
        return_data = return_object.get(20002, str(e))
    if echo:
        return_data["echo"] = echo
    logger.debug(return_data)
    return return_data
