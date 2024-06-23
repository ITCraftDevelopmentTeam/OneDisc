import utils.event as event
import asyncio


async def setup_heartbeat_event(config: dict) -> None:
    """
    初始化心跳元事件

    Args:
        config (dict): 心跳事件配置
    """
    while config.get("enabled", True):
        await asyncio.sleep(config.get("interval", 5000) * 0.001)
        event.new_event("meta", "heartbeat", interval=config.get("interval", 5000))
