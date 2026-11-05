"""actions/v12/file.py 文件 ID 查询的回归测试（issue #138）

issue #138：get_file_name_by_id 中把 file_list_path 误写成 ffile_list_path，
调用 send_msg 发送 image 时抛 NameError，表情包管理器因此发送失败。
"""
import json

from actions.v12.file import get_file_name_by_id, register_saved_file
from utils.cache import cached_url_path, file_list_path


def _reset_cache(file_list: dict, cached_url: dict | None = None) -> None:
    with open(file_list_path(), "w", encoding="utf-8") as f:
        json.dump(file_list, f)
    with open(cached_url_path(), "w", encoding="utf-8") as f:
        json.dump(cached_url or {}, f)


async def test_get_file_name_by_id_命中文件列表():
    _reset_cache({}, {})
    file_id = register_saved_file("meme.png", "file-id-138")

    assert await get_file_name_by_id(file_id) == "meme.png"


async def test_get_file_name_by_id_未知ID返回None():
    _reset_cache({}, {})

    assert await get_file_name_by_id("not-exist") is None
