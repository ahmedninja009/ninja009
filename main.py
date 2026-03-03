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
current_data = None

# ================== OPTIONS ==================
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YDL_OPTIONS = {
    'format': 'bestaudio',
    'noplaylist': True
}

# ================== FORMAT DURATION ==================
def format_duration(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"

# ================== PLAY FUNCTIONS ==================

async def start_playing(ctx, data):
    global current_song, current_data

    current_song = data["url"]
    current_data = data

    ctx.voice_client.play(
        FFmpegPCMAudio(data["url"], **FFMPEG_OPTIONS),
        after=lambda e: bot.loop.create_task(play_next(ctx))
    )

    embed = discord.Embed(
        title="🎶 Now Playing",
        description=f"[{data['title']}]({data['webpage_url']})",
        color=discord.Color.green()
    )

    embed.add_field(name="⏱ Duration", value=format_duration(data["duration"]), inline=True)
    embed.add_field(name="👤 Requested by", value=data["requester"].mention, inline=True)

    embed.set_thumbnail(url=data["thumbnail"])
    embed.set_footer(text=f"Server: {ctx.guild.name}")

    await ctx.send(embed=embed)


async def play_next(ctx):
    global current_song, current_data

    if len(queue) > 0:
        data = queue.pop(0)
        await start_playing(ctx, data)
    else:
        current_song = None
        current_data = None
        embed = discord.Embed(
            title="📭 Queue Finished",
            description="مفيش أغاني تاني.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# ================== COMMANDS ==================

@bot.command()
async def play(ctx, *, search: str):
    if ctx.author.voice is None:
        return await ctx.send("❌ لازم تكون في روم صوتي الأول!")

    if ctx.voice_client is None:
        await ctx.author.voice.channel.connect()

    with YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]

        data = {
            "url": info["url"],
            "title": info["title"],
            "duration": info["duration"],
            "thumbnail": info["thumbnail"],
            "webpage_url": info["webpage_url"],
            "requester": ctx.author
        }

    if ctx.voice_client.is_playing():
        queue.append(data)

        embed = discord.Embed(
            title="✅ Added to Queue",
            description=f"[{data['title']}]({data['webpage_url']})",
            color=discord.Color.orange()
        )

        embed.add_field(name="⏱ Duration", value=format_duration(data["duration"]), inline=True)
        embed.add_field(name="👤 Requested by", value=ctx.author.mention, inline=True)
        embed.set_thumbnail(url=data["thumbnail"])

        await ctx.send(embed=embed)
    else:
        await start_playing(ctx, data)


@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        embed = discord.Embed(
            title="⏭ Skipped",
            description=f"تم تخطي: **{current_data['title']}**",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        ctx.voice_client.stop()
    else:
        await ctx.send("❌ مفيش أغنية شغالة.")


@bot.command()
async def stop(ctx):
    global current_song, current_data
    if ctx.voice_client:
        queue.clear()
        current_song = None
        current_data = None
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 تم إيقاف التشغيل والخروج من الروم.")


@bot.command()
async def queue_list(ctx):
    if not queue:
        return await ctx.send("📭 الكيو فاضي.")

    embed = discord.Embed(title="📜 Current Queue", color=discord.Color.blue())

    for i, song in enumerate(queue, start=1):
        embed.add_field(
            name=f"{i}. {song['title']}",
            value=f"⏱ {format_duration(song['duration'])} | 👤 {song['requester'].mention}",
            inline=False
        )

    await ctx.send(embed=embed)


@bot.command()
async def now(ctx):
    if current_data:
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"[{current_data['title']}]({current_data['webpage_url']})",
            color=discord.Color.green()
        )

        embed.add_field(name="⏱ Duration", value=format_duration(current_data["duration"]), inline=True)
        embed.add_field(name="👤 Requested by", value=current_data["requester"].mention, inline=True)
        embed.set_thumbnail(url=current_data["thumbnail"])

        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ مفيش حاجة شغالة.")


@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latency: **{latency}ms**",
        color=discord.Color.blurple()
    )
    await ctx.send(embed=embed)


bot.run(TOKEN)
