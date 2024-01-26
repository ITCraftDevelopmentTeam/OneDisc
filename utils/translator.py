from utils.config import config
import json
import time
import actions.v12.file as file
from utils.client import client
import actions.v11.basic as basic
from utils.message.v11.parser import parse_string_to_array
from utils.logger import get_logger

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
    del event["id"]
    # if event[f"{event['post_type']}_type"] == "channel":
    #     event[f"{event['post_type']}_type"] = "group"
    if not event["sub_type"]:
        del event["sub_type"]
    if "channel_id" in event.keys():
        event["group_id"] = int(event.pop("channel_id"))
        del event["guild_id"]
    # 类型替换
    for key in event.keys():
        if key.endswith("_id"):
            event[key] = int(event[key])
    if event["post_type"] == "notice":
        match event["notice_type"]:
            case "group_message_delete":
                event["notice_type"] = "group_recall"
                del event["sub_type"]
            case "private_message_delete":
                event["notice_type"] = "friend_recall"
    elif event["post_type"] == "message":
        event["raw_message"] = event.pop("alt_message")
        event["sender"] = {
            "user_id": event["user_id"]
        }
        event["message"] = await translate_v12_message_to_v11(event["message"])

        if (sender := client.get_user(event["user_id"])):
            event["sender"]["nickname"] = sender.name
        
        if event["message_type"] == "private":
            event["sub_type"] = config["system"].get("default_message_sub_type", "friend")
            event["font"] = 0
        
        elif event["message_type"] == "group":
            event["sub_type"] = "normal"
            event["anonymous"] = None
            event["font"] = 0
            if (sender := client.get_channel(event["group_id"]).guild.get_member(event["user_id"])):
                event["sender"]["card"] = sender.nick
                event["sender"]["role"] = basic.get_role(sender)

        
    elif event["post_type"] == "meta_event" and event["meta_event_type"] == "heartbeat":
        event["status"] = (await basic.get_status())["data"]
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
    if not isinstance(_message, list):
        message = parse_string_to_array(_message)
        # 这样似乎可以解决，Issue #1
    else:
        message = _message.copy()
    i = -1
    for item in message:
        i += 1
        if item["type"] == "face":
            item = message[i] = {
                "type": "image",
                "data": {
                    "file": f"https://raw.githubusercontent.com/richardchien/coolq-http-api/master/docs/qq-face/{item['data']['id']}.{'png' if config['system'].get('use_static_face') else 'gif'}"
                }
            }
        elif item["type"] in ["channel", "emoji", "role", "timestamp", "navigation", "markdown"]:
            message[i]["type"] = item["type"] = f'discord.{item["type"]}'
        match item["type"]:
            case "location":
                message[i] = {
                    "type": "location",
                    "data": {
                        "latitude": item["data"]["lat"],
                        "longitude": item["data"]["lon"],
                        "title": item["data"].get("title", "位置分享"),
                        "content": item["data"].get("content", config["system"].get("location_default_content", "机器人向你发送了一个位置"))
                    }
                }
            case "at":
                if item["data"]["qq"] != "all":
                    message[i]["type"] = "mention"
                    message[i]["data"]["user_id"] = message[i]["data"].pop("qq")
                else:
                    message[i]["type"] = "mention_all"
                    message[i]["data"] = {}
            case "reply":
                message[i]["data"]["message_id"] = str(message[i]["data"].pop("id"))
            case "image" | "record" | "video":
                if item["data"]["file"].startswith("http"):
                    file_name = (splited_url := item["data"]["file"].split("/"))[-1] or splited_url[-2] or f"{int(time.time())}"
                    message[i]["data"]["file_id"] = (await file.upload_file(
                        "url",
                        file_name,
                        item["data"]["file"]
                    ))["data"]["file_id"]
                elif item["data"]["file"].startswith("file"):
                    file_name = (splited_url := item["data"]["file"].split("/"))[-1] or splited_url[-2] or f"{int(time.time())}"
                    message[i]["data"]["file_id"] = (await file.upload_file(
                        "name",
                        file_name,
                        path=item["data"]["file"][7:]
                    ))["data"]["file_id"]
                elif item["data"]["file"].startswith("base64"):
                    message[i]["data"]["file_id"] = (await file.upload_file(
                        "data",
                        f"{int(time.time())}{config['system'].get('base64_default_image_type', '.png')}",
                        data=item["data"]["file"][9:]
                    ))["data"]["file_id"]
                if item["type"] == "record":
                    item["type"] = "voice"
            case "discord.channel":
                message[i]["type"] = "discord.channel"
                message[i]["data"]["channel_id"] = str(message[i]["data"]["channel_id"])
            case "discord.role":
                message[i]["type"] = "discord.role"
                message[i]["data"]["id"] = str(message[i]["data"]["id"])
            case "share":
                message[i]["type"] = "discord.embed"
                if message[i]["data"].get("content"):
                    message[i]["data"]["description"] = message[i]["data"].pop("content")
                message[i]["data"]["fields"] = [{
                    "name": "URL",
                    "value": message[i]["data"]["url"]
                }]
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
    logger.debug(message)
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
                    message[i]["data"]["file"] = "_".join([
                        message[i]["data"]["file_id"],
                        cached_url[message[i]["data"]["file_id"]]["name"]
                    ])
                    message[i]["data"]["url"] = cached_url[message[i]["data"]["file_id"]]["url"]
                else:
                    message[i]["data"]["file"] = await file.get_file_name_by_id(message[i]["data"]["file_id"])
                    message[i]["data"]["url"] = f'file://{file.get_file_path(message[i]["data"]["file"])}'
            case _:
                if message[i]["type"].startswith("discord."):
                    message[i]["type"] = message[i]["type"][8:]
                    for key in message[i]["data"].keys():
                        if key.endswith("id"):
                            message[i]["data"][key] = int(message[i]["data"][key])
    return message

