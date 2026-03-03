import os
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio, Embed
from yt_dlp import YoutubeDL
import asyncio

# ================== TOKEN ==================
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("Please set your TOKEN in Environment Variables.")

# ================== INTENTS ==================
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================== QUEUE ==================
queue = []

# ================== OPTIONS ==================
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YDL_OPTIONS = {
    'format': 'bestaudio',
    'noplaylist': True
}

# ================== PLAY NEXT ==================
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
@bot.command(name="play", aliases=["شغل", "p"])
async def play(ctx, *, search: str = None):
    if ctx.author.voice is None:
        await ctx.send("❌ You must be in a voice channel first!")
        return

    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await voice_channel.connect()

    if not search:
        await ctx.send(
            "💡 Play Usage:\n"
            "play [track title] - play track by the first result\n"
            "play [URL] - play track by provided link"
        )
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

@bot.command(name="skip", aliases=["تخطي", "s"])
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Song skipped!")
        await ctx.message.add_reaction("✅")
    else:
        await ctx.send("❌ No song is playing.")

@bot.command(name="pause", aliases=["ايقاف", "pa"])
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Song paused.")
        await ctx.message.add_reaction("✅")
    else:
        await ctx.send("❌ No song is playing.")

@bot.command(name="resume", aliases=["كمل", "r"])
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Song resumed.")
        await ctx.message.add_reaction("✅")
    else:
        await ctx.send("❌ No song is paused.")

@bot.command(name="stop", aliases=["اوقف", "st"])
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

# ================== CUSTOM HELP ==================
@bot.command(name="help", aliases=["هلب", "مساعدة"])
async def help_command(ctx):
    await ctx.message.add_reaction("✅")
    embed = Embed(title="📜 Bot Commands", color=0x00ff00)
    embed.add_field(name="!play [song]", value="Play a song by name or URL", inline=False)
    embed.add_field(name="!skip", value="Skip current song", inline=False)
    embed.add_field(name="!pause", value="Pause the current song", inline=False)
    embed.add_field(name="!resume", value="Resume the paused song", inline=False)
    embed.add_field(name="!stop", value="Stop playback and disconnect", inline=False)
    embed.add_field(name="!ping", value="Check bot latency", inline=False)
    try:
        await ctx.author.send(embed=embed)
    except:
        await ctx.send("❌ Could not send you DM. Make sure your DMs are open!")

# ================== RUN ==================
bot.run(TOKEN)
