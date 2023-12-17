import inspect
import traceback
import utils.return_object as return_object
from utils.config import config
from typing import Callable
from utils.logger import get_logger

logger = get_logger()

class BadParam(Exception): pass

def check_aruments(*args) -> None:
    if None in args:
        raise BadParam("None is not allowed")
    

def check_request_params(func: Callable, params: dict) -> tuple[bool, dict]:
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
        if config["system"].get("skip_params_type_checking", False):
            continue
        try:
            if not key in arg_spec.annotations.keys():
                continue
            arg_type = arg_spec.annotations[key]
            if not isinstance(arg_type, type):
                if hasattr(arg_type, "__origin__"):
                    arg_type = arg_type.__origin__
                else:
                    continue
            if not isinstance(params[key], arg_type if isinstance(arg_type)):
                logger.warning(f"参数 {key} ({type(params[key])}，应为 {arg_spec.annotations[key]}) 类型不正确，尝试强制转换")
                try:
                    params[key] = arg_spec.annotations[key](params[key])
                except Exception:
                    logger.error(f"强制转换类型失败：{traceback.format_exc()}")
                    return False, return_object.get(10001, f"参数 {key} ({type(params[key])}，应为 {arg_spec.annotations[key]}) 类型不正确")
        except TypeError:
            logger.warning(f"检查参数 {key} 的类型时出现错误：{traceback.format_exc()}")
    return True, {}
        
