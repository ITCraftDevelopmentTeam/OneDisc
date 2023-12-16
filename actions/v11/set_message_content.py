import utils.message.v11.parser as parser
import utils.translator as translator
from actions import register_action
from actions.v12.extra import edit_message


@register_action("v11", "edit_message")
@register_action("v11")
async def set_message_content(message_id: int, content: list | str) -> dict:
    if isinstance(content, str):
        message = parser.parse_string_to_array(content)
    else:
        message = content.copy()
    message = await translator.translate_message_array(message)
    return await edit_message(str(message_id), message)