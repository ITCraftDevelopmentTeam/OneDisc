import traceback
from typing import Awaitable, Callable
from utils.logger import get_logger
from utils import return_object
from actions import register_action

handlers: dict[str, dict[str, Callable[..., Awaitable[None]]]] = {}
logger = get_logger()


async def handle_quick_operation(content: dict, event: dict) -> None:
    """
    处理 OneBot V11 快速操作请求

    Args:
        content (dict): 快速操作内容
        event (dict): 所属事件
    """
    try:
        handler = handlers[post_type := event["post_type"]][event[f"{post_type}_type"]]
    except KeyError:
        logger.warning(f"事件没有可用的快速操作选项: {event['post_type']=}")
        return
    try:
        await handler(**content, event=event)
    except Exception:
        logger.error(f"处理快速操作时出现错误: {traceback.format_exc()}")
    

def register_quick_operation(post_type: str, detail_type: str) -> Callable[..., Callable[..., Awaitable[None]]]:
    def _(func: Callable[..., Awaitable[None]]) -> Callable[..., Awaitable[None]]:
        if post_type not in handlers.keys():
            handlers[post_type] = {}
        handlers[post_type][detail_type] = func
        logger.debug(f"成功注册快速操作: {post_type}.{detail_type}")
        return func
    return _

@register_action("v11", ".handle_quick_operation")
async def _(context: dict, operation: dict) -> dict:
    await handle_quick_operation(operation, context)
    return return_object.get()