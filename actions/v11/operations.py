from typing import Optional
from .quick_operation import register_quick_operation
from utils.message.v11.parser import parse_string_to_array
from . import basic as actions

@register_quick_operation("message", "private")
async def _(
    event: dict,
    reply: Optional[str | list[dict]] = None,
    auto_escape: bool = False
) -> None:
    if reply is not None:
        await actions.send_private_msg(
            event["user_id"],
            reply,
            auto_escape
        )

def parse_reply_message(
        original_message: str | list[dict],
        user_id: int,
        at_sender: bool,
        auto_escape: bool
) -> str | list[dict]:
    if not at_sender:
        return original_message
    if isinstance(original_message, str):
        if auto_escape:
            message = parse_string_to_array(original_message)
        else:
            message = [{
                "type": "text",
                "data": {
                    "text": original_message
                }
            }]
    else:
        message = original_message.copy()
    message.insert(0, {
        "type": "at",
        "data": {
            "qq": user_id
        }
    })
    return message


@register_quick_operation("message", "group")
async def _(
    event: dict,
    reply: Optional[str | list[dict]] = None,
    auto_escape: bool = False,
    at_sender: bool = True,
    delete: bool = False,
    kick: bool = False,
    ban: bool = False,
    ban_duration: int = 1800
) -> None:
    if reply is not None:
        await actions.send_group_msg(
            event["group_id"],
            parse_reply_message(
                reply,
                event["user_id"],
                at_sender,
                auto_escape
            ),
            auto_escape
        )
    if delete is not None:
        await actions.delete_message(event["message_id"])
    if ban is not None:
        await actions.set_group_ban(
            event["group_id"],
            event["user_id"],
            ban_duration
        )
    if kick is not None:
        await actions.set_group_kick(
            event["group_id"],
            event["user_id"]
        )
