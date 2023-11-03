from config import config
from logger import get_logger
from client import client
from typing import (
    Any,
    TypedDict,
    Optional
)
import time
import message_parser_v11
import translator
import message_parser
import markdown2image

logger = get_logger()

class MessageSegment(TypedDict):
    data: dict[str, Any]
    type: str

class NodeItemData(TypedDict):
    content: list[MessageSegment]
    user_id: int
    nickname: Optional[str] 

class NodeItemDataWithMessageId(TypedDict):
    id: int

class NodeItem(TypedDict):
    type: str
    data: NodeItemData | NodeItemDataWithMessageId

async def get_message(node_item_data: NodeItemDataWithMessageId | NodeItemData) -> NodeItemData | None:
    if "id" not in node_item_data.keys():
        if "uin" in node_item_data.keys():
            node_item_data["user_id"] = int(node_item_data["uin"])
        if (not node_item_data.get("nickname")) and (user := client.get_user(node_item_data["user_id"])):
            node_item_data["nickname"] = user.name
        elif node_item_data.get("nickname"):
            node_item_data["nickname"] = str(node_item_data["user_id"])
        if isinstance(node_item_data["content"], str):
            node_item_data["content"] = message_parser_v11.parse_string_to_array(node_item_data["content"])
        return node_item_data
    else:
        for message in client.cached_messages:
            if message.id == node_item_data["id"]:
                return {
                    "user_id": message.author.id,
                    "nickname": message.author.name,
                    "content": await translator.translate_v12_message_to_v11(
                        message_parser.parse_string(
                            message.content
                        )
                    )
                }
        logger.warning(f"解析合并转发消息时出错：找不到 ID 为 {node_item_data['id']} 的消息")


def get_user_name(user_id: int) -> str:
    try:
        return client.get_user(user_id).name or str(user_id)
    except AttributeError:
        return str(user_id)


async def node2markdown(node: list[NodeItem]) -> str:
    markdown = config["system"].get("node_title", "### 合并转发消息\n\n")
    for node_item in node:
        if node_item["type"] != "node":
            continue
        node_item["data"] = await get_message(node_item["data"])
        if not node_item["data"]: continue
        markdown += f"##### {node_item['data']['nickname']}: \n\n"#<blockquote>"
        for s in node_item['data']['content']:
            match s['type']:
                case "text":
                    markdown += s["data"]["text"]
                case "at":
                    markdown += f'`@{get_user_name(s["data"]["qq"])}`'
            markdown += ""
        markdown += "\n\n"#</blockquote>\n\n"
    return markdown
    


async def node2image(node: list[NodeItem]) -> str:
    markdown2image.md2img(await node2markdown(node), n := f".cache/node.{time.time()}.png")
    return n
   

if __name__ == "__main__":
    import asyncio

    asyncio.run(node2image([
        {
            "type": "node",
            "data": {
                "user_id": 1006777034564968498,
                "content": "HelloWorld,[CQ:at,qq=114514]",
                "nickname": "XiaoDeng3386"
            }
        },
        {
            "type": "node",
            "data": {
                "user_id": 1006777034564968498,
                "content": "HelloWorld,[CQ:at,qq=114514]",
                "nickname": None
            }
        },
        {
            "type": "node",
            "data": {
                "user_id": 1006777034564968498,
                "content": "HelloWorld,[CQ:at,qq=114514]",
                "nickname": None
            }
        }


    ])) 
