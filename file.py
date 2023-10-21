from logger import get_logger
from config import config
from api import register_action
import checker
import os.path
import os
import traceback
import base64
import uuid
import hashlib
import json
import httpx
import return_object

try:
    os.makedirs(".cache/files")
except OSError:
    pass

try:
    json.load(open(".cache/.file_list.json", "r", encoding="utf-8"))
except Exception:
    json.dump({}, open(".cache/.file_list.json", "w", encoding="utf-8"))

logger = get_logger()

def verify_sha256(content: bytes, sha256: str | None) -> bool:
    if sha256 is None:
        return True
    return hashlib.sha256(content).hexdigest() == sha256

async def upload_file_from_url(
        url: str,
        headers: dict,
        name: str,
        proxy: str | None,
        sha256: str | None,
        retry_count: int = 0
) -> bool:
    try:
        async with httpx.AsyncClient(proxies=proxy) as client:
            response = await client.get(url, headers=headers)    
            if response.status_code == 200 and verify_sha256(response.content, sha256):
                with open(f".cache/files/{name}", "wb") as f:
                    f.write(response.content)
                return True
        logger.warning(f"下载文件 {url} (到 {name}) 失败：({response.status_code}) 远程返回错误或校验失败")
    except:
        logger.error(f"下载文件 {url} （到 {name}）时出现错误：{traceback.format_exc()}")
    if retry_count <= 0:
        return False
    return await upload_file_from_url(
        url,
        headers,
        name,
        proxy,
        sha256,
        retry_count - 1
    )

def upload_file_from_data(name: str, data: str) -> tuple[bool, str]:
    try:
        with open(f".cache/files/{name}", "wb") as f:
            f.write(base64.b64decode(data))
        return True, ""
    except Exception as e:
        logger.warning(f"向 {name} 写入 data 失败：{e}")
        return False, str(e)


def register_file(data: dict) -> str:
    file_id = str(uuid.uuid1())
    with open(".cache/.file_list.json", "r", encoding="utf-8") as f:
        file_list = json.load(f)
    file_list[file_id] = data
    with open(".cache/.file_list.json", "w", encoding="utf-8") as f:
        json.dump(file_list, f, ensure_ascii=False, indent=4)
    return file_id

def register_saved_file(name: str) -> str:
    return register_file({"type": "saved", "name": name})

def upload_file_from_path(name: str, path: str) -> tuple[bool, str]:
    try:
        with open(path, "rb") as from_f:
            with open(f".cache/files/{name}", "wb") as to_f:
                to_f.write(from_f.read())
        return True, ""
    except Exception as e:
        logger.warning(f"从 {path} 获取文件 (到 {name}) 失败：{e}")
        return False, str(e)


@register_action()
async def get_file_fragmented(
        stage: str,
        file_id: str,
        offset: int | None = None,
        size: int | None = None
) -> dict:
    if not (file_name := await get_file_name_by_id(file_id)):
        return return_object.get(31001, f"文件 {file_id} 不存在")
    with open(get_file_path(file_name), "rb") as f:
        content = f.read()

    match stage:
        case "prepare":
            checker.check_aruments(file_id)
            return return_object.get(
                0,
                name=file_name,
                total_size=len(content),
                sha256=hashlib.sha256(content).hexdigest()
            )
        case "transfer":
            checker.check_aruments(file_id, offset, size)
            return return_object.get(
                0,
                data=base64.b64encode(content[offset:offset + size]).decode("utf-8")    # type: ignore
            )
        case _:
            return return_object.get(10003, f"无效的 stage 参数：{stage}")

uploading_files = {}

@register_action()
async def upload_file_fragmented(
        stage: str,
        name: str | None = None,
        total_size: str | None = None,
        file_id: str | None = None,
        offset: int | None = None,
        data: str | None = None,
        sha256: str | None = None
) -> dict:
    match stage:

        case "prepare":
            checker.check_aruments(name, total_size)
            uploading_files[file_id := str(uuid.uuid1())] = {
                "name": name,
                "content": [0] * total_size
            }
            return return_object.get(
                file_id=file_id
            )
        
        case "transfer":
            checker.check_aruments(file_id, offset, data)
            byte_offset = 0
            for byte in list(base64.b64decode(data)):
                uploading_files[file_id]["content"][offset + byte_offset] = byte
                byte_offset += 1
            return return_object.get()
        
        case "finish":
            checker.check_aruments(file_id, offset, sha256)
            file_name = uploading_files[file_id]['name']
            with open(f".cache/files/{file_name}", "wb") as f:
                f.write(bytes(uploading_files.pop(file_id)["content"]))
            # TODO sha256 校验
            return return_object.get(
                file_id=register_saved_file(file_name)
            )
    return return_object.get(10003, f"无效的 stage 参数：{stage}")

async def clean_cache() -> None:
    with open(f".cache/.file_list.json", "r", encoding="utf-8") as f:
        file_list = json.load(f)
    logger.info("正在清理已经上传的文件")
    for file_id, file_data in list(file_list.items()):
        if file_id not in file_list.keys():
            continue
        match file_data["type"]:
            case "saved":
                if not os.path.exists(get_file_path(file_data["name"])):
                    logger.warning(f"文件 {file_data['name']} ({file_id}, type=name) 未存在于 files 中")
                    file_list.pop(file_id)
                    continue
            case "name":
                if not os.path.exists(file_data["path"]):
                    logger.warning(f"文件 {file_data['name']} ({file_id}, type=name) 未存在于 {file_data['path']} 中")
                    file_list.pop(file_id)
                    continue
            case "url":
                pass        # TODO
        for _id, _file in list(file_list.items()):
            if _file["name"]  == file_data["name"]:
                a = -config["system"].get("file_priority", ["url", "saved", "path"]).index(_file["type"])
                b = -config["system"].get("file_priority", ["url", "saved", "path"]).index(file_data["type"])
                if a >= b:
                    file_list.pop(file_id)
                    continue
                else:
                    file_list.pop(_id)
    for file in os.listdir(".cache/files"):
        for file_data in file_list.values():
            if file_data == file:
                break
        else:
            logger.warning(f"文件 {file} 不存在于索引中！")
            os.remove(file)
    with open(".cache/.file_list.json", "w", encoding="utf-8") as f:
        json.dump(file_list, f)
    logger.info("清理文件完成！")



@register_action()
async def upload_file(
        type: str,
        name: str,
        url: str,
        headers: dict = {},
        path: str | None = None,
        data: str | None = None,
        sha256: str | None = None,
        proxy: str | None = None,
        use_cache: bool | None = None
) -> dict:
    match type:

        case "url":
            checker.check_aruments(name, url)
            if not (config["system"].get("use_cache_for_url", True) or use_cache):
                is_successful = await upload_file_from_url(
                    url,
                    headers, 
                    name, 
                    proxy, 
                    sha256, 
                    config["system"].get("download_max_retry_count", 0)
                )
                if not is_successful:
                    return return_object.get(33000)
                return return_object.get(
                    file_id=register_saved_file(name)
                )
            else:
                return return_object.get(
                    file_id=register_file({
                    "type": "url",
                    "url": url,
                    "name": name,
                    "headers": headers,
                    "proxy": proxy,
                    "sha256": sha256
                }))
               

        case "name":
            checker.check_aruments(name, path)
            if not (config["system"].get("use_cache_for_name", False) or use_cache):
                is_successful = upload_file_from_path(name, path)
                if not is_successful[0]:
                    return return_object.get(32001, is_successful[1]) 
                return return_object.get(0, file_id=register_saved_file(name))
            else:
                return return_object.get(0, file_id=register_file({
                    "type": "name",
                    "name": name,
                    "path": path
                }))

        case "data":
            checker.check_aruments(name, data)
            is_successful = upload_file_from_data(name, data)
            if not is_successful[0]:
                return return_object.get(32001, is_successful[1])
            return return_object.get(0, file_id=register_saved_file(name))
        
        case _:
            return return_object.get(10003, f"无效的 type 参数：{type}")

async def get_file_name_by_id(file_id: str) -> str:
    """
    根据文件 ID 获取文件名
    """
    with open(f".cache/.file_list.json", "r", encoding="utf-8") as f:
        file_list = json.load(f)
    file = file_list.get(file_id)
    if file["type"] != "saved":
        return await get_file_name_by_id((await upload_file(**file, use_cache = False))["data"]["file_id"])
    return file["name"]

def get_file_path(file_name: str) -> str:
    return os.path.abspath(f".cache/files/{file_name}")

@register_action()
async def get_file(file_id: str, type: str) -> dict:
    """
    获取文件
    """
    if not (file := get_file_name_by_id(file_id)):
        return return_object.get(31001, f"文件 {file_id} 不存在")
    
    match type:

        case "url":
            return return_object.get(10004, "未实现的操作：获取文件 URL")       # TODO
        
        case "path":
            return return_object.get(
                0,
                name=file,
                path=os.path.abspath(f".cache/files/{file}")
            )
        # TODO 返回 sha256
        
        case "data":
            with open(f".cache/files/{file}", "rb") as f:
                return return_object.get(
                    0,
                    name=file,
                    data=base64.b64encode(f.read()).decode("utf-8")
                )
        case _:
            return return_object.get(10003, f"无效的 type 参数：{type}")
