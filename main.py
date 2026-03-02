import discord
from discord.ext import commands
import os
import asyncio
from yt_dlp import YoutubeDL

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # ضروري لتشغيل الصوت

bot = commands.Bot(command_prefix="!", intents=intents)

# إعدادات yt-dlp
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True
}

FFMPEG_OPTIONS = {
    'options': '-vn'
}

# Queue لكل سيرفر
queues = {}

# دالة مساعدة لتشغيل الصوت
async def play_song(ctx, url):
    if ctx.guild.id not in queues:
        queues[ctx.guild.id] = []

    def next_song(error=None):
        if queues[ctx.guild.id]:
            source = queues[ctx.guild.id].pop(0)
            ctx.guild.voice_client.play(source, after=next_song)

    with YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['url']
        source = discord.FFmpegPCMAudio(url2, **FFMPEG_OPTIONS)

    if not ctx.voice_client.is_playing():
        ctx.voice_client.play(source, after=next_song)
        await ctx.send(f"**Playing:** {info['title']}")
    else:
        queues[ctx.guild.id].append(source)
        await ctx.send(f"**Added to queue:** {info['title']}")

# أوامر البوت
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"Joined {channel}")
    else:
        await ctx.send("You are not in a voice channel!")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected!")
    else:
        await ctx.send("I'm not in a voice channel!")

@bot.command()
async def play(ctx, *, query):
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("Join a voice channel first!")
            return

    # تحقق إذا المدخل URL أو كلمة بحث
    if "youtube.com" in query or "youtu.be" in query:
        url = query
    else:
        # بحث على يوتيوب
        with YoutubeDL({'format':'bestaudio','noplaylist':'True','default_search':'ytsearch'}) as ydl:
            info = ydl.extract_info(query, download=False)['entries'][0]
            url = info['webpage_url']

    await play_song(ctx, url)

@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Stopped playing!")
    else:
        await ctx.send("Nothing is playing!")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped current song!")
    else:
        await ctx.send("Nothing is playing!")

@bot.command()
async def queue(ctx):
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        await ctx.send(f"Queue length: {len(queues[ctx.guild.id])} songs")
    else:
        await ctx.send("Queue is empty!")

# تشغيل البوت
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
