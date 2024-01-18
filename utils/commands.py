import traceback
from typing import Awaitable, Callable, Optional, cast
from .logger import get_logger
from .event.command_event import on_command
from .client import tree, client
from .config import config
import json
from discord import Interaction, Object

logger = get_logger()
try:
    commands = cast(list[dict], json.load(open("commands.json")))
except FileNotFoundError:
    commands = []
except json.JSONDecodeError:
    logger.error(f"无法读取指令列表: {traceback.format_exc()}")
    commands = []
deferred_sessions: dict[str, tuple[Callable[..., Awaitable[int]], Callable[[], Awaitable[None]]]] = {}

async def handle_command(interaction: Interaction, args: Optional[str]) -> None:
    logger.debug(f"收到命令: {interaction.command} ({args=})")
    if not interaction.command:
        return
    if not (user := client.get_user(interaction.user.id)):
        return    
    
    content = f"{config['system'].get('prefix', '/')}{interaction.command.name} {args}"
    await interaction.response.defer()
    session_id = str(interaction.channel_id or interaction.user.id)
    if session_id in deferred_sessions:
        await deferred_sessions[session_id][1]()

    def remove() -> None:
        deferred_sessions.pop(session_id, None)

    async def followup(**kwargs) -> int:
        await interaction.followup.send(**kwargs)
        remove()
        return interaction.followup.id
    
    async def abandon() -> None:
        # 我不知道有没有用，但是它能跑
        await interaction.followup.send(config['system'].get('command_timeout_message', 'timeout'))
        remove()

    deferred_sessions[session_id] = (followup, abandon)

    await on_command(
        interaction.guild,
        interaction.created_at,
        content,
        interaction.channel.id if interaction.channel is not None else -1,
        user
    )


def register_commands() -> None:
    for command in commands:
        if "guild" in command:
            command["guild"] = Object(id=int(command["guild"]))
        tree.command(**command)(handle_command)
        logger.debug(f"已注册指令: {command['name']} (guild={command.get('guild')})")

register_commands()
