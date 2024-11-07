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
    async def join(self, ctx, channel: discord.VoiceChannel = None):
        # Check if the user provided a channel or is in one
        if channel is None:
            if ctx.author.voice:  # Ensure the user is in a voice channel
                channel = ctx.author.voice.channel
            else:
                await ctx.send("You must be in a voice channel or specify one!")
                return

        # Get the current voice client for the guild, if any
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if voice is None or not voice.is_connected():
            # Connect to the voice channel
            await channel.connect()
            await ctx.send(f"Bot has joined {channel.name}")
        else:
            # Move to the new voice channel if already connected
            await voice.move_to(channel)
            await ctx.send(f"Bot has moved to {channel.name}")



    @commands.command(name='leave', help='Leaves the voice channel')
    async def leave(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.disconnect()
            await ctx.send('Disconnected from the voice channel.')
        else:
            await ctx.send('I am not connected to any voice channel.')

    @commands.command(name='play', help='Plays a song from a YouTube URL')
    async def play(self, ctx, url: str):
        print(f"Received play command with URL: {url}")
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        # Ensure the bot is connected to a voice channel
        if not voice or not voice.is_connected():
            print("Bot is not connected to a voice channel; invoking join command.")
            await ctx.invoke(self.join)
        else:
            print("Bot is already connected to a voice channel.")

        # Attempt to retrieve audio URL
        song_url = await self.get_audio(url)
        if song_url:
            print(f"Retrieved audio URL: {song_url}")
            self.queue.append(song_url)
            print(f"Song added to queue. Queue length is now {len(self.queue)}.")
            if not self.voice_client.is_playing():
                print("Voice client is not playing; calling play_next_song.")
                await self.play_next_song(ctx)
            else:
                print("Voice client is already playing.")
        else:
            await ctx.send('Could not fetch the song.')
            print("Failed to fetch the song URL.")

    async def get_audio(self, url):
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }

        try:
            print("Attempting to extract audio using youtube_dl.")
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info:
                    video = info['entries'][0]
                else:
                    video = info
                print(f"Audio extraction successful. URL: {video['url']}")
                return video['url']
        except Exception as e:
            print(f"Error extracting audio from URL: {e}")
            return None

    async def play_next_song(self, ctx):
        if self.queue:
            song_url = self.queue.pop(0)
            print(f"Attempting to play next song in queue: {song_url}")
            self.voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

            if self.voice_client:
                try:
                    print("Voice client is ready. Starting audio playback.")
                    self.voice_client.play(
                        discord.FFmpegPCMAudio(song_url),
                        after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next_song(ctx), self.bot.loop)
                    )
                    await ctx.send(f'Now playing: {song_url}')
                    print("Playback started successfully.")
                except Exception as e:
                    print(f"Error during playback: {e}")
                    await ctx.send('An error occurred while trying to play the song.')
            else:
                print("No voice client available to play the song.")
                await ctx.send("I'm not connected to any voice channel.")
        else:
            print("Queue is empty; no more songs to play.")
            await ctx.send('No more songs in the queue.')

async def setup(bot):
    await bot.add_cog(MusicBot(bot))
