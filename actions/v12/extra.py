from utils import discord_api
import utils.message.v12.parser as parser
import utils.return_object as return_object
from actions import register_action
from utils.db import get_session, Message


@register_action()
async def edit_message(message_id: str, content: list) -> dict:
    async with get_session() as session:
        message = await session.get_one(
            Message,
            int(message_id)
        )
    await discord_api.call(
        "PATCH",
        f"/channels/{message.channel}/messages/{message.id}",
        await parser.parse_message(content)
    )
    return return_object.get(0)



@register_action()
async def call_api(endpoint: str, method: str, data: dict) -> dict:
    response = await discord_api.call(method, endpoint, data)
    return return_object.get(
        0,
        status_code=response["code"],
        response=response
    )