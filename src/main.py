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
async def commands(ctx):
    print('In "hello" function')
    embeded_msg = discord.Embed(title="List of commands", description="", color=discord.Color.green())
    embeded_msg.add_field(name="Play a track", value="!play <link>", inline=False)
    await ctx.send(embed=embeded_msg)


bot.run(bot_token)

