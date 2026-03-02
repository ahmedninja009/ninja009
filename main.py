import discord
from discord.ext import commands
import yt_dlp
import asyncio
import json
import os

# ---------- Prefix System ----------
PREFIX_FILE = "prefixes.json"

def load_prefixes():
    if not os.path.exists(PREFIX_FILE):
        with open(PREFIX_FILE, "w") as f:
            json.dump({}, f)
    with open(PREFIX_FILE, "r") as f:
        return json.load(f)

def save_prefixes(prefixes):
    with open(PREFIX_FILE, "w") as f:
        json.dump(prefixes, f, indent=4)

prefixes = load_prefixes()

def get_prefix(bot, message):
    if not message.guild:
        return "!"
    return prefixes.get(str(message.guild.id), "!")

# ---------- Intents ----------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=get_prefix, intents=intents)

# ---------- Ready ----------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ---------- Ping ----------
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! {latency}ms")

# ---------- Set Prefix ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def setprefix(ctx, new_prefix):
    prefixes[str(ctx.guild.id)] = new_prefix
    save_prefixes(prefixes)
    await ctx.send(f"✅ تم تغيير البرفكس إلى: `{new_prefix}`")

# ---------- Music Setup ----------
ydl_opts = {
    'format': 'bestaudio',
    'quiet': True,
}

ffmpeg_options = {
    'options': '-vn'
}

# ---------- Join ----------
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send("🎧 دخلت الروم")
    else:
        await ctx.send("❌ لازم تكون في روم صوتي")

# ---------- Leave ----------
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 خرجت من الروم")

# ---------- Play ----------
@bot.command()
async def play(ctx, *, url):
    if not ctx.author.voice:
        return await ctx.send("❌ ادخل روم صوتي الأول")

    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['url']
        source = await discord.FFmpegOpusAudio.from_probe(url2)

        ctx.voice_client.play(source)
        await ctx.send(f"🎶 شغال: {info['title']}")

# ---------- Skip ----------
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ تم التخطي")

# ---------- Stop ----------
@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("⏹ تم الإيقاف")

# ---------- Pause ----------
@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸ تم الإيقاف المؤقت")

# ---------- Resume ----------
@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶ تم الاستكمال")

# ---------- Run ----------
bot.run("PUT_YOUR_TOKEN_HERE")
