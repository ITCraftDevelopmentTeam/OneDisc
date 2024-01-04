from typing import Literal
from .logger import get_logger
from .config import config
import version
import httpx

logger = get_logger()


async def get_latest_version() -> dict[str, str]:
    async with httpx.AsyncClient(proxies=config["system"].get("proxy")) as client:
        response = await client.get("https://onedisc.itcdt.top/version.json")
    return response.json()

def get_version_type() -> Literal["beta", "stable"]:
    return "stable" if version.SUB_VER == 0 else "beta"

def parse_version_number(version_number: str) -> tuple[str, int, str]:
    ver = version_number.split(".")
    return ".".join(ver[:3]), int(ver[3]), version_number

async def check_update() -> None:
    latest_version = parse_version_number(
        (await get_latest_version())[get_version_type()]
    )
    if latest_version[0] == version.VERSION and latest_version[1] <= version.SUB_VER:
        return
    logger.info(f"发现新版本: {latest_version[2]}")