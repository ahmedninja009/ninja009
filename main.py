import os
import discord
from discord.ext import commands, tasks
import yt_dlp
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

queue = []
current = None

ytdl_options = {
    'format': 'bestaudio',
    'quiet': True,
    'noplaylist': True,
}

ffmpeg_options = {
    'options': '-vn',
}

async def play_next(ctx):
    global current
    if len(queue) == 0:
        await ctx.send("🎧 خلصت القائمة!")
        current = None
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        return

    url = queue.pop(0)
    with yt_dlp.YoutubeDL(ytdl_options) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception:
            await ctx.send("❌ حصل خطأ في تحميل الأغنية.")
            await play_next(ctx)
            return

    stream_url = info['url']
    current = info['title']

    source = await discord.FFmpegOpusAudio.from_probe(stream_url, **ffmpeg_options)
    ctx.voice_client.play(
        source,
        after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
    )

    await ctx.send(f"🎶 شغال دلوقتي: **{current}**")

# ====== Commands ======

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
        await ctx.send("✅ دخلت الروم الصوتي")
    else:
        await ctx.send("❌ لازم تكون في روم صوتي!")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("✅ خرجت من الروم")
    else:
        await ctx.send("❌ البوت مش موجود في أي روم")

@bot.command()
async def play(ctx, *, url: str):
    if not ctx.author.voice:
        return await ctx.send("❌ لازم تكون في روم صوتي!")

    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    queue.append(url)

    if not ctx.voice_client.is_playing() and current is None:
        await play_next(ctx)
    else:
        await ctx.send(f"✅ تمت إضافة الأغنية للقائمة: {url}")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ تم التخطي")
    else:
        await ctx.send("❌ مفيش أغنية شغالة دلوقتي")

@bot.command()
async def stop(ctx):
    queue.clear()
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
    await ctx.send("⛔ تم الايقاف والخروج")

@bot.command()
async def nowplaying(ctx):
    if current:
        await ctx.send(f"🎶 دلوقتي شغال: **{current}**")
    else:
        await ctx.send("❌ مفيش أغنية دلوقتي")

@bot.command()
async def queue_list(ctx):
    if queue:
        msg = "\n".join(f"{i+1}. {q}" for i, q in enumerate(queue))
        await ctx.send(f"📜 قائمة الأغاني:\n{msg}")
    else:
        await ctx.send("📭 قائمة الأغاني فاضية")

# ===== Bot Startup =====
token = os.getenv("DISCORD_TOKEN")  # لازم تضيفه كـ Variable في Railway

if not token:
    print("❌ TOKEN مش موجود! اعمل Secret في Railway باسم DISCORD_TOKEN")
else:
    bot.run(token)
