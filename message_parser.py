import file
from logger import get_logger
from config import config
import message_tokenizer
import re

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
                case "dc.emoji":
                    message_data["content"] += f'<:{segment["data"]["name"]}:{segment["data"]["id"]}>'
                
                case _:
                    if config["system"].get("ignore_unsupported_segment"):
                        logger.warning(f"不支持的消息段类型：{segment['type']}，已忽略")
                    else:
                        raise UnsupportedSegment(segment["type"])
        except KeyError as e:
            raise BadSegmentData(segment["type"])
    if not message_data["file"]:
        message_data.pop("file")
    return message_data

def parse_string(string: str) -> list:
    message = []
    tokenized_messages = message_tokenizer.tokenizer(string)
    for token in tokenized_messages:
        match token[0]:
            case 'mention':
                message.append({
                    "type": "mention",
                    "data": {
                        "user_id": token[1][2:-1]
                    }
                })
            case 'mention_all':
                message.append({
                    "type": 'mention_all',
                    'data': {}
                })
            case "text":
                message.append({
                    "type": "text",
                    "data": {
                        "text": token[1]
                    }
                })
            case "dc.emoji":
                message.append({
                    "type": "dc.emoji",
                    "data": {
                        "name": re.search(":.+:", token[1]).group(0)[1:-1],   # type: ignore
                        "id": re.search("[0-9]+>", token[1]).group(0)[:-1]  # type: ignore
                    }
                })
    return message
    
