import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.queue = []

    @commands.command(name='join', help='Joins the voice channel')
    async def join(self, ctx):
        if self.voice_client and self.voice_client.is_connected():
            await ctx.send(f'Already connected to {self.voice_client.channel.name}')
            return

        await ctx.send('Joining voice channel...')
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            self.voice_client = await channel.connect()
            await ctx.send(f'Joined {channel.name}')
        else:
            await ctx.send('You must join a voice channel first!')

    @commands.command(name='leave', help='Leaves the voice channel')
    async def leave(self, ctx):
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
            await ctx.send('Disconnected from the voice channel.')
        else:
            await ctx.send('I am not connected to any voice channel.')

    @commands.command(name='play', help='Plays a song from a YouTube URL')
    async def play(self, ctx, url: str):
        if not self.voice_client:
            await ctx.invoke(self.join)

        song = await self.get_audio(url)
        if song:
            self.queue.append(song)
            if not self.voice_client.is_playing():
                await self.play_next_song(ctx)
        else:
            await ctx.send('Could not fetch the song.')

    async def get_audio(self, url):
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegAudioConvertor',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'quiet': True,
        }

        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info:
                    video = info['entries'][0]
                else:
                    video = info
                audio_url = video['formats'][0]['url']
                return audio_url
        except Exception as e:
            print(f"Error extracting audio from URL: {e}")
            return None

    async def play_next_song(self, ctx):
        if len(self.queue) > 0:
            song_url = self.queue.pop(0)
            if song_url:
                self.voice_client.play(discord.FFmpegPCMAudio(song_url), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next_song(ctx), self.bot.loop))
                await ctx.send(f'Now playing: {song_url}')
            else:
                await ctx.send('Error playing the song.')
        else:
            await ctx.send('No more songs in the queue.')

async def setup(bot):
    await bot.add_cog(MusicBot(bot))
