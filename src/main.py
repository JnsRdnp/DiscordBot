import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv("BOT_TOKEN")


bot = commands.Bot(command_prefix='.', intents=discord.Intents.all())


@bot.event
async def on_ready():
    print("Bot is ready.")



bot.run(bot_token)




