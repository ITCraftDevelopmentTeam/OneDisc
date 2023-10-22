from config import config
import json
import time
import file
from client import client
import basic_api_v11
from logger import get_logger

logger = get_logger()


async def translate_event(_event: dict) -> dict:
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
        event["message"] = await translate_v12_message_to_v11(event["message"])
    elif event["post_type"] == "meta_event" and event["meta_event_type"] == "heartbeat":
        event["status"] = (await basic_api_v11.get_status())["data"]
    logger.debug(event)
    return event


def translate_action_response(_response: dict) -> dict:
    response = _response.copy()
    if isinstance(response["data"], dict):
        for key, value in list(response["data"].items()):
            if isinstance(value, dict):
                response["data"][key] = translate_action_response({"data": value})["data"]
            elif key.endswith("_id"):
                try:
                    response["data"][key] = int(value)
                except ValueError:
                    pass
            elif key == "user_name":
                response["data"]["nickname"] = value
    elif isinstance(response["data"], list):
        length = 0
        for item in response["data"]:
            response["data"][length] = translate_action_response({"data": item})["data"]
            length += 1
    return response

async def translate_message_array(_message: list) -> list:      # v11 -> v12
    message = _message.copy()
    length = -1
    for item in message:
        length += 1
        match item["type"]:
            case "at":
                if item["data"]["qq"] != "all":
                    message[length]["type"] = "mention"
                    message[length]["data"]["user_id"] = message[length]["data"].pop("qq")
                else:
                    message[length]["type"] = "mention_all"
                    message[length]["data"] = {}
            case "reply":
                message[length]["data"]["message_id"] = str(message[length]["data"].pop("id"))
            case "image" | "record" | "video":
                if item["data"]["file"].startswith("http"):
                    file_name = (splited_url := item["data"]["file"].split("/"))[-1] or splited_url[-2] or f"{int(time.time())}"
                    message[length]["data"]["file_id"] = (await file.upload_file(
                        "url",
                        file_name,
                        item["data"]["file"]
                    ))["data"]["file_id"]
                elif item["data"]["file"].startswith("file"):
                    file_name = (splited_url := item["data"]["file"].split("/"))[-1] or splited_url[-2] or f"{int(time.time())}"
                    message[length]["data"]["file_id"] = (await file.upload_file(
                        "name",
                        file_name,
                        path=item["data"]["file"][7:]
                    ))["data"]["file_id"]
                elif item["data"]["file"].startswith("base64"):
                    message[length]["data"]["file_id"] = (await file.upload_file(
                        "data",
                        f"{int(time.time())}",
                        data=item["data"]["file"][9:]
                    ))["data"]["file_id"]
                if item["type"] == "record":
                    item["type"] = "voice"
            # case "image" | "record" | "video":
            #     if item["data"].get("url") or item["data"].get("file", "").startswith("http") or item["data"].get("file", "").startswith("file"):
            #         file_url = item["data"].get("url") or item["data"].get("file")
            #         file_name = (tmp := file_url.split("/"))[-1] or tmp[-2] or f"_tmp_file_{int(time.time())}"
            #         message[length]["data"]["file_id"] = file.create_url_cache(file_name, file_url)
            #     elif item["data"]["file"].startswith("base64://"):
            #         message[length]["data"]["file_id"] = (
            #             await file.upload_file(
            #                 "data",
            #                 f"_tmp_file_{int(time.time())}",
            #                 data=item["data"]["file"].split("base64://")[1]
            #             )
            #         )["data"]["file_id"]

    return message
           
async def translate_v12_message_to_v11(v12_message: list) -> list:
    message = v12_message.copy()
    for i in range(len(message)):
        match message[i]["type"]:
            case "mention":
                message[i]["type"] = "at"
                message[i]["data"]["qq"] = int(message[i]["data"]["user_id"])
            case "mention_all":
                message[i]["type"] = "at"
                message[i]["data"]["qq"] = "all"
            case "reply":
                message[i]["data"]["id"] = int(message[i]["data"]["message_id"])
            case "image" | "voice" | "audio" | "video":
                with open(".cache/cached_url.json", "r", encoding="utf-8") as f:
                    cached_url = json.load(f)
                if message[i]["data"]["file_id"] in cached_url:
                    message[i]["data"]["file"] = cached_url[message[i]["data"]["file_id"]]["name"]
                    message[i]["data"]["url"] = cached_url[message[i]["data"]["file_id"]]["name"]
                else:
                    message[i]["data"]["file"] = await file.get_file_name_by_id(message[i]["data"]["file_id"])
                    message[i]["data"]["url"] = f'file://{file.get_file_path(message[i]["data"]["file"])}'
    return message

