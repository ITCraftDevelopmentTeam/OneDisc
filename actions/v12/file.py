from utils.logger import get_logger
from utils.config import config
from actions import register_action
import utils.checker as checker
import os.path
import os
import traceback
import base64
import uuid
import hashlib
import json
import httpx
import utils.return_object as return_object

try:
    os.makedirs(".cache/files")
except OSError:
    pass

try:
    json.load(open(".cache/file_list.json", "r", encoding="utf-8"))
except Exception:
    json.dump({}, open(".cache/file_list.json", "w", encoding="utf-8"))
try:
    json.load(open(".cache/cached_url.json", "r", encoding="utf-8"))
except Exception:
    json.dump({}, open(".cache/cached_url.json", "w", encoding="utf-8"))

logger = get_logger()

def verify_sha256(content: bytes, sha256: str | None) -> bool:
    if sha256 is None:
        return True
    return hashlib.sha256(content).hexdigest() == sha256

def create_url_cache(name: str, url: str) -> str:
    with open(".cache/cached_url.json", "r", encoding="utf-8") as f:
        cache = json.load(f)
    cache[file_id := create_file_id()] = {
        "name": name,
        "url": url
    }
    with open(".cache/cached_url.json", "w", encoding="utf-8") as f:
        json.dump(cache, f)
    return file_id

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


def create_file_id() -> str:
    file_id = str(uuid.uuid1())
    with open(".cache/file_list.json", "r", encoding="utf-8") as f:
        if file_id in json.load(f).keys():
            return create_file_id()
    with open(".cache/cached_url.json", "r", encoding="utf-8") as f:
        if file_id in json.load(f).keys():
            return create_file_id()
    return file_id


def register_saved_file(name: str, _file_id: str | None = None) -> str:
    file_id = _file_id or create_file_id()
    with open(".cache/file_list.json", "r", encoding="utf-8") as f:
        file_list = json.load(f)
    file_list[file_id] = name
    with open(".cache/file_list.json", "w", encoding="utf-8") as f:
        json.dump(file_list, f, ensure_ascii=False, indent=4)
    return file_id

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
        total_size: int | None = None,
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

@register_action()
async def upload_file(
        type: str,
        name: str,
        url: str | None = None,
        headers: dict = {},
        path: str | None = None,
        data: str | None = None,
        sha256: str | None = None,
        proxy: str | None = None,
        file_id: str | None = None
) -> dict:
    match type:

        case "url":
            checker.check_aruments(name, url)
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
                file_id=register_saved_file(name, file_id)
            )

        case "name":
            checker.check_aruments(name, path)
            is_successful = upload_file_from_path(name, path)
            if not is_successful[0]:
                return return_object.get(32001, is_successful[1])
            return return_object.get(0, file_id=register_saved_file(name))

        case "data":
            checker.check_aruments(name, data)
            is_successful = upload_file_from_data(name, data)
            if not is_successful[0]:
                return return_object.get(32001, is_successful[1])
            return return_object.get(0, file_id=register_saved_file(name))
        
        case _:
            return return_object.get(10003, f"无效的 type 参数：{type}")

async def get_file_name_by_id(file_id: str) -> str | None:
    """
    根据文件 ID 获取文件名
    """
    with open(f".cache/file_list.json", "r", encoding="utf-8") as f:
        file_list = json.load(f)
    if (_id := file_list.get(file_id)):
        return _id
    with open(".cache/cached_url.json", "r", encoding="utf-8") as f:
        cached_url_list = json.load(f)
    if (cache_data := cached_url_list.get(file_id)):
        return await get_file_name_by_id((await upload_file(
            "url",
            cache_data["name"],
            cache_data["url"]
        ))["data"]["file_id"])
    
async def clean_files() -> None:
    with open(".cache/file_list.json", "r", encoding="utf-8") as f:
        file_list = json.load(f)
    with open(".cache/cached_url.json", "r", encoding="utf-8") as f:
        cached_url_list = json.load(f)
    for file_id in list(file_list.keys()):
        if not os.path.exists(get_file_path(file_list[file_id])):
            logger.warning(f"文件 {file_list[file_id]} ({file_id}) 不存在，正在删除")
            file_list.pop(file_id)
            continue
        if file_id in cached_url_list:
            if config["system"].get("cahce_first"):
                logger.warning(f"文件 {file_list[file_id]} ({file_id}) 已被缓存，正在删除储存文件")
                file_list.pop(file_id)
                continue
            else:
                logger.warning(f"文件 {file_list[file_id]} ({file_id}) 已被储存，正在删除缓存索引")
                cached_url_list.pop(file_id)
    logger.debug(file_list)
    logger.debug(cached_url_list)
    with open(".cache/file_list.json", "w", encoding="utf-8") as f:
        json.dump(file_list, f, ensure_ascii=False, indent=4)
    with open(".cache/cached_url.json", "w", encoding="utf-8") as f:
        json.dump(cached_url_list, f, ensure_ascii=False, indent=4)

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
