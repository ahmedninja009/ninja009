import os
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL

# جلب التوكن من Environment Variable
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("Please set your TOKEN in Environment Variables.")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# قائمة الانتظار
queue = []

# خيارات FFmpeg
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YDL_OPTIONS = {'format': 'bestaudio'}

# أمر تشغيل الأغاني
@bot.command()
async def play(ctx, *, search: str):
    if ctx.author.voice is None:
        await ctx.send("انت لازم تكون في الروم الصوتي الأول!")
        return

    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await voice_channel.connect()
    
    # البحث عن الأغنية في يوتيوب
    with YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
        url = info['url']

    queue.append(url)

    # إذا مش شغال حاجة دلوقتي، شغّل الأغنية
    if not ctx.voice_client.is_playing():
        source = FFmpegPCMAudio(queue.pop(0), **FFMPEG_OPTIONS)
        ctx.voice_client.play(source, after=lambda e: play_next(ctx))
        await ctx.send(f"🎵 **Playing:** {info['title']}")

# دالة لتشغيل الأغاني التالية في القائمة
def play_next(ctx):
    if len(queue) > 0:
        next_song = queue.pop(0)
        ctx.voice_client.play(FFmpegPCMAudio(next_song, **FFMPEG_OPTIONS), after=lambda e: play_next(ctx))

# أمر تخطي الأغنية الحالية
@bot.command()
async def skip(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ الأغنية تم تخطيها!")

# أمر إيقاف مؤقت
@bot.command()
async def pause(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ الأغنية متوقفة مؤقتًا!")

# أمر استكمال التشغيل
@bot.command()
async def resume(ctx):
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ استكمال الأغنية!")

# أمر إيقاف كل شيء وترك الروم
@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        queue.clear()
        await ctx.send("🛑 الأغاني توقفت وتم مغادرة الروم الصوتي!")

bot.run(TOKEN)
