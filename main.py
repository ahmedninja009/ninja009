# main.py
import os
import discord
from discord.ext import commands
import yt_dlp
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# YT-DLP options
ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'extract_flat': 'in_playlist',
    'jsruntimes': ['node'],  # استخدام Node.js runtime
}

queues = {}  # لتخزين قوائم التشغيل لكل سيرفر

async def play_next(ctx, guild_id):
    if queues[guild_id]:
        url = queues[guild_id].pop(0)
        vc = ctx.voice_client
        FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        vc.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx, guild_id), bot.loop))
    else:
        await ctx.voice_client.disconnect()

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
        await ctx.send("Joined the voice channel!")
    else:
        await ctx.send("You are not in a voice channel!")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Left the voice channel!")
    else:
        await ctx.send("I'm not in a voice channel!")

@bot.command()
async def play(ctx, *, search: str):
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("You are not in a voice channel!")
            return

    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = []

    # البحث عن الأغنية على يوتيوب
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
            url = info['url']
            title = info['title']
        except Exception as e:
            await ctx.send(f"❌ Could not find the song: {e}")
            return

    queues[guild_id].append(url)
    await ctx.send(f"✅ Added to queue: {title}")

    if not ctx.voice_client.is_playing():
        await play_next(ctx, guild_id)

@bot.command()
async def queue(ctx):
    guild_id = ctx.guild.id
    if guild_id in queues and queues[guild_id]:
        msg = "\n".join(f"{i+1}. {q}" for i, q in enumerate(queues[guild_id]))
        await ctx.send(f"**Queue:**\n{msg}")
    else:
        await ctx.send("The queue is empty.")

# تشغيل البوت
TOKEN = os.getenv("DISCORD_TOKEN")  # تأكد إنك ضيفت التوكن كـ Environment Variable
bot.run(TOKEN)
