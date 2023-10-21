import file
from logger import get_logger
from config import config
from client import client
import discord
import message_tokenizer
import re
import discord.file


class BadSegmentData(Exception):
    pass


class UnsupportedSegment(Exception):
    pass


logger = get_logger()



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
                case "reply":
                    for msg in client.cached_messages:
                        if msg.id == int(segment["data"]["message_id"]):
                            message_data["reference"] = msg
                            break
                    else:
                        logger.warning(f"解析消息段 {segment} 时出现错误：找不到指定消息，已忽略")

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


def parse_string(string: str) -> list:
    message = []
    tokenized_messages = message_tokenizer.tokenizer(string)
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
    logger.debug(message)
    return message
