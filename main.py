import os
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL

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
            FFmpegPCMAudio(next_song, **FFMPEG_OPTIONS),
            after=lambda e: play_next(ctx)
        )

# ================== COMMANDS ==================

# 🎵 Play
@bot.command()
async def play(ctx, *, search: str):
    if ctx.author.voice is None:
        await ctx.send("❌ لازم تكون في روم صوتي الأول!")
        return

    voice_channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        await voice_channel.connect()

    with YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
        url = info['url']
        title = info['title']

    queue.append(url)

    if not ctx.voice_client.is_playing():
        source = FFmpegPCMAudio(queue.pop(0), **FFMPEG_OPTIONS)
        ctx.voice_client.play(
            source,
            after=lambda e: play_next(ctx)
        )
        await ctx.send(f"🎶 **Now Playing:** {title}")
    else:
        await ctx.send(f"✅ Added to queue: {title}")

# ⏭ Skip
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ تم تخطي الأغنية!")
    else:
        await ctx.send("❌ مفيش أغنية شغالة.")

# ⏸ Pause
@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ تم إيقاف الأغنية مؤقتًا.")
    else:
        await ctx.send("❌ مفيش أغنية شغالة.")

# ▶ Resume
@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ تم استكمال الأغنية.")
    else:
        await ctx.send("❌ مفيش أغنية متوقفة.")

# 🛑 Stop
@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        queue.clear()
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 تم إيقاف التشغيل والخروج من الروم.")
    else:
        await ctx.send("❌ البوت مش في روم صوتي.")

# 🏓 Ping
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! البينج: {latency}ms")

# ================== RUN ==================
bot.run(TOKEN)
