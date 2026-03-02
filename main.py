import discord
from discord.ext import commands
import asyncio
from yt_dlp import YoutubeDL
import os

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

queue = []
current = None
is_playing = False

ytdl_opts = {
    "format": "bestaudio",
    "quiet": True,
    "noplaylist": True,
    "default_search": "ytsearch"
}

ffmpeg_opts = {
    "options": "-vn"
}

async def play_next(ctx):
    global is_playing, current
    if len(queue) == 0:
        is_playing = False
        current = None
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        await ctx.send("خلصت القائمة 🎧")
        return

    is_playing = True
    url = queue.pop(0)
    current = url

    with YoutubeDL(ytdl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        stream_url = info['url']
        title = info['title']

    source = await discord.FFmpegOpusAudio.from_probe(stream_url, **ffmpeg_opts)
    ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
    await ctx.send(f"🎶 شغال دلوقتي: **{title}**")

async def search_youtube(query):
    with YoutubeDL(ytdl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if "entries" in info:
            return info["entries"][0]["webpage_url"]
        return info["webpage_url"]

# =======================
# Commands
# =======================

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send("دخلت الروم 🎧")
    else:
        await ctx.send("لازم تكون في روم صوتي!")

@bot.command()
async def play(ctx, *, query):
    if not ctx.author.voice:
        return await ctx.send("لازم تكون في روم صوتي!")

    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    # لو النص مش رابط، نبحثه على يوتيوب
    if not query.startswith("http"):
        try:
            query = await search_youtube(query)
        except Exception:
            return await ctx.send("مش قادر ألاقي الأغنية 😔")

    queue.append(query)
    if not ctx.voice_client.is_playing() and not is_playing:
        await play_next(ctx)
    else:
        await ctx.send("تمت إضافة الأغنية للقائمة ✅")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("تم التخطي ⏭️")
    else:
        await ctx.send("لا يوجد أغنية تعمل دلوقتي!")

@bot.command()
async def stop(ctx):
    queue.clear()
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("تم الايقاف والخروج ⛔")

@bot.command()
async def queue_list(ctx):
    if len(queue) == 0:
        await ctx.send("القائمة فاضية 😅")
    else:
        msg = "\n".join([f"{i+1}. {q}" for i, q in enumerate(queue)])
        await ctx.send(f"**قائمة الأغاني:**\n{msg}")

@bot.command()
async def nowplaying(ctx):
    if current:
        await ctx.send(f"🎵 الآن شغال: {current}")
    else:
        await ctx.send("لا يوجد أغنية تعمل الآن!")

@bot.command()
async def helpme(ctx):
    cmds = """
**قائمة الأوامر:**
!play <اسم أو رابط> - تشغيل الأغنية أو إضافتها للقائمة
!skip - تخطي الأغنية الحالية
!stop - إيقاف الأغنية والخروج
!join - دخول الروم الصوتي
!queue_list - عرض قائمة الأغاني
!nowplaying - معرفة الأغنية الحالية
!helpme - قائمة الأوامر
"""
    await ctx.send(cmds)

# =======================
# Run bot
# =======================

token = os.getenv("DISCORD_TOKEN")  # سيب التوكن في Railway Secrets باسم DISCORD_TOKEN
if not token:
    print("❌ التوكن مش موجود في Secrets")
else:
    bot.run(token)
