import os
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio, Embed
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
            FFmpegPCMAudio(next_song['url'], **FFMPEG_OPTIONS),
            after=lambda e: play_next(ctx)
        )
        # رسالة اغنية جديدة
        embed = Embed(title="🎶 Now Playing", description=f"{next_song['title']}", color=0x00ff00)
        embed.set_thumbnail(url=next_song['thumbnail'])
        embed.add_field(name="المدة", value=next_song['duration'], inline=True)
        embed.add_field(name="الطلب من", value=next_song['requester'], inline=True)
        bot.loop.create_task(ctx.send(embed=embed))

# ================== COMMANDS ==================

# 🎵 تشغيل الأغنية
@bot.command(name="تشغيل", aliases=["ش", "play"])
async def تشغيل(ctx, *, search: str):
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
        thumbnail = info.get('thumbnail', None)
        duration = info.get('duration_string', "غير معروف")

    song = {"url": url, "title": title, "thumbnail": thumbnail, "duration": duration, "requester": ctx.author.mention}

    # اذا فيه أغنية شغالة
    if ctx.voice_client.is_playing():
        queue.append(song)
        await ctx.send(f"✅ تم إضافة للأنتظار: **{title}**")
    else:
        ctx.voice_client.play(
            FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
            after=lambda e: play_next(ctx)
        )
        embed = Embed(title="🎶 Now Playing", description=f"{title}", color=0x00ff00)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        embed.add_field(name="المدة", value=duration, inline=True)
        embed.add_field(name="الطلب من", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)

# ⏭ تخطي
@bot.command(name="تخطي", aliases=["skip", "تخطي"])
async def تخطي(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ تم تخطي الأغنية!")
    else:
        await ctx.send("❌ مفيش أغنية شغالة.")

# ⏸ إيقاف مؤقت
@bot.command(name="إيقاف", aliases=["pause", "وقف"])
async def إيقاف(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ تم إيقاف الأغنية مؤقتًا.")
    else:
        await ctx.send("❌ مفيش أغنية شغالة.")

# ▶ استكمال
@bot.command(name="استكمال", aliases=["resume", "كمل"])
async def استكمال(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ تم استكمال الأغنية.")
    else:
        await ctx.send("❌ مفيش أغنية متوقفة.")

# 🛑 إيقاف نهائي
@bot.command(name="إيقاف_كلي", aliases=["stop", "ايقاف"])
async def إيقاف_كلي(ctx):
    if ctx.voice_client:
        queue.clear()
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 تم إيقاف التشغيل والخروج من الروم.")
    else:
        await ctx.send("❌ البوت مش في روم صوتي.")

# 🏓 بينج
@bot.command(name="بينج", aliases=["ping", "بينج"])
async def بينج(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! البينج: {latency}ms")

# ================== RUN ==================
bot.run(TOKEN)
