from typing import Callable
from logger import get_logger

logger = get_logger()
action_list = {"v12": {}, "v11": {}}

'''
def register_action(name: str) -> Callable:
    """
    Register an action
    """
    def decorator(func: Callable) -> None:
        action_list[name] = func
        logger.debug(f"成功注册动作：{name}")
    return decorator
'''

def register_action(_type: str = "v12", name: str | None = None) -> Callable:
    def _(func: Callable):
        action_list[_type][name or func.__name__] = func
        logger.debug(f"成功注册动作：{func.__name__} ({_type=})")
        return func
    return _
