from logger import get_logger
from config import config
from api import register_extra_action
import os.path
import os
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
    json.load(open(".cache/file_list.json", "r", encoding="utf-8"))
except Exception:
    json.dump({}, open(".cache/file_list.json", "w", encoding="utf-8"))

logger = get_logger()

def verify_sha256(contnet: bytes, sha256: str | None) -> bool:
    if sha256 is None:
        return True
    return hashlib.sha256(contnet).hexdigest() == sha256

async def upload_file_from_url(
        url: str,
        headers: dict,
        name: str,
        proxy: str | None,
        sha256: str | None,
        retry_count: int = 0
) -> bool:
    async with httpx.AsyncClient(proxies=proxy) as client:
        response = await client.get(url, headers=headers)    
        if response.status_code == 200 and verify_sha256(response.content, sha256):
            with open(f".cache/{name}", "wb") as f:
                f.write(response.content)
            return True
    logger.warning(f"下载文件 {url} (到 {name}) 失败：({response.status_code}) 远程返回错误或校验失败")
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
        with open(f".cache/{name}", "wb") as f:
            f.write(base64.b64decode(data))
        return True, ""
    except Exception as e:
        logger.warning(f"向 {name} 写入 data 失败：{e}")
        return False, str(e)


def new_file(name: str) -> str:
    file_id = str(uuid.uuid1())
    with open(".cache/file_list.json", "r", encoding="utf-8") as f:
        file_list = json.load(f)
    file_list[file_id] = name
    with open(".cache/file_list.json", "w", encoding="utf-8") as f:
        json.dump(file_list, f, ensure_ascii=False, indent=4)
    return file_id

def upload_file_from_path(name: str, path: str) -> tuple[bool, str]:
    try:
        with open(path, "rb") as from_f:
            with open(f".cache/{name}", "wb") as to_f:
                to_f.write(from_f.read())
        return True, ""
    except Exception as e:
        logger.warning(f"从 {path} 获取文件 (到 {name}) 失败：{e}")
        return False, str(e)
            
@register_extra_action("upload_file")
async def upload_file(
        type: str,
        name: str,
        url: str,
        headers: dict = {},
        path: str | None = None,
        data: str | None = None,
        sha256: str | None = None,
        proxy: str | None = None
) -> dict:
    match type:

        case "url":
            if url == None:
                return return_object.get(10003, "url 参数为空")
            status = await upload_file_from_url(
                url,
                headers, 
                name, 
                proxy, 
                sha256, 
                config["system"].get("download_max_retry_count", 0)
            )
            if status:
                return return_object.get(status)
            return return_object.get(
                0,
                file_id=new_file(name),
            )

        case "name":
            if path == None:
                return return_object.get(10003, "path 参数为空")
            status = upload_file_from_path(name, path)
            if not status[0]:
                return return_object.get(32001, status[1])
            return return_object.get(0, file_id=new_file(name))

        case "data":
            if data == None:
                return return_object.get(10003, "data 参数为空")
            status = upload_file_from_data(name, data)
            if not status[0]:
                return return_object.get(32001, status[1])
            return return_object.get(0, file_id=new_file(name))
        
        case _:
            return return_object.get(10003, f"无效的 type 参数：{type}")

def get_file_name_by_id(file_id: str) -> str:
    """
    根据文件 ID 获取文件名
    """
    with open(f".cache/file_list.json", "r", encoding="utf-8") as f:
        file_list = json.load(f)
    return file_list.get(file_id)


@register_extra_action("get_file")
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
                path=os.path.abspath(f".config/{file}")
            )
        # TODO 返回 sha256
        
        case "data":
            with open(f".config/{file}", "rb") as f:
                return return_object.get(
                    0,
                    name=file,
                    data=base64.b64encode(f.read()).decode("utf-8")
                )