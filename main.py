import os
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio, Embed
import asyncio
from youtubesearchpython import VideosSearch

# ================== CONFIG ==================
CONFIGS = [
    {"token": os.environ.get("TOKEN1"), "prefix": "!"},
    {"token": os.environ.get("TOKEN2"), "prefix": "#"},
]

# ================== GLOBAL OPTIONS ==================
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -ar 22050 -b:a 64k'
}

# ================== BOT CREATOR ==================
def create_bot(token, prefix):
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    bot = commands.Bot(command_prefix=prefix, intents=intents, help_command=None)
    queue = []

    # ------------------ PLAY NEXT ------------------
    def play_next(ctx):
        if len(queue) > 0:
            next_song = queue.pop(0)
            
            def after_play(error):
                if error:
                    print(f"Playback error: {error}")
                    return
                bot.loop.create_task(play_next_async(ctx))
            
            ctx.voice_client.play(
                FFmpegPCMAudio(next_song['url'], **FFMPEG_OPTIONS),
                after=after_play
            )

            embed = Embed(
                title="🎶 Now Playing",
                description=f"{next_song['title']}",
                color=0x00ff00
            )
            embed.add_field(name="Duration", value=next_song['duration'], inline=True)
            bot.loop.create_task(ctx.send(embed=embed))

    async def play_next_async(ctx):
        await asyncio.sleep(1)
        if ctx.voice_client:
            play_next(ctx)

    # ------------------ COMMANDS ------------------
    @bot.command(name="play", aliases=["ش", "شغل", "p"])
    async def play(ctx, *, query=None):
        if ctx.author.voice is None:
            await ctx.send("❌ You must be in a voice channel first!")
            return

        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()

        if not query:
            await ctx.send("💡 Play Usage:\nplay [track title] - play track by first result")
            return

        # ------------------ البحث عن الفيديو ------------------
        videosSearch = VideosSearch(query, limit=1)
        result = videosSearch.result()['result'][0]
        url = result['link']
        title = result['title']
        duration = result.get('duration', "Unknown")

        song = {"url": url, "title": title, "duration": duration}

        if ctx.voice_client.is_playing():
            queue.append(song)
            await ctx.send(f"✅ Added to queue: **{title}**")
        else:
            ctx.voice_client.play(
                FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
                after=lambda e: bot.loop.create_task(play_next_async(ctx))
            )
            embed = Embed(title="🎶 Now Playing", description=f"{title}", color=0x00ff00)
            embed.add_field(name="Duration", value=duration, inline=True)
            await ctx.send(embed=embed)

    @bot.command(name="skip", aliases=["تخطي", "s"])
    async def skip(ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Song skipped!")
        else:
            await ctx.send("❌ No song is playing.")

    @bot.command(name="pause", aliases=["ايقاف", "pa"])
    async def pause(ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Song paused.")
        else:
            await ctx.send("❌ No song is playing.")

    @bot.command(name="resume", aliases=["كمل", "r"])
    async def resume(ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Song resumed.")
        else:
            await ctx.send("❌ No song is paused.")

    @bot.command(name="stop", aliases=["اوقف", "st"])
    async def stop(ctx):
        if ctx.voice_client:
            queue.clear()
            await ctx.voice_client.disconnect()
            await ctx.send("🛑 Playback stopped and disconnected.")
        else:
            await ctx.send("❌ Bot is not in a voice channel.")

    @bot.command(name="ping", aliases=["بينج"])
    async def ping(ctx):
        latency = round(bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: {latency}ms")

    # ------------------ HELP COMMAND ------------------
    @bot.command(name="help", aliases=["h"])
    async def help_command(ctx):
        embed = Embed(
            title="📜 Bot Commands",
            description="Here is a list of available commands:",
            color=0x00ff00
        )
        embed.add_field(
            name="🎵 Music Commands",
            value="`play [title]`\n`skip`\n`pause`\n`resume`\n`stop`",
            inline=False
        )
        embed.add_field(
            name="🏓 Utility",
            value="`ping`\n`help`",
            inline=False
        )
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        try:
            dm = await ctx.author.create_dm()
            await dm.send(embed=embed)
            await ctx.message.add_reaction("📬")
        except discord.Forbidden:
            await ctx.send("❌ افتح الخاص علشان أقدر أبعتلك الهيلب.")

    # ------------------ REACT ON COMMAND ------------------
    @bot.event
    async def on_command_completion(ctx):
        try:
            await ctx.message.add_reaction("✅")
        except:
            pass

    # ------------------ CHANGE PREFIX VIA MENTION ------------------
    @bot.event
    async def on_message(message):
        if message.author.bot:
            return
        if bot.user.mentioned_in(message):
            parts = message.content.split()
            if len(parts) >= 2:
                new_prefix = parts[1]
                bot.command_prefix = new_prefix
                await message.channel.send(f"✅ Prefix changed to: {new_prefix}")
        await bot.process_commands(message)

    @bot.event
    async def on_message_edit(before, after):
        pass

    return bot, token

# ================== RUN ALL BOTS ==================
async def main():
    bots = []
    for conf in CONFIGS:
        if not conf["token"]:
            continue
        bot_instance, token = create_bot(conf["token"], conf["prefix"])
        bots.append(bot_instance)

    await asyncio.gather(*(bot.start(conf["token"]) for bot, conf in zip(bots, CONFIGS)))

if __name__ == "__main__":
    asyncio.run(main())
