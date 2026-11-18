"""OneBot V11 反向 WebSocket 重连：并发重连时不得重复建立连接"""
import asyncio
from types import SimpleNamespace

import pytest

import network.v11.ws_reverse as ws_reverse
from websockets.legacy.server import serve


@pytest.fixture(autouse=True)
def stub_discord_client(monkeypatch):
    # 未登录时 discord.Client.user 为 None，构造 X-Self-ID 头会失败
    monkeypatch.setattr(
        ws_reverse, "client", SimpleNamespace(user=SimpleNamespace(id=1))
    )


@pytest.fixture
async def reverse_ws_server():
    active = set()

    async def handler(websocket):
        active.add(websocket)
        try:
            async for _ in websocket:
                pass
        except Exception:
            pass
        finally:
            active.discard(websocket)

    server = await serve(handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        yield f"ws://127.0.0.1:{port}", active
    finally:
        for websocket in list(active):
            await websocket.close()
        server.close()
        await server.wait_closed()


async def wait_for(predicate, timeout: float = 2.0, interval: float = 0.01) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while not predicate():
        if asyncio.get_running_loop().time() > deadline:
            raise AssertionError("等待条件超时")
        await asyncio.sleep(interval)


async def drop_connection(active: set) -> None:
    for websocket in list(active):
        await websocket.close()
    await wait_for(lambda: not active)


async def test_single_reconnect_keeps_one_connection(reverse_ws_server):
    url, active = reverse_ws_server
    client = ws_reverse.EventClient({"url": url, "reconnect_interval": 20})

    await client.reconnect()
    await wait_for(lambda: len(active) == 1)

    await drop_connection(active)
    await wait_for(lambda: not client.is_ready())

    await client.reconnect()
    await wait_for(lambda: len(active) == 1)
    assert len(active) == 1


async def test_concurrent_reconnect_keeps_one_connection(reverse_ws_server):
    url, active = reverse_ws_server
    client = ws_reverse.EventClient({"url": url, "reconnect_interval": 20})

    await client.reconnect()
    await wait_for(lambda: len(active) == 1)

    await drop_connection(active)
    await wait_for(lambda: not client.is_ready())

    # 模拟 close() 因 close_timeout 卡住、且各调用完成时间不同：
    # 旧实现会把等待 close 的任务错开成多次 connect()，每次各建一条连接。
    original_close = client.ws.close
    delays = [0.0, 0.05, 0.1, 0.15]

    async def slow_close(*args, **kwargs):
        await asyncio.sleep(delays.pop(0) if delays else 0.2)
        return await original_close(*args, **kwargs)

    client.ws.close = slow_close

    await asyncio.gather(*(client.reconnect() for _ in range(4)))
    await asyncio.sleep(0.1)

    assert len(active) == 1
