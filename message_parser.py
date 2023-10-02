import file
from logger import get_logger
from config import config

class BadSegmentData(Exception): pass
class UnsupportedSegment(Exception): pass

logger = get_logger()

def escape_mentions(text):
    text = text.replace('<', '<\u200B').replace('>', '\u200B>')
    text = text.replace('@everyone', '@\u200Beveryone')
    text = text.replace('@here', '@\u200Bhere')
    return text

def parse_message(message: list) -> dict:
    message_data = {"content": "", "file": []}
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
                    message_data["file"].append(file.get_file_path(file.get_file_name_by_id(segment["data"]["file_id"])))
                    if segment["type"] == "voice":
                        logger.warning("OneDisc 暂不支持 voice 消息段，将以 audio 消息段发送")
                
                case _:
                    if config["system"].get("ignore_unsupported_segment"):
                        logger.warning(f"不支持的消息段类型：{segment['type']}，已忽略")
                    else:
                        raise UnsupportedSegment
        except KeyError:
            raise BadSegmentData
    if not message_data["file"]:
        message_data.pop("file")
    return message_data

def parse_string(string: str, file: list = []) -> list:
    # TODO
    return [{
        "type": "text",
        "data": {
            "text": string
        }
    }]
