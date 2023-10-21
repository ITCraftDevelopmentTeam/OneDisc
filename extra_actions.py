from api import register_action
from client import client
import return_object
import message_parser
import message_parser_v11
import translator


@register_action()
async def edit_message(message_id: str, content: list) -> dict:
    for message in client.cached_messages:
        if message.id == int(message_id):
            await message.edit(content=message_parser.parse_message(content)["content"])
            return return_object.get(0)
    return return_object.get(35002, f"消息 {message_id} 不存在")

@register_action("v11", "edit_message")
async def edit_message_v11(message_id: int, content: list | str) -> dict:
    if isinstance(content, str):
        message = message_parser_v11.parse_string_to_array(content)
    else:
        message = content.copy()
    message = translator.translate_message_array(message)
    return await edit_message(str(message_id), message)

