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

# ================== QUEUE SYSTEM ==================
queue = []
current_song = None
current_title = None

# ================== OPTIONS ==================
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YDL_OPTIONS = {
    'format': 'bestaudio',
    'noplaylist': True
}

# ================== EMBED FUNCTION ==================
def create_embed(title, description, color=discord.Color.blue()):
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

# ================== PLAY FUNCTIONS ==================

async def start_playing(ctx, url, title):
    global current_song, current_title

    current_song = url
    current_title = title

    ctx.voice_client.play(
        FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
        after=lambda e: bot.loop.create_task(play_next(ctx))
    )

    embed = create_embed("🎶 Now Playing", f"**{title}**", discord.Color.green())
    await ctx.send(embed=embed)


async def play_next(ctx):
    global current_song, current_title

    if len(queue) > 0:
        url, title = queue.pop(0)
        await start_playing(ctx, url, title)
    else:
        current_song = None
        current_title = None
        embed = create_embed("📭 Queue Finished", "مفيش أغاني تاني.", discord.Color.red())
        await ctx.send(embed=embed)


# ================== COMMANDS ==================

# 🎵 Play
@bot.command()
async def play(ctx, *, search: str):
    if ctx.author.voice is None:
        embed = create_embed("❌ Error", "لازم تكون في روم صوتي الأول!", discord.Color.red())
        return await ctx.send(embed=embed)

    voice_channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        await voice_channel.connect()

    with YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
        url = info['url']
        title = info['title']

    if ctx.voice_client.is_playing():
        queue.append((url, title))
        embed = create_embed("✅ Added to Queue", f"**{title}**", discord.Color.orange())
        await ctx.send(embed=embed)
    else:
        await start_playing(ctx, url, title)


# ⏭ Skip
@bot.command()
async def skip(ctx):
    global current_title

    if ctx.voice_client and ctx.voice_client.is_playing():
        embed = create_embed("⏭ Skipped", f"تم تخطي: **{current_title}**", discord.Color.orange())
        await ctx.send(embed=embed)
        ctx.voice_client.stop()
    else:
        embed = create_embed("❌ Error", "مفيش أغنية شغالة.", discord.Color.red())
        await ctx.send(embed=embed)


# ⏸ Pause
@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        embed = create_embed("⏸ Paused", "تم إيقاف الأغنية مؤقتًا.", discord.Color.gold())
        await ctx.send(embed=embed)
    else:
        embed = create_embed("❌ Error", "مفيش أغنية شغالة.", discord.Color.red())
        await ctx.send(embed=embed)


# ▶ Resume
@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        embed = create_embed("▶ Resumed", "تم استكمال الأغنية.", discord.Color.green())
        await ctx.send(embed=embed)
    else:
        embed = create_embed("❌ Error", "مفيش أغنية متوقفة.", discord.Color.red())
        await ctx.send(embed=embed)


# 🛑 Stop
@bot.command()
async def stop(ctx):
    global current_song, current_title

    if ctx.voice_client:
        queue.clear()
        current_song = None
        current_title = None
        await ctx.voice_client.disconnect()
        embed = create_embed("🛑 Stopped", "تم إيقاف التشغيل والخروج من الروم.", discord.Color.red())
        await ctx.send(embed=embed)
    else:
        embed = create_embed("❌ Error", "البوت مش في روم صوتي.", discord.Color.red())
        await ctx.send(embed=embed)


# 📜 Queue
@bot.command()
async def queue_list(ctx):
    if not queue:
        embed = create_embed("📭 Queue", "الكيو فاضي.", discord.Color.blue())
        await ctx.send(embed=embed)
    else:
        msg = ""
        for i, song in enumerate(queue, start=1):
            msg += f"{i}- {song[1]}\n"
        embed = create_embed("📜 Current Queue", msg, discord.Color.blue())
        await ctx.send(embed=embed)


# 📢 Now Playing
@bot.command()
async def now(ctx):
    if current_title:
        embed = create_embed("🎵 Now Playing", f"**{current_title}**", discord.Color.green())
        await ctx.send(embed=embed)
    else:
        embed = create_embed("❌ Error", "مفيش حاجة شغالة.", discord.Color.red())
        await ctx.send(embed=embed)


# 🏓 Ping
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    embed = create_embed("🏓 Pong!", f"البينج: **{latency}ms**", discord.Color.blurple())
    await ctx.send(embed=embed)


# ================== RUN ==================
bot.run(TOKEN)
