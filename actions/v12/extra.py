from utils.config import config
import utils.message.v12.parser as parser
import utils.return_object as return_object
from actions import register_action
from utils.client import client


@register_action()
async def edit_message(message_id: str, content: list) -> dict:
    for message in client.cached_messages:
        if message.id == int(message_id):
            await message.edit(content=(await parser.parse_message(content))["content"])
            return return_object.get(0)
    return return_object.get(35002, f"消息 {message_id} 不存在")


@register_action()
async def call_api(endpoint: str, method: str, data: dict) -> dict:
    async with httpx.AsyncClient(proxies=config["system"]["proxy"]) as client:
        response = await client.request(
            method,
            f"https://discord.com/api/v9/{endpoint}",
            json=data
        )
    return return_object.get(
        0,
        status_code=response.status_code,
        response=response.json()
    )