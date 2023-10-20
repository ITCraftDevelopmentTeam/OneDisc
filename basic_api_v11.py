import basic_actions_v12
from api import register_action
import translator
import message_parser_v11
import return_object
from client import client


@register_action("v11")
async def send_group_msg(
    group_id: int,
    message: str | list[dict],
    auto_escape: bool = False
) -> dict:
    if isinstance(message, str) and not auto_escape:
        message = message_parser_v11.parse_text(message)
    elif isinstance(message, str):
        message = [{
            "type": "text",
            "data": {
                "text": message
            }
        }]
    return translator.translate_action_response(
        await basic_actions_v12.send_message(
            "group",
            translator.translate_message_array(message),
            group_id = str(group_id)
        )
    )



@register_action("v11")
async def send_msg(
    message: str | list,
    message_type: str,
    group_id: int | None = None,
    user_id: int | None = None,
    auto_escape: bool = False
) -> dict:
    if isinstance(message, str) and not auto_escape:
        message = message_parser_v11.parse_text(message)
    elif isinstance(message, str):
        message = [{
            "type": "text",
            "data": {
                "text": message
            }
        }]
    return translator.translate_action_response(
        await basic_actions_v12.send_message(
            message_type,
            translator.translate_message_array(message),
            group_id=str(group_id),
            user_id=str(user_id)
        )
    )


@register_action("v11")
async def get_stranger_info(
    user_id: int,
    no_cache: bool = False
) -> dict:
    resp_data = translator.translate_action_response(
        await basic_actions_v12.get_user_info(
            str(user_id)
        )
    )
    resp_data["data"]["nickname"] = resp_data["data"].get("user_name", "")
    resp_data["data"]["sex"] = "unknown"
    return resp_data
