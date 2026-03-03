import os
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio, Embed
from yt_dlp import YoutubeDL
import asyncio

# ================== CONFIG ==================
BOTS_CONFIG = [
    {"token": os.environ.get("TOKEN1"), "prefix": "!"},
    {"token": os.environ.get("TOKEN2"), "prefix": "?"},
]

# ================== YT & FFMPEG OPTIONS ==================
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YDL_OPTIONS = {
    'format': 'bestaudio',
    'noplaylist': True
}

# ================== CREATE BOT ==================
def create_bot(token, prefix):
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True

    bot = commands.Bot(command_prefix=prefix, intents=intents)
    bot.queue = []
    bot.prefixes = {}  # لتخزين البرفيكس لكل سيرفر

    # ===== AUTO-REACT ON COMMAND =====
    @bot.event
    async def on_command(ctx):
        try:
            await ctx.message.add_reaction("✅")
        except:
            pass

    # ===== CHANGE PREFIX WITH MENTION =====
    @bot.event
    async def on_message(message):
        if message.author.bot:
            return
        # تحقق من منشن للبوت لتغيير البرفيكس
        if bot.user in message.mentions:
            content = message.content.replace(f"<@{bot.user.id}>", "").strip()
            if content:
                bot.prefixes[message.guild.id] = content
                await message.channel.send(f"✅ Prefix changed to `{content}` for this server!")
        await bot.process_commands(message)

    # لتحديد البرفيكس حسب السيرفر
    async def get_prefix(bot_instance, message):
        return bot.prefixes.get(message.guild.id, prefix)

    bot.command_prefix = get_prefix

    # ===== PLAY NEXT =====
    def play_next(ctx):
        if bot.queue:
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

    # ===== COMMANDS =====
    @bot.command(name="play", aliases=["p"])
    async def play(ctx, *, search: str = None):
        if ctx.author.voice is None:
            await ctx.send("❌ You must be in a voice channel first!")
            return
        if not search:
            await ctx.send("💡 Play Usage:\n`play [track title]` - play track by first result\n`play [URL]` - play track by link")
            return
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

    # ===== HELP COMMAND =====
    @bot.command(name="help", aliases=["h"])
    async def help_command(ctx):
        embed = Embed(title="Bot Commands", color=0x00ff00)
        embed.add_field(name="play [song]", value="Play a song or add to queue", inline=False)
        embed.add_field(name="skip", value="Skip current song", inline=False)
        embed.add_field(name="pause", value="Pause current song", inline=False)
        embed.add_field(name="resume", value="Resume paused song", inline=False)
        embed.add_field(name="stop", value="Stop playback and leave VC", inline=False)
        embed.add_field(name="ping", value="Show bot latency", inline=False)
        try:
            await ctx.message.add_reaction("✅")
        except:
            pass
        try:
            await ctx.author.send(embed=embed)
        except:
            await ctx.send("❌ I can't DM you. Please check your privacy settings.")

    @bot.command(name="ping")
    async def ping(ctx):
        await ctx.send(f"🏓 Pong! Latency: {round(bot.latency*1000)}ms")

    return bot

# ================== RUN MULTI-BOTS ==================
async def main():
    bots = []
    for conf in BOTS_CONFIG:
        if conf["token"] is None:
            raise ValueError("Please set all bot TOKENs in Environment Variables.")
        bot_instance = create_bot(conf["token"], conf["prefix"])
        bots.append(bot_instance)
    await asyncio.gather(*[bot.start(conf["token"]) for bot, conf in zip(bots, BOTS_CONFIG)])

asyncio.run(main())
