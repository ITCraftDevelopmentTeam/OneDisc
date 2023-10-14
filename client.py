from config import config
import discord
import discord.http

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
discord.http.disable_ssl = config["system"].get("disable_ssl", False)

client = discord.Client(intents=intents, proxy=config["system"]["proxy"])