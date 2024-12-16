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


        await ctx.message.delete()
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


    async def append_to_messages(self, ctx, message):
        current_function = inspect.currentframe().f_code.co_name
        print(f"Executing function: {current_function}")
        try:
            # Ensure the bot_messages dictionary has an entry for the guild
            if ctx.guild.id not in self.bot_messages:
                self.bot_messages[ctx.guild.id] = []

            # Send the message and append it to the guild's list
            self.bot_messages[ctx.guild.id].append(message)

        except Exception as e:
            print(f"An error occurred in send and append: {e}")

    async def delete_all_messages(self, ctx):
        current_function = inspect.currentframe().f_code.co_name
        print(f"Executing function: {current_function}")
        try:
            # Check if there are messages to delete for the guild
            if ctx.guild.id in self.bot_messages:
                # Iterate through all the messages and delete them
                for message in self.bot_messages[ctx.guild.id]:
                    try:
                        await message.delete()
                    except Exception as e:
                        print(f"Failed to delete message: {e}")

                # Clear the message list for the guild
                self.bot_messages[ctx.guild.id] = []
                print("All messages deleted successfully.")
            else:
                print("No messages to delete for this guild.")

        except Exception as e:
            print(f"An error occurred in delete_all_messages: {e}")


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
        

        # Ensure a queue exists for the guild
        if ctx.guild.id not in self.queues:
            self.queues[ctx.guild.id] = []

        # If no song is playing, start playing this song
        if not ctx.voice_client.is_playing():
            player = discord.FFmpegOpusAudio(song, **self.ffmpeg_options)
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.after_song_finish(ctx), self.bot.loop))
        else:
            # If a song is playing, add this song to the queue
            self.queues[ctx.guild.id].append({"song": song, "link": link})

            await self.embed_status(ctx)



    async def after_song_finish(self, ctx):
        current_function = inspect.currentframe().f_code.co_name
        print(f"Executing function: {current_function}")
        """Called when a song finishes playing. Plays the next song in the queue."""
        
        # Check if the queue exists and has songs
        if ctx.guild.id in self.queues and len(self.queues[ctx.guild.id]) > 0:
            # Retrieve the next song dictionary (contains 'song' and 'link')
            next_song = self.queues[ctx.guild.id].pop(0)
            
            # Extract the song and link
            song = next_song["song"]
            link = next_song["link"]

            print(f"Next song link: {link}")
            
            # Play the next song
            await self.play_song(ctx, song, link)
            await self.embed_status(ctx)
        else:
            self.delete_all_messages(ctx)
            print("Queue is empty")


    async def embed_status(self, ctx):

        # Delete all previous status messages
        await self.delete_all_messages(ctx)

        try:
            # Get the queue for the current guild
            queue = self.queues.get(ctx.guild.id, [])  # Defaults to an empty list if no queue exists

            if not queue:
                return

            # Create the embed
            embed = discord.Embed(title="Queue", color=0x56c50d)

            # Dynamically list all songs in the queue
            queue_details = []
            for index, track in enumerate(queue, start=1):
                try:
                    title = await self.get_title(track["link"])  # Fetch title dynamically
                    queue_details.append(f"{index}. [{title}]({track['link']})")
                except Exception as e:
                    print(f"Error fetching title for track {track}: {e}")
                    queue_details.append(f"{index}. [Unknown Title]({track['link']})")

            # Join all queue details into a single string for the embed
            embed.add_field(name="Tracks currently in queue", value="\n".join(queue_details), inline=False)

            # Footer for usage instructions
            embed.set_footer(text="Use !play <link/search> to add a song to the queue.")

            # Send the embed
            message = await ctx.send(embed=embed)
            await self.append_to_messages(ctx, message)

        except Exception as e:
            print(f"Error generating queue embed: {e}")


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