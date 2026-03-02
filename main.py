import discord
from discord.ext import commands
import asyncio
import yt_dlp
import os

# إعداد intents بشكل آمن
intents = discord.Intents.default()
intents.message_content = True  # علشان نقدر نقرأ أوامر المستخدمين

bot = commands.Bot(command_prefix="!", intents=intents)

# قائمة انتظار الأغاني لكل جيلد
queues = {}

# جلب التوكن من متغير البيئة (Railway Secret)
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# تشغيل الأغنية
@bot.command()
async def play(ctx, *, search: str):
    if not ctx.author.voice:
        return await ctx.send("انت لازم تكون في قناة صوتية أولاً!")

    voice_channel = ctx.author.voice.channel
    guild_id = ctx.guild.id

    if guild_id not in queues:
        queues[guild_id] = []

    # البحث عن الأغنية على يوتيوب
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch',
        'extract_flat': 'in_playlist'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search, download=False)
        url = info['entries'][0]['url'] if 'entries' in info else info['url']
        title = info['entries'][0]['title'] if 'entries' in info else info['title']

    queues[guild_id].append((title, url))
    await ctx.send(f"✅ **Added to queue:** {title}")

    # لو البوت مش متصل في القناة الصوتية، اتصل وشغل
    if not ctx.voice_client:
        vc = await voice_channel.connect()
        await play_next(ctx, vc)
    elif not ctx.voice_client.is_playing():
        await play_next(ctx, ctx.voice_client)

async def play_next(ctx, vc):
    guild_id = ctx.guild.id
    if queues[guild_id]:
        title, url = queues[guild_id].pop(0)
        ydl_opts = {
            'format': 'bestaudio',
            'quiet': True,
        }
        ffmpeg_opts = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']

        vc.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_opts), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx, vc), bot.loop))
        await ctx.send(f"🎶 **Now Playing:** {title}")
    else:
        await vc.disconnect()

# أمر skip
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ Skipped current song!")
    else:
        await ctx.send("لا يوجد أغنية حالياً للتخطي.")

# أمر stop
@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("⏹ Stopped and disconnected from voice channel!")
        queues[ctx.guild.id] = []
    else:
        await ctx.send("البوت مش متصل بأي قناة صوتية.")

# تشغيل البوت
bot.run(TOKEN)
