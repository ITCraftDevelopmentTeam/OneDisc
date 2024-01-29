from .. import register_action
import json
import httpx
from ..v12.file import get_file_name_by_id
from utils import return_object
from pathlib import Path

@register_action("v11")
async def get_image(file: str) -> dict:
    file_name = await get_file_name_by_id(file.split("_")[0])
    if not file_name:
        return return_object.get(31001, f"文件 {file} 不存在")
    return return_object.get(
        0,
        file=Path(".cache/file").joinpath(file_name).as_posix()
    )
