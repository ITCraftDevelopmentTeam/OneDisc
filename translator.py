from config import config
import message_parser_v11
from client import client
from logger import get_logger

logger = get_logger()


def translate_event(_event: dict) -> dict:
    event = _event.copy()
    # 键名替换
    event["time"] = int(event["time"]) 
    event["self_id"] = int(event.pop("self")["user_id"])
    event["post_type"] = event.pop("type")
    if event["post_type"] == "meta":
        event["post_type"] = "meta_event"
    event[f"{event['post_type']}_type"] = event.pop("detail_type").replace("channel", "group")
    event.pop("id")
    if event[f"{event['post_type']}_type"] == "channel":
        event[f"{event['post_type']}_type"] = "group"
    if not event["sub_type"]:
        del event["sub_type"]
    if "channel_id" in event.keys():
        event["group_id"] = int(event.pop("channel_id"))
    # 类型替换
    if "user_id" in event.keys():
        event["user_id"] = int(event["user_id"])
    if "group_id" in event.keys():
        event["group_id"] = int(event["group_id"])
    if "operator_id" in event.keys():
        event["operator_id"] = int(event["operator_id"])
    if "message_id" in event.keys():
        event["message_id"] = int(event["message_id"])
    if event["post_type"] == "message":
        if event["message_type"] == "private":
            event["sub_type"] = config["system"].get("default_message_sub_type", "group")
        elif event["message_type"] == "group":
            event["sub_type"] = "normal"
            event["anonymous"] = None
            event["font"] = 0
        event["raw_message"] = event.pop("alt_message")
        sender = client.get_user(event["user_id"])
        event["sender"] = {
            "user_id": event["user_id"]
        }
        if sender:
            event["sender"].update({
                "nickname": sender.global_name,
                "card": sender.display_name
            })
        event["message"] = message_parser_v11.parse_text(event["raw_message"])
    logger.debug(event)
    return event


def translate_action_response(_response: dict) -> dict:
    response = _response.copy()
    if isinstance(response["data"], dict):
        for key, value in response["data"].items():
            if key.endswith("_id"):
                try:
                    response["data"][key] = int(value)
                except ValueError:
                    pass
    elif isinstance(response["data"], list):
        length = 0
        for item in response["data"]:
            response["data"][length] = translate_action_response(item)
            length += 1
    return response

def translate_message_array(_message: list) -> list:
    message = _message.copy()
    length = -1
    for item in message:
        length += 1
        match item["type"]:
            case "at":
                message[length]["type"] = "mention"
                message[length]["data"]["user_id"] = message[length]["data"].pop("qq")
            case "reply":
                message[length]["data"]["message_id"] = message[length]["data"].pop("id")
    return message
            
        
