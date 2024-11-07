import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv("BOT_TOKEN")


intents = discord.Intents().all()
intents.message_content= True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print("Bot is ready.")

@bot.command()
async def hello(ctx):
    print('In "hello" function')
    await ctx.send("Hello, I am PompivaBot.")


bot.run(bot_token)




