import os
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio, Embed
from yt_dlp import YoutubeDL
import asyncio

# ================== TOKENS ==================
# كل توكن مع البرفكس الخاص به
BOTS_CONFIG = [
    {"token": os.environ.get("TOKEN1"), "prefix": "!"},
    {"token": os.environ.get("TOKEN2"), "prefix": "?"},
    # ممكن تضيف اكتر
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

# ================== CREATE BOT ==================
def create_bot(initial_prefix):
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True

    # نخلي البرفكس ممكن يتغير لما حد يعمل منشن للبوت
    bot = commands.Bot(command_prefix=commands.when_mentioned_or(initial_prefix), intents=intents)

    queue = []

    def play_next(ctx):
        if len(queue) > 0:
            next_song = queue.pop(0)
            ctx.voice_client.play(
                FFmpegPCMAudio(next_song['url'], **FFMPEG_OPTIONS),
                after=lambda e: play_next(ctx)
            )
            embed = Embed(title="🎶 Now Playing", description=f"{next_song['title']}", color=0x00ff00)
            if next_song['thumbnail']:
                embed.set_thumbnail(url=next_song['thumbnail'])
            embed.add_field(name="Duration", value=next_song['duration'], inline=True)
            asyncio.create_task(ctx.send(embed=embed))

    # ================== COMMANDS ==================
    @bot.command(name="play", aliases=["شغل","ش","p"])
    async def play(ctx, *, search: str = None):
        if ctx.author.voice is None:
            await ctx.send("❌ You must be in a voice channel first!")
            return
        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
        if not search:
            await ctx.send("💡 Play Usage:\nplay [track title]\nplay [URL]")
            await ctx.message.add_reaction("✅")
            return
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
            url = info['url']
            title = info['title']
            thumbnail = info.get('thumbnail', None)
            duration = info.get('duration_string', "Unknown")
        song = {"url": url, "title": title, "thumbnail": thumbnail, "duration": duration}
        if ctx.voice_client.is_playing():
            queue.append(song)
            await ctx.send(f"✅ Added to queue: **{title}**")
            await ctx.message.add_reaction("✅")
        else:
            ctx.voice_client.play(
                FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
                after=lambda e: play_next(ctx)
            )
            embed = Embed(title="🎶 Now Playing", description=f"{title}", color=0x00ff00)
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)
            embed.add_field(name="Duration", value=duration, inline=True)
            await ctx.send(embed=embed)
            await ctx.message.add_reaction("✅")

    @bot.command(name="skip", aliases=["تخطي","s"])
    async def skip(ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Song skipped!")
            await ctx.message.add_reaction("✅")
        else:
            await ctx.send("❌ No song is playing.")

    @bot.command(name="pause", aliases=["ايقاف","pa"])
    async def pause(ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Song paused.")
            await ctx.message.add_reaction("✅")
        else:
            await ctx.send("❌ No song is playing.")

    @bot.command(name="resume", aliases=["كمل","r"])
    async def resume(ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Song resumed.")
            await ctx.message.add_reaction("✅")
        else:
            await ctx.send("❌ No song is paused.")

    @bot.command(name="stop", aliases=["اوقف","st"])
    async def stop(ctx):
        if ctx.voice_client:
            queue.clear()
            await ctx.voice_client.disconnect()
            await ctx.send("🛑 Playback stopped and disconnected.")
            await ctx.message.add_reaction("✅")
        else:
            await ctx.send("❌ Bot is not in a voice channel.")

    @bot.command(name="ping", aliases=["بينج"])
    async def ping(ctx):
        latency = round(bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: {latency}ms")
        await ctx.message.add_reaction("✅")

    # ================== CHANGE PREFIX ==================
    @bot.event
    async def on_message(message):
        if message.author.bot:
            return
        # لو البوت تم منشنه، يغير البرفكس
        if bot.user.mentioned_in(message):
            parts = message.content.split()
            if len(parts) > 1:
                new_prefix = parts[1]
                bot.command_prefix = commands.when_mentioned_or(new_prefix)
                await message.channel.send(f"✅ Prefix changed to: `{new_prefix}`")
        await bot.process_commands(message)

    return bot

# ================== RUN ALL BOTS ==================
async def start_all_bots():
    tasks = []
    for config in BOTS_CONFIG:
        token = config.get("token")
        prefix = config.get("prefix", "!")
        if token:
            bot_instance = create_bot(prefix)
            tasks.append(bot_instance.start(token))
    await asyncio.gather(*tasks)

asyncio.run(start_all_bots())
