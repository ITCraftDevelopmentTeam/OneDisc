from api import api_list
import return_object 
from logger import get_logger
import traceback

logger = get_logger()


async def on_call_action(action: str, params: dict, echo: str | None = None) -> dict:
    try:
        return_data = await api_list[action](**params)
    except Exception as e:
        logger.error(traceback.format_exc())
        return_data = return_object.get(20002, str(e))
    if echo:
        return_data["echo"] = echo
    return return_data
