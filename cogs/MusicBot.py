import discord
from discord.ext import commands
import yt_dlp
import asyncio
import urllib.parse, urllib.request, re

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.queues = {}
        self.voice_clients = {}
        self.youtube_base_url = 'https://www.youtube.com/'
        self.youtube_results_url = self.youtube_base_url + 'results?'
        self.youtube_watch_url = self.youtube_base_url + 'watch?v='
        self.yt_dl_options = {"format": "bestaudio/best"}
        self.ytdl = yt_dlp.YoutubeDL(self.yt_dl_options)
        self.ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn -filter:a "volume=0.25"'}

    async def play_next(self, ctx):
        """Play the next song in the queue if one exists."""
        # Check if the queue for the current guild is not empty
        if self.queues.get(ctx.guild.id) and len(self.queues[ctx.guild.id]) > 0:
            link = self.queues[ctx.guild.id].pop(0)
            await self.play(ctx, link=link)
        else:
            print(f"No songs left in the queue for guild {ctx.guild.id}")

    @commands.command(name="skip")
    async def skip(self, ctx):
        """Skip the currently playing song and play the next one in the queue."""
        try:
            # Check if a song is currently playing
            if ctx.guild.id in self.voice_clients and self.voice_clients[ctx.guild.id].is_playing():
                # Stop the current song
                self.voice_clients[ctx.guild.id].stop()
                print(f"Skipping song in guild {ctx.guild.id}")

                # Play the next song
                await self.play_next(ctx)
                await ctx.send("Song skipped.")
            else:
                await ctx.send("No song is currently playing.")
        except Exception as e:
            print(f"Error skipping song: {e}")
            await ctx.send("An error occurred while trying to skip the song.")

    @commands.command(name="leave")
    async def leave(self, ctx):
        """Make the bot leave the voice channel and stop playing music."""
        try:
            # Check if the bot is connected to a voice channel
            if ctx.guild.id in self.voice_clients and self.voice_clients[ctx.guild.id].is_connected():
                # Stop the current song
                self.voice_clients[ctx.guild.id].stop()
                print(f"Leaving the voice channel for guild {ctx.guild.id}")

                # Disconnect from the voice channel
                await self.voice_clients[ctx.guild.id].disconnect()
                # Remove the voice client from the dictionary
                del self.voice_clients[ctx.guild.id]

                # Clear the queue for the guild
                if ctx.guild.id in self.queues:
                    del self.queues[ctx.guild.id]

                await ctx.send("Disconnected from the voice channel and cleared the queue.")
            else:
                await ctx.send("I'm not connected to a voice channel.")
        except Exception as e:
            print(f"Error leaving the voice channel: {e}")
            await ctx.send("An error occurred while trying to leave the voice channel.")

    @commands.command(name="play")
    async def play(self, ctx, *, link):
        """Play a song or add it to the queue if one is already playing."""
        try:
            # Check if the bot is already connected to the voice channel
            try:
                if ctx.guild.id not in self.voice_clients or not self.voice_clients[ctx.guild.id].is_connected():
                    # If not, connect to the voice channel
                    self.voice_client = await ctx.author.voice.channel.connect()
                    self.voice_clients[ctx.guild.id] = self.voice_client
            except Exception as e:
                print(f"Error connecting to the voice channel: {e}")
                await ctx.send('Failed to connect to the voice channel.')

            # Check if the link is a YouTube URL, if not, perform a search
            try:
                if self.youtube_base_url not in link:
                    query_string = urllib.parse.urlencode({
                        'search_query': link
                    })
                    content = urllib.request.urlopen(self.youtube_results_url + query_string)
                    search_results = re.findall(r'/watch\?v=(.{11})', content.read().decode())
                    
                    if not search_results:
                        print("No results found from the search.")
                        await ctx.send("No results found for your search.")
                        return
                    
                    link = self.youtube_watch_url + search_results[0]
            except Exception as e:
                print(f"Error searching YouTube: {e}")
                await ctx.send('An error occurred while searching YouTube.')

            # Extract audio data from the YouTube link
            try:
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(link, download=False))
                song = data['url']
            except Exception as e:
                print(f"Error extracting audio data from the YouTube link: {e}")
                await ctx.send("An error occurred while extracting audio from the YouTube link.")
                return

            # Play the song
            try:
                player = discord.FFmpegOpusAudio(song, **self.ffmpeg_options)

                # If no song is playing, start playing this song
                if not self.voice_clients[ctx.guild.id].is_playing():
                    self.voice_clients[ctx.guild.id].play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
                else:
                    # If a song is playing, add this song to the queue
                    if ctx.guild.id not in self.queues:
                        self.queues[ctx.guild.id] = []
                    self.queues[ctx.guild.id].append(link)
                    await ctx.send(f'Added to queue: {link}')
                    print(self.queues[ctx.guild.id])
            except Exception as e:
                print(f"Error playing the song: {e}")
                await ctx.send("An error occurred while trying to play the song.")
                
        except Exception as e:
            print('Exception in play: ')
            print(e)
            await ctx.send('An error occurred while trying to play the song.')

async def setup(bot):
    await bot.add_cog(MusicBot(bot))
