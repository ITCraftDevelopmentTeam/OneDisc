from api import register_action
import httpx
from client import client
from logger import discord_api_failed
import return_object
import message_parser
from config import config
import message_parser_v11
import translator

@register_action()
async def edit_message(message_id: str, content: list) -> dict:
    for message in client.cached_messages:
        if message.id == int(message_id):
            await message.edit(content=await message_parser.parse_message(content)["content"])
            return return_object.get(0)
    return return_object.get(35002, f"消息 {message_id} 不存在")

@register_action("v11", "edit_message")
async def edit_message_v11(message_id: int, content: list | str) -> dict:
    if isinstance(content, str):
        message = message_parser_v11.parse_string_to_array(content)
    else:
        message = content.copy()
    message = await translator.translate_message_array(message)
    return await edit_message(str(message_id), message)

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
