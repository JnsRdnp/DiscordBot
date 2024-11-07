import discord
from discord.ext import commands

class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")


    @commands.command()
    async def commands(self,ctx):
        embeded_msg = discord.Embed(title="List of commands", description="", color=discord.Color.green())
        embeded_msg.add_field(name="Play a track", value="!play <link>", inline=False)
        await ctx.send(embed=embeded_msg)


async def setup(bot):
    await bot.add_cog(Test(bot))






