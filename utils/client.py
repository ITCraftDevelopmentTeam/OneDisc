from utils.config import config
from discord import Client
import discord.http
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
#discord.http.disable_ssl = config["system"].get("disable_ssl", False)

client = Client(
    intents=intents,
    proxy=config["system"]["proxy"]
)
tree = app_commands.CommandTree(client)
