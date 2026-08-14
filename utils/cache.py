"""缓存目录工具与过期清理

- 缓存目录可通过 system.cache_dir 配置（默认 .cache），所有模块统一从这里取路径
- 缓存过期清理：system.cache 下的 files_ttl / url_cache_ttl / db_ttl（秒），
  0 或缺省表示不过期（默认不清理）；start_cleanup_loop() 按 cleanup_interval 周期执行
"""
import os
import time
import json
import asyncio
from .config import config
from .logger import get_logger

logger = get_logger()


def get_cache_dir() -> str:
    """返回缓存目录（system.cache_dir，默认 .cache），确保目录存在"""
    cache_dir = config["system"].get("cache_dir", ".cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def files_dir() -> str:
    """文件缓存目录（cache_dir/files），确保目录存在"""
    directory = os.path.join(get_cache_dir(), "files")
    os.makedirs(directory, exist_ok=True)
    return directory


def file_list_path() -> str:
    """文件列表索引路径"""
    return os.path.join(get_cache_dir(), "file_list.json")


def cached_url_path() -> str:
    """URL 缓存索引路径"""
    return os.path.join(get_cache_dir(), "cached_url.json")


def get_file_path(file_name: str) -> str:
    """返回缓存文件的绝对路径"""
    return os.path.abspath(os.path.join(files_dir(), file_name))


def cache_config() -> dict:
    """system.cache 配置段（不存在时返回空 dict）"""
    return config["system"].get("cache", {}) or {}


async def clean_expired() -> None:
    """按 system.cache 的 TTL 清理过期缓存；TTL=0（默认）表示不过期不清理"""
    cache = cache_config()
    now = int(time.time())

    # 1) 文件缓存（files/ 目录下全部文件 + cache_dir 根下的 node.* 合并转发节点文件，按 mtime）
    files_ttl = int(cache.get("files_ttl", 0) or 0)
    if files_ttl > 0:
        try:
            for path in (
                os.path.join(files_dir(), f) for f in os.listdir(files_dir())
            ):
                if now - int(os.path.getmtime(path)) > files_ttl:
                    os.remove(path)
                    logger.info(f"已清理过期缓存文件：{path}")
            for name in os.listdir(get_cache_dir()):
                if not name.startswith("node."):
                    continue
                path = os.path.join(get_cache_dir(), name)
                if now - int(os.path.getmtime(path)) > files_ttl:
                    os.remove(path)
                    logger.info(f"已清理过期节点缓存：{path}")
        except Exception as e:
            logger.warning(f"清理过期文件缓存失败：{e}")

    # 2) URL 缓存索引（条目含 time 字段才参与过期判断，旧条目视为不过期）
    url_ttl = int(cache.get("url_cache_ttl", 0) or 0)
    if url_ttl > 0:
        try:
            with open(cached_url_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
            keep = {}
            for file_id, item in data.items():
                created = item.get("time") if isinstance(item, dict) else None
                if created is None or now - int(created) <= url_ttl:
                    keep[file_id] = item
            if len(keep) != len(data):
                with open(cached_url_path(), "w", encoding="utf-8") as f:
                    json.dump(keep, f)
                logger.info(f"已清理过期 URL 缓存索引（{len(data) - len(keep)} 条）")
        except Exception as e:
            logger.warning(f"清理过期 URL 缓存失败：{e}")

    # 3) 本地消息数据库（延迟导入避免循环依赖）
    db_ttl = int(cache.get("db_ttl", 0) or 0)
    if db_ttl > 0:
        from .db import cleanup_expired_messages

        try:
            await cleanup_expired_messages(db_ttl)
        except Exception as e:
            logger.warning(f"清理过期消息记录失败：{e}")


async def start_cleanup_loop() -> None:
    """后台自动清理循环：按 system.cache.cleanup_interval（秒，默认 3600）周期执行"""
    interval = int(cache_config().get("cleanup_interval", 3600) or 3600)
    if interval <= 0:
        return
    while True:
        await asyncio.sleep(interval)
        await clean_expired()
