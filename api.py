from typing import Callable
from logger import get_logger

logger = get_logger()
action_list = {}

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

def register_action(func: Callable) -> None:
    action_list[func.__name__] = func
    logger.debug(f"成功注册动作：{func.__name__}")