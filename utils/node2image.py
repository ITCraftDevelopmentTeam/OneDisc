from time import time
from utils.config import config
from typing import Any, Literal
from utils.logger import get_logger
from utils.client import client
import utils.message.v11.parser as parser

# import utils.message.v12.parser as parser
import utils.translator as translator
import imgkit

logger = get_logger()


def get_message_by_id(message_id: int) -> dict | None:
    for message in client.cached_messages:
        if message.id == message_id:
            return {
                "user_id": message.author.id,
                "content": translator.translate_v12_message_to_v11(
                    parser.parse_string(message.content)
                ),
                "nickname": message.author.name,
            }
    logger.warning(f"解析合并转发节点时出现错误：找不到消息：{message_id}")


def get_nickname_by_id(user_id: int | Literal["all"]) -> str:
    if user_id == "all":
        return "全体成员"
    elif user := client.get_user(user_id):
        return user.name
    return str(user_id)


def init_dict_message(message: dict[str, Any]) -> dict[str, Any] | None:
    message["user_id"] = message.get("user_id") or message.get("uin")
    if not (message["user_id"] and message.get("content")):
        logger.warning(f"解析合并转发节点时出现错误：无效的节点：{message}")
        return
    if not message.get("nickname"):
        message["nickname"] = get_nickname_by_id(message["user_id"])
    if isinstance(message["content"], str):
        message["content"] = parser.parse_string_to_array(message["content"])
    return message


def get_message(message: dict[str, Any]) -> dict[str, Any] | None:
    if "message_id" in message:
        return get_message_by_id(message["message_id"])
    return init_dict_message(message)


def get_channel_name(channel_id: int) -> str:
    if not (channel := client.get_channel(channel_id)):
        return "未知频道"
    return channel.name


def get_file_url(file: str) -> str:
    if file.startswith("base64://"):
        return f"data:image/png;base64,{file[9:]}"
    return file


def message2html(message: list[dict[str, Any]]) -> str:
    html = ""
    is_node = False
    for segment in message:
        if segment["type"] != "node" and is_node:
            is_node = False
            html += "</div>"
        match segment["type"]:
            case "text":
                html += segment["data"]["text"]
            case "image":
                html += f'<img src="{get_file_url(segment["data"]["file"])}" width="100%" />'
            case "at":
                html += f'<strong>@{get_nickname_by_id(segment["data"]["qq"])}</strong>'
            case "channel":
                html += f'<strong>#{get_channel_name(segment["data"]["id"])}</strong>'

            case "node":
                if not is_node:
                    html += (
                        '<div style="mapping: 10px;border: 2px solid #000; padding: 10px;">'
                        "<h2>嵌套合并转发消息</h2>"
                    )
                    is_node = True
                if not (message := get_message(segment["data"])):
                    continue
                html += f'<hr><h4><strong>{message["nickname"]}</strong>: </h4><p>'
                html += message2html(message["content"])
                html += "</p>"
    if is_node:
        html += "</div>"

    return html.replace(
        "\n", config["system"].get("node_linebreak_replacement", "<br>")
    )


def node2html(messages: list[dict[str, Any]]) -> str:
    html = (
        "<!DOCTYPE html>"
        "<html>"
        "<head>"
        '<meta charset="utf-8">'
        '<link href="https://cdnjs.cloudflare.com/ajax/libs/mdb-ui-kit/6.1.0/mdb.min.css" rel="stylesheet" />'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "</head>"
        '<body style="background-color: #f1f1f1;">'
        '<div class="container">'
        "<br>"
        "<h1>合并转发消息</h1>"
    )
    for item in messages:
        if not (message := get_message(item["data"])):
            continue
        html += f'<hr><h3><strong>{message["nickname"]}</strong>: </h3><p>'
        html += message2html(message["content"])
        html += "</p>"
    return html + f"<br></div></body></html>"


if config["system"].get("wkhtmltopdf"):
    logger.info(f"WKHTMLTOPDF 路径：{config['system']['wkhtmltopdf']}")
    imgkit_config = imgkit.config(wkhtmltoimage=config["system"]["wkhtmltopdf"])
else:
    imgkit_config = None


def node2image(messages: list[dict[str, Any]]) -> str:
    file_name = f".cache/node.{time()}.{config['system'].get('node_image_type', 'jpg')}"
    imgkit.from_string(node2html(messages), file_name, config=imgkit_config)
    return file_name


if __name__ == "__main__":
    """
        print(node2image([
            {
                "type": "node",
                "data": {
                    "user_id": 114514,
                    "nickname": "XiaoDeng3386",
                    "content": "Hello world",
                }
            },
            {
                "type": "node",
                "data": {
                    "user_id": 114514,
                    "nickname": "XiaoDeng3386",
                    "content": "Hello, [CQ:at,qq=114514]",
                }
            },

            {
                "type": "node",
                "data": {
                    "user_id": 114514,
                    "nickname": "XiaoDeng3386",
                    "content": [
                        {
                            "type": "node",
                            "data": {
                                "user_id": 114514,
                                "nickname": "XiaoDeng3386",
                                "content": [
                        {
                            "type": "node",
                            "data": {
                                "user_id": 114514,
                                "nickname": "XiaoDeng3386",
                                "content": "Hello, [CQ:at,qq=114514]",
                            }
                        }
                    ],

                            }
                        }
                    ],
                }
            },
    {
                "type": "node",
                "data": {
                    "user_id": 114514,
                    "nickname": "XiaoDeng3386",
                    "content": "[CQ:image,file=https://www.dmoe.cc/random.php]",
                }
            },
        ]))


    """
    node = [
        {
            "type": "node",
            "data": {
                "user_id": 114514,
                "nickname": "XiaoDeng3386",
                "content": "Hello, [CQ:at,qq=114514]",
            },
        },
        {
            "type": "node",
            "data": {
                "user_id": 114514,
                "nickname": "XiaoDeng3386",
                "content": "[CQ:image,file=https://www.dmoe.cc/random.php]",
            },
        },
    ]

    for i in range(100):
        node = [
            {
                "type": "node",
                "data": {
                    "user_id": 114514,
                    "nickname": "XiaoDeng3386",
                    "content": "Hello, [CQ:at,qq=114514]",
                },
            },
            {
                "type": "node",
                "data": {
                    "user_id": 114514,
                    "nickname": "XiaoDeng3386",
                    "content": node,
                },
            },
        ]
    print(node2image(node))
