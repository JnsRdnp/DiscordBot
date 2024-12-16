import discord
from discord.ext import commands
import yt_dlp
import asyncio
import urllib.parse, urllib.request, re
import inspect

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.youtube_base_url = 'https://www.youtube.com/'
        self.youtube_results_url = self.youtube_base_url + 'results?'
        self.youtube_watch_url = self.youtube_base_url + 'watch?v='
        self.yt_dl_options = {"format": "bestaudio/best"}
        self.ytdl = yt_dlp.YoutubeDL(self.yt_dl_options)
        self.ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn -filter:a "volume=0.25"'}
        self.bot_messages = {}

    @commands.command(name="play")
    async def play(self, ctx, *, link):
        current_function = inspect.currentframe().f_code.co_name
        print(f"Executing function: {current_function}")
        """Play a song or add it to the queue if one is already playing."""

        # Connect to the voice channel if not already connected
        await self.connect_to_voice_channel(ctx)

        # Search YouTube if the link is not a direct URL
        link = await self.search_youtube(ctx, link)
        if not link:
            return

        # Extract audio from the YouTube link
        song = await self.extract_audio(link)
        if not song:
            await ctx.send("An error occurred while extracting audio.")
            return

        # Play the song or add it to the queue
        await self.play_song(ctx, song)
                

    @commands.command(name="skip")
    async def skip(self, ctx):
        current_function = inspect.currentframe().f_code.co_name
        print(f"Executing function: {current_function}")
        """Skip the currently playing song and play the next one in the queue."""
        try:
            # Ensure the bot is connected and playing a song
            if ctx.voice_client and ctx.voice_client.is_playing():
                # Stop the current song
                ctx.voice_client.stop()
                print(f"Skipping song in guild {ctx.guild.id}")
                
                # Notify the user
                await self.send_and_append(ctx, "Song skipped")
                
                # Call after_song_finish to handle the next song
            else:
                await self.send_and_append(ctx, "Nothing is currently playing")
        except Exception as e:
            print(f"Error skipping song: {e}")
            await self.send_and_append(ctx, "An error occurred while trying to skip the song")


    @commands.command(name="leave")
    async def leave(self, ctx):
        current_function = inspect.currentframe().f_code.co_name
        print(f"Executing function: {current_function}")
        """Make the bot leave the voice channel and stop playing music."""
        try:
            # Ensure the bot is connected to a voice channel
            if ctx.voice_client and ctx.voice_client.is_connected():
                # Stop any playing music
                ctx.voice_client.stop()

                # Log the disconnection
                print(f"Leaving the voice channel for guild {ctx.guild.id}")
                
                # Disconnect from the voice channel
                await ctx.voice_client.disconnect()

                # Clear the guild's queue and bot messages
                if ctx.guild.id in self.queues:
                    del self.queues[ctx.guild.id]

                if ctx.guild.id in self.bot_messages:
                    for msg in self.bot_messages[ctx.guild.id]:
                        await msg.delete()
                    del self.bot_messages[ctx.guild.id]

                # Notify the user
                await self.send_and_append(ctx, "Disconnected from the voice channel and cleared the queue.")
            else:
                await self.send_and_append(ctx, "I'm not connected to a voice channel.")
        except Exception as e:
            print(f"Error leaving the voice channel: {e}")
            await self.send_and_append(ctx, "An error occurred while trying to leave the voice channel.")

        await ctx.message.delete()


    async def send_and_append(self, ctx, message):
        current_function = inspect.currentframe().f_code.co_name
        print(f"Executing function: {current_function}")
        try:
            # Ensure the bot_messages dictionary has an entry for the guild
            if ctx.guild.id not in self.bot_messages:
                self.bot_messages[ctx.guild.id] = []

            # Send the message and append it to the guild's list
            bot_message = await ctx.send(message)
            self.bot_messages[ctx.guild.id].append(bot_message)

        except Exception as e:
            print(f"An error occurred in send and append: {e}")


    async def connect_to_voice_channel(self, ctx):
        current_function = inspect.currentframe().f_code.co_name
        print(f"Executing function: {current_function}")
        """Connect to the voice channel if not already connected."""
        try:
            # Check if the bot is not already connected to a voice channel
            if not ctx.voice_client or not ctx.voice_client.is_connected():
                # Connect to the voice channel
                await ctx.author.voice.channel.connect()

        except Exception as e:
            print(f"Error connecting to the voice channel: {e}")
            await ctx.send('Failed to connect to the voice channel.')

    async def search_youtube(self, ctx, link):
        current_function = inspect.currentframe().f_code.co_name
        print(f"Executing function: {current_function}")
        """Search YouTube for the link if it is not a direct URL."""
        
        # Try to process the link and perform the search
        try:
            if self.youtube_base_url not in link:
                query_string = urllib.parse.urlencode({'search_query': link})
                content = urllib.request.urlopen(self.youtube_results_url + query_string)
        except Exception as e:
            print(f"Error processing the YouTube search: {e}")
            await ctx.send('An error occurred while processing the search query.')
            return None
        
        # Try to extract the search results from the content
        try:
            search_results = re.findall(r'/watch\?v=(.{11})', content.read().decode())
            
            if not search_results:
                print("No results found from the search.")
                await ctx.send("No results found for your search.")
                return None
            
            link = self.youtube_watch_url + search_results[0]
        except Exception as e:
            print(f"Error extracting search results: {e}")
            await ctx.send('An error occurred while extracting YouTube results.')
            return None

        return link
    
    async def extract_audio(self, link):
        current_function = inspect.currentframe().f_code.co_name
        print(f"Executing function: {current_function}")
        """Extract audio URL from the YouTube link."""
        
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(link, download=False))
            song = data['url']
            return song
        except Exception as e:
            print(f"Error extracting audio data from the YouTube link: {e}")
            return


    async def play_song(self, ctx, song):
        current_function = inspect.currentframe().f_code.co_name
        print(f"Executing function: {current_function}")
        """Play the song or add it to the queue."""
        player = discord.FFmpegOpusAudio(song, **self.ffmpeg_options)

        # Ensure a queue exists for the guild
        if ctx.guild.id not in self.queues:
            self.queues[ctx.guild.id] = []

        # If no song is playing, start playing this song
        if not ctx.voice_client.is_playing():
            ctx.voice_client.play(player, loop=self.bot.loop, after=lambda e: self.after_song_finish(ctx))
        else:
            # If a song is playing, add this song to the queue
            self.queues[ctx.guild.id].append(song)
            await ctx.send(f'Added to queue: {song}')


    async def after_song_finish(self, ctx):
        current_function = inspect.currentframe().f_code.co_name
        print(f"Executing function: {current_function}")
        """Called when a song finishes playing. Plays the next song in the queue."""
        if len(self.queues[ctx.guild.id]) > 0:
            next_song = self.queues[ctx.guild.id].pop(0)  # Remove the song from the queue before playing
            await self.play_song(ctx, next_song)
        else:
            print("Queue is empty")



async def setup(bot):
    await bot.add_cog(MusicBot(bot))