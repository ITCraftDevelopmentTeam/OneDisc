import basic_actions_v12
from api import register_action
from discord.abc import PrivateChannel
from discord.channel import CategoryChannel, ForumChannel
from discord.types.channel import ThreadChannel
from logger import get_logger
import translator
import message_parser_v11
import return_object
from client import client
import message_parser_v11


logger = get_logger()

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
    # resp_data = translator.translate_action_response(
        # await basic_actions_v12.get_user_info(
            # str(user_id)
        # )
    # )
    # resp_data["data"]["nickname"] = resp_data["data"].get("user_name", "")
    # resp_data["data"]["sex"] = "unknown"
    return translator.translate_action_response(
        await basic_actions_v12.get_user_info(
            str(user_id)
        )
    )


@register_action("v11")
async def get_login_info() -> dict:
    return translator.translate_action_response(
        await basic_actions_v12.get_self_info()
    )

@register_action("v11")
async def get_msg(message_id: int) -> dict:
    for msg in client.cached_messages:
        if msg.id == message_id:
            return return_object.get(
                0,
                time=-1,
                message_type="normal",
                message_id=msg.id,
                real_id=msg.id,
                sender={
                    "user_id": msg.author.id,
                    "nickname": msg.author.name,
                    "card": msg.author.display_name,
                    "sex": "unknown"
                },
                message=message_parser_v11.parse_text(msg.content)
            )
    return return_object.get(
        1404,
        "消息不存在！"
    )

@register_action("v11")
async def set_group_kick(group_id: int, user_id: int, reason: str | None = None, reject_add_request: bool = False) -> dict:
    if not (group := client.get_channel(group_id)):
        return return_object.get(
            1404,
            f"不存在的频道：{group_id}"
        )
    if isinstance(group, PrivateChannel | ForumChannel | ThreadChannel | CategoryChannel):
        return return_object.get(
            1400,
            f"不支持的操作：从 {type(group)} 中移除 {user_id}"
        )
    for user in group.members:
        if user.id == user_id:
            await user.kick(reason=reason)  # type: ignore
            logger.info(f"已将 {user.name} ({user.id}) 从频道 {group.name} 中移除") # type: ignore
            return return_object.get(0)
    return return_object.get(
        1400,
        f"未找到用户：{user_id} （在 {group.id} 中）"
    )




