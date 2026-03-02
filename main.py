import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Queues
queue = []
history = []
current = None
volume_level = 0.5  # 50% volume
loop_mode = "none"  # "none", "one", "all"

# YTDL & FFMPEG options
ytdl_opts = {
    "format": "bestaudio",
    "quiet": True,
    "noplaylist": True,
}

ffmpeg_opts = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

# ----------------------
# MUSIC PLAY FUNCTION
# ----------------------
async def play_next(ctx):
    global current, history
    if len(queue) == 0:
        current = None
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        await ctx.send("خلصت القائمة 🎧")
        return

    query = queue.pop(0)
    history.append(query)

    try:
        with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
            if query.startswith("http"):
                info = ydl.extract_info(query, download=False)
            else:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                info = info['entries'][0]
            url = info['url']
            title = info.get("title", "Unknown")
    except Exception as e:
        await ctx.send(f"❌ حصل خطأ في تشغيل الأغنية: {e}")
        await play_next(ctx)
        return

    try:
        source = discord.FFmpegPCMAudio(url, **ffmpeg_opts)
        ctx.voice_client.play(
            source,
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        )
        current = title
        await ctx.send(f"🎶 شغال دلوقتي: {title}")
    except Exception as e:
        await ctx.send(f"❌ حصل خطأ في تشغيل الصوت: {e}")
        await play_next(ctx)

# ----------------------
# EVENTS
# ----------------------
@bot.event
async def on_ready():
    print(f"Bot جاهز: {bot.user}")

# ----------------------
# COMMANDS
# ----------------------
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send("دخلت الروم 🎧")
    else:
        await ctx.send("لازم تكون في روم صوتي!")

@bot.command()
async def leave(ctx):
    queue.clear()
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("خرجت من الروم ⛔")

@bot.command()
async def play(ctx, *, query):
    if not ctx.author.voice:
        return await ctx.send("لازم تكون في روم صوتي!")

    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    queue.append(query)

    if not ctx.voice_client.is_playing():
        await play_next(ctx)
    else:
        await ctx.send(f"تمت إضافة الأغنية للقائمة ✅: {query}")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("تم التخطي ⏭️")

@bot.command()
async def stop(ctx):
    queue.clear()
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("تم الايقاف والخروج ⛔")

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ تم الإيقاف مؤقت")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ تم استئناف التشغيل")

@bot.command()
async def queue_list(ctx):
    if queue:
        msg = "\n".join(f"{i+1}. {song}" for i, song in enumerate(queue))
        await ctx.send(f"📜 قائمة الانتظار:\n{msg}")
    else:
        await ctx.send("لا توجد أغاني في القائمة 🎶")

@bot.command()
async def current_song(ctx):
    if current:
        await ctx.send(f"🎵 دلوقتي شغال: {current}")
    else:
        await ctx.send("لا توجد أغنية حالياً")

@bot.command()
async def commands_list(ctx):
    cmds = """
**Commands List:**
`play [p]` : Play song or add to queue (يمكنك كتابة اسم الأغنية)
`pause` : Pause the song
`resume` : Resume the song
`queue` : Show the queue
`skip` : Skip current song
`stop` : Stop and clear queue
`join` : Join voice channel
`leave` : Leave voice channel
`current` : Show current song
"""
    await ctx.send(cmds)

# ----------------------
# TOKEN
# ----------------------
token = "DISCORD_TOKEN"  # ضع توكن البوت هنا
bot.run(token)
