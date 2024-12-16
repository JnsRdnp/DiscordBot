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
            return

        # Play the song or add it to the queue
        await self.play_song(ctx, song, link)
                

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
                
                # Call after_song_finish to handle the next song
            else:
                print("Nothing is playing")
        except Exception as e:
            print(f"Error skipping song: {e}")
        await ctx.message.delete()


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

            else:
                print("I'm not connected to a voice channel.")
        except Exception as e:
            print(f"Error leaving the voice channel: {e}")

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
            return None
        
        # Try to extract the search results from the content
        try:
            search_results = re.findall(r'/watch\?v=(.{11})', content.read().decode())
            
            if not search_results:
                print("No results found from the search.")
                return None
            
            link = self.youtube_watch_url + search_results[0]
        except Exception as e:
            print(f"Error extracting search results: {e}")
            return None

        print(f"Returning {link}")
        return link
    
    async def extract_audio(self, link):
        current_function = inspect.currentframe().f_code.co_name
        print(f"Executing function: {current_function}")
        """Extract audio URL from the YouTube link."""
        
        try:
            # Run the blocking ytdl extract_info in the executor
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(link, download=False))
            
            # Extract the song URL from the data
            song = data.get('url')  # Use .get() to prevent KeyError if 'url' isn't found
            if song:
                return song
            else:
                raise ValueError("No audio URL found")
        
        except Exception as e:
            print(f"Error extracting audio data from the YouTube link: {e}")
            return None  # Or handle more gracefully


    async def play_song(self, ctx, song, link):
        current_function = inspect.currentframe().f_code.co_name
        print(f"Executing function: {current_function}")
        """Play the song or add it to the queue."""
        player = discord.FFmpegOpusAudio(song, **self.ffmpeg_options)

        # Ensure a queue exists for the guild
        if ctx.guild.id not in self.queues:
            self.queues[ctx.guild.id] = []

        # If no song is playing, start playing this song
        if not ctx.voice_client.is_playing():
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.after_song_finish(ctx), self.bot.loop))
        else:
            # If a song is playing, add this song to the queue
            self.queues[ctx.guild.id].append({"song": song, "link": link})


    async def after_song_finish(self, ctx):
        current_function = inspect.currentframe().f_code.co_name
        print(f"Executing function: {current_function}")
        """Called when a song finishes playing. Plays the next song in the queue."""
        if len(self.queues[ctx.guild.id]) > 0:
            next_song = self.queues[ctx.guild.id].pop(0)  # Remove the song from the queue before playing
            await self.play_song(ctx, next_song)
        else:
            print("Queue is empty")


    async def embed_status(self, ctx, link):
        try:
            video_title = await self.get_title(self.now_playing)
            thumbnail_url = await self.get_thumbnail(self.now_playing)

            # Create the embed
            embed = discord.Embed(title="Now playing", description=f'{video_title}', color=0x56c50d)
            
            # Add the thumbnail if it exists:
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            
            # Spacer field (empty field for space)
            embed.add_field(name="\u200b", value="\u200b", inline=False)  # Zero-width space for spacing
            
            # Queue field and other fields
            embed.add_field(name="Queue", value="", inline=False)

            # Assuming self.queues is a dictionary where each guild has a queue list
            queue = self.queues.get(ctx.guild.id, [])  # Get the queue for the current guild, default to empty list
            for track in queue:
                title = await self.get_title(f'{track}')
                embed.add_field(name="", value=f'{title}', inline=False)
            
            embed.add_field(name="\u200b", value="\u200b", inline=False)  # Zero-width space for spacing
            embed.set_footer(text="Use !play <link/search> to request a track.")

            # Send the embed
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"Error extracting video info: {e}")
            await ctx.send("An error occurred while fetching video information.")

            
    async def get_title(self, link):
        with yt_dlp.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(link, download=False)
            video_title = info_dict.get('title', 'Unknown Title')  # Get the video title
            return video_title

    async def get_thumbnail(self, link):
        with yt_dlp.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(link, download=False)
            thumbnail_url = info_dict.get('thumbnail', '')  # Get the thumbnail URL  
            return thumbnail_url   




async def setup(bot):
    await bot.add_cog(MusicBot(bot))