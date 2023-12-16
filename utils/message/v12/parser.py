import actions.v12.file as file
from utils.logger import get_logger
from utils.config import config
from utils.client import client
import discord
import utils.message.v12.tokenizer as tokenizer
import re
import discord.file


class BadSegmentData(Exception):
    pass


class UnsupportedSegment(Exception):
    pass


logger = get_logger()


def get_embed_color(color: str | None, is_default: bool = False) -> discord.Color:
    if color:
        if hasattr(discord.Color, color):
            return getattr(discord.Color, color)()
        else:
            try:
                return discord.Color.from_str(color)
            except ValueError:
                logger.warning(f"无效的颜色：{color}")
                if not is_default:
                    return get_embed_color(config["system"].get("embed_default_color"), is_default=True)
                return get_embed_color(None, True)
    elif not is_default:
        return get_embed_color(config["system"].get("embed_default_color"), True)
    else:
        return discord.Color.default()

def escape_mentions(text):
    text = text.replace("<", "<\u200B").replace(">", "\u200B>")
    text = text.replace("@everyone", "@\u200Beveryone")
    text = text.replace("@here", "@\u200Bhere")
    return text


async def parse_message(message: list) -> dict:
    logger.debug(config)
    message_data = {"content": "", "files": []}
    for segment in message:
        try:
            if segment["type"] == "location":
                segment = {
                    "type": "discord.embed",
                    "data": {
                        "title": segment["data"]["title"],
                        "description": segment["data"]["content"],
                        "url": f"https://www.google.com/maps/place/{segment['data']['latitude']},{segment['data']['longitude']}"
                    }
                }
            match segment["type"]:
                case "text":
                    message_data["content"] += escape_mentions(segment["data"]["text"])
                case "mention":
                    message_data["content"] += f"<@{segment['data']['user_id']}>"
                case "mention_all":
                    message_data["content"] += "@everyone"
                case "image" | "voice" | "audio" | "video" | "file":
                    message_data["files"].append(
                        discord.file.File(
                            open(
                                file.get_file_path(
                                    await file.get_file_name_by_id(segment["data"]["file_id"])
                                ),
                                "rb",
                            )
                        )
                    )
                    if segment["type"] == "voice":
                        logger.warning("OneDisc 暂不支持 voice 消息段，将以 audio 消息段发送")
                case "discord.emoji":
                    message_data[
                        "content"
                    ] += f'<:{segment["data"]["name"]}:{segment["data"]["id"]}>'
                case "discord.channel":
                    message_data["content"] += f"<#{segment['data']['channel_id']}>"
                case "discord.role":
                    message_data["content"] += f"<@&{segment['data']['id']}>"
                case "discord.timestamp":
                    if segment["data"].get("style"):
                        style = f':{segment["data"]["style"]}'
                    else:
                        style = ""
                    message_data["content"] += f"<t:{segment['data']['time']}{style}>"
                case "discord.navigation":
                    message_data["content"] += f"<id:{segment['data']['type']}>"
                case "reply":
                    for msg in client.cached_messages:
                        if msg.id == int(segment["data"]["message_id"]):
                            message_data["reference"] = msg
                            break
                    else:
                        logger.warning(f"解析消息段 {segment} 时出现错误：找不到指定消息，已忽略")

                case "discord.embed":
                    message_data["embed"] = discord.Embed(
                        title=segment["data"]["title"],
                        description=segment["data"].get("description"),
                        color=get_embed_color(segment["data"].get("color")),
                        url=segment["data"].get("url")
                    )
                    if segment["data"].get("fields"):
                        for field in segment["data"]["fields"]:
                            message_data["embed"].add_field(
                                name=field.get("name"),
                                value=field.get("value"),
                                inline=field.get("inline")
                            )
        

                case _:
                    if config["system"].get("ignore_unsupported_segment"):
                        logger.warning(f"不支持的消息段类型：{segment['type']}，已忽略")
                    else:
                        raise UnsupportedSegment(f'不支持的消息段: {segment["type"]}')
        except KeyError as e:
            raise BadSegmentData(f"无效的参数：{e} (在 {segment['type']} 中)")
    if not message_data["files"]:
        message_data.pop("files")
    logger.debug(message_data)
    return message_data


def parse_string(string: str, msg: discord.Message | None = None) -> list:
    message = []
    tokenized_messages = tokenizer.tokenizer(string)
    for token in tokenized_messages:
        match token[0]:
            case "mention":
                message.append({"type": "mention", "data": {"user_id": token[1][2:-1]}})
            case "mention_all":
                message.append({"type": "mention_all", "data": {}})
            case "text":
                message.append({"type": "text", "data": {"text": token[1]}})
            case "channel":
                message.append({
                    "type": "discord.channel",
                    "data": {
                        "channel_id": token[1][2:-1]
                    }
                })
            case "emoji":
                message.append(
                    {
                        "type": "discord.emoji",
                        "data": {
                            "name": re.search(":.+:", token[1]).group(0)[1:-1],  # type: ignore
                            "id": int(re.search("[0-9]+>", token[1]).group(0)[:-1]),  # type: ignore
                        },
                    }
                )
            case "role":
                message.append({
                    "type": "discord.role",
                    "data": {
                        "id": token[1][3:-1]
                    }
                })
            case "navigation":
                message.append({
                    "type": "discord.navigation",
                    "data": {
                        "type": token[1][4:-1]
                    }
                })
            case "timestamp":
                message.append({
                    "type": "discord.timestamp",
                    "data": {
                        "time": int(re.search("[0-9]+", token[1]).group(0)),
                        "style": token[1][-2] if token[1][-2] in ["s", "m", "h", "d"] else "d"
                    }
                })
    for attachment in msg.attachments:
        for file_type in ["image", "video", "audio"]:
            if attachment.content_type.startswith(file_type):
                message.append({"type": file_type, "data": {"file_id": file.create_url_cache(attachment.filename, attachment.url)}})
                break
        else:
            message.append({"type": "file", "data": {"file_id": file.create_url_cache(attachment.filename, attachment.url)}})
    logger.debug(message)
    return message
