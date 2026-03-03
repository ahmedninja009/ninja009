import os
import asyncio
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio, Embed
from yt_dlp import YoutubeDL

# ================== CONFIG ==================
# Example configuration for multiple bots
# كل بوت عنده token وبرفيكس
BOT_CONFIGS = [
    {"token": os.environ.get("TOKEN1"), "prefix": "!"},
    {"token": os.environ.get("TOKEN2"), "prefix": "?"},
]

# ================== OPTIONS ==================
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YDL_OPTIONS = {
    'format': 'bestaudio',
    'noplaylist': True
}

# ================== BOT CREATION ==================
def create_bot(token, prefix):
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True

    # help_command=None لحل مشكلة CommandRegistrationError مع help
    bot = commands.Bot(command_prefix=prefix, intents=intents, help_command=None)
    bot.queue = []

    # ================== PLAY NEXT ==================
    def play_next(ctx):
        if len(bot.queue) > 0:
            next_song = bot.queue.pop(0)
            ctx.voice_client.play(
                FFmpegPCMAudio(next_song['url'], **FFMPEG_OPTIONS),
                after=lambda e: play_next(ctx)
            )
            embed = Embed(title="🎶 Now Playing", description=next_song['title'], color=0x00ff00)
            if next_song['thumbnail']:
                embed.set_thumbnail(url=next_song['thumbnail'])
            embed.add_field(name="Duration", value=next_song['duration'], inline=True)
            asyncio.create_task(ctx.send(embed=embed))

    # ================== COMMANDS ==================

    @bot.command(name="play", aliases=["p"])
    async def play(ctx, *, search: str = None):
        if ctx.author.voice is None:
            await ctx.send("❌ You must be in a voice channel first!")
            return

        if search is None:
            return await ctx.send(
                "💡 Play Usage:\n"
                "`play [track title]` - play track by the first result\n"
                "`play [URL]` - play track by provided link"
            )

        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()

        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
            url = info['url']
            title = info['title']
            thumbnail = info.get('thumbnail', None)
            duration = info.get('duration_string', "Unknown")

        song = {"url": url, "title": title, "thumbnail": thumbnail, "duration": duration}

        if ctx.voice_client.is_playing():
            bot.queue.append(song)
            await ctx.send(f"✅ Added to queue: **{title}**")
        else:
            ctx.voice_client.play(
                FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
                after=lambda e: play_next(ctx)
            )
            embed = Embed(title="🎶 Now Playing", description=title, color=0x00ff00)
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)
            embed.add_field(name="Duration", value=duration, inline=True)
            await ctx.send(embed=embed)

    @bot.command(name="skip", aliases=["s"])
    async def skip(ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Song skipped!")
        else:
            await ctx.send("❌ No song is playing.")

    @bot.command(name="pause", aliases=["pa"])
    async def pause(ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Song paused.")
        else:
            await ctx.send("❌ No song is playing.")

    @bot.command(name="resume", aliases=["r"])
    async def resume(ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Song resumed.")
        else:
            await ctx.send("❌ No song is paused.")

    @bot.command(name="stop", aliases=["st"])
    async def stop(ctx):
        if ctx.voice_client:
            bot.queue.clear()
            await ctx.voice_client.disconnect()
            await ctx.send("🛑 Playback stopped and disconnected.")
        else:
            await ctx.send("❌ Bot is not in a voice channel.")

    @bot.command(name="ping")
    async def ping(ctx):
        latency = round(bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: {latency}ms")

    # ================== HELP COMMAND ==================
    @bot.command(name="help", aliases=["h"])
    async def help_command(ctx):
        # React to the message
        await ctx.message.add_reaction("✅")
        # Send help in DM
        embed = Embed(title="Help - Music Commands", color=0x00ff00)
        embed.add_field(name="play [title|URL]", value="Play a track or add to queue", inline=False)
        embed.add_field(name="skip", value="Skip current track", inline=False)
        embed.add_field(name="pause", value="Pause the music", inline=False)
        embed.add_field(name="resume", value="Resume the music", inline=False)
        embed.add_field(name="stop", value="Stop playback and disconnect", inline=False)
        embed.add_field(name="ping", value="Check bot latency", inline=False)
        try:
            await ctx.author.send(embed=embed)
        except:
            await ctx.send("❌ I couldn't DM you. Please check your DM settings.")

    return bot

# ================== RUN MULTIPLE BOTS ==================
async def main():
    bots = [create_bot(conf["token"], conf["prefix"]) for conf in BOT_CONFIGS]
    tasks = [bot_instance.start(conf["token"]) for bot_instance, conf in zip(bots, BOT_CONFIGS)]
    await asyncio.gather(*tasks)

asyncio.run(main())
