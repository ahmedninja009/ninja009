import os
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio, Embed
from yt_dlp import YoutubeDL
import asyncio

# ================== إعدادات البوتات ==================
# خلي التوكنات في Environment Variables
# TOKEN1, TOKEN2, TOKEN3... PREFIX1, PREFIX2, PREFIX3...
bots_config = [
    {"token": os.environ.get("TOKEN1"), "prefix": os.environ.get("PREFIX1", "!")},
    {"token": os.environ.get("TOKEN2"), "prefix": os.environ.get("PREFIX2", "!")},
]

# ================== إعدادات الصوت ==================
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': True}

# ================== دالة إنشاء بوت ==================
def create_bot(token, prefix):
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    bot = commands.Bot(command_prefix=prefix, intents=intents)
    queue = []

    # -------- تشغيل الأغاني --------
    def play_next(ctx):
        if queue:
            next_song = queue.pop(0)
            ctx.voice_client.play(
                FFmpegPCMAudio(next_song['url'], **FFMPEG_OPTIONS),
                after=lambda e: play_next(ctx)
            )
            embed = Embed(title="🎶 Now Playing", description=f"{next_song['title']}", color=0x00ff00)
            if next_song['thumbnail']:
                embed.set_thumbnail(url=next_song['thumbnail'])
            embed.add_field(name="Duration", value=next_song['duration'], inline=True)
            asyncio.create_task(ctx.send(embed=embed))

    # -------- أمر تشغيل الأغاني --------
    @bot.command(aliases=["ش", "p"])
    async def play(ctx, *, search: str = None):
        if ctx.author.voice is None:
            await ctx.send("❌ You must be in a voice channel first!")
            return

        if not search:
            await ctx.send(
                "💡 Play Usage:\n"
                "`play [track title]` - play track by the first result\n"
                "`play [URL]` - play track by provided link"
            )
            return

        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()

        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
            url = info['url']
            title = info['title']
            thumbnail = info.get('thumbnail', None)
            duration = info.get('duration_string', "Unknown")

        song = {"url": url, "title": title, "thumbnail": thumbnail, "duration": duration}

        if ctx.voice_client.is_playing():
            queue.append(song)
            await ctx.send(f"✅ Added to queue: **{title}**")
        else:
            ctx.voice_client.play(
                FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
                after=lambda e: play_next(ctx)
            )
            embed = Embed(title="🎶 Now Playing", description=f"{title}", color=0x00ff00)
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)
            embed.add_field(name="Duration", value=duration, inline=True)
            await ctx.send(embed=embed)

    # -------- بقية أوامر الصوت --------
    @bot.command(aliases=["تخطي", "s"])
    async def skip(ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Song skipped!")
        else:
            await ctx.send("❌ No song is playing.")

    @bot.command(aliases=["ايقاف", "pa"])
    async def pause(ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Song paused.")
        else:
            await ctx.send("❌ No song is playing.")

    @bot.command(aliases=["كمل", "r"])
    async def resume(ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Song resumed.")
        else:
            await ctx.send("❌ No song is paused.")

    @bot.command(aliases=["st", "اوقف"])
    async def stop(ctx):
        if ctx.voice_client:
            queue.clear()
            await ctx.voice_client.disconnect()
            await ctx.send("🛑 Playback stopped and disconnected.")
        else:
            await ctx.send("❌ Bot is not in a voice channel.")

    @bot.command(aliases=["بينج"])
    async def ping(ctx):
        latency = round(bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: {latency}ms")

    # -------- تغيير البرفكس عند منشن البوت --------
    @bot.event
    async def on_message(message):
        if message.author.bot:
            return
        if bot.user in message.mentions:
            parts = message.content.split()
            if len(parts) > 1:
                new_prefix = parts[1]
                bot.command_prefix = new_prefix
                await message.channel.send(f"✅ Prefix changed to: `{new_prefix}`")
        await bot.process_commands(message)

    # -------- قائمة help خاصة --------
    @bot.command()
    async def help(ctx):
        await ctx.message.add_reaction("✅")
        embed = Embed(title="Bot Commands", color=0x00ff00)
        embed.add_field(name="Play", value="`play [song name/URL]` - Play a song", inline=False)
        embed.add_field(name="Skip", value="`skip` - Skip current song", inline=False)
        embed.add_field(name="Pause", value="`pause` - Pause song", inline=False)
        embed.add_field(name="Resume", value="`resume` - Resume song", inline=False)
        embed.add_field(name="Stop", value="`stop` - Stop playback", inline=False)
        embed.add_field(name="Ping", value="`ping` - Show latency", inline=False)
        await ctx.author.send(embed=embed)

    return bot, token

# ================== تشغيل كل البوتات ==================
async def main():
    bots = []
    for conf in bots_config:
        bot_instance, token = create_bot(conf["token"], conf["prefix"])
        bots.append((bot_instance, token))

    tasks = [bot_instance.start(token) for bot_instance, token in bots]
    await asyncio.gather(*tasks)

asyncio.run(main())
