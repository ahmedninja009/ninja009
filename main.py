import discord
from discord.ext import commands
import yt_dlp
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# قائمة الانتظار
queue = []

ytdl_options = {
    'format': 'bestaudio',
    'quiet': True,
    'noplaylist': True,
}

# ================= Commands ==================

@bot.event
async def on_ready():
    print(f"Bot جاهز: {bot.user}")

# أمر تشغيل الأغنية أو إضافتها للقائمة
@bot.command()
async def play(ctx, *, query):
    """ابعت الأغنية بالاسم أو الرابط"""
    with yt_dlp.YoutubeDL(ytdl_options) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        except Exception:
            await ctx.send("🙁 مفيش نتيجة للبحث")
            return

    url = info['webpage_url']
    title = info['title']

    queue.append((title, url))

    if len(queue) == 1:
        await ctx.send(f"🎶 شغال دلوقتي: [{title}]({url})")
    else:
        await ctx.send(f"✅ تمت إضافة [{title}]({url}) للقائمة. **المركز في الانتظار: {len(queue)}**")

# عرض قائمة الانتظار
@bot.command()
async def queue_list(ctx):
    """عرض قائمة الانتظار"""
    if not queue:
        await ctx.send("القائمة فاضية 😅")
        return

    msg = "**🎵 قائمة الانتظار:**\n"
    for i, (title, url) in enumerate(queue, start=1):
        msg += f"{i}. [{title}]({url})\n"
    await ctx.send(msg)

# أمر تخطي أغنية
@bot.command()
async def skip(ctx):
    """تخطي الأغنية الحالية"""
    if queue:
        skipped = queue.pop(0)
        if queue:
            title, url = queue[0]
            await ctx.send(f"⏭️ تم تخطي [{skipped[0]}]. دلوقتي: [{title}]({url})")
        else:
            await ctx.send(f"⏹️ تم تخطي [{skipped[0]}]. مفيش أغاني تانية دلوقتي.")
    else:
        await ctx.send("مفيش أغاني في القائمة 😅")

# أمر عرض الأغنية الحالية
@bot.command()
async def nowplaying(ctx):
    """عرض الأغنية الحالية"""
    if queue:
        title, url = queue[0]
        await ctx.send(f"🎧 دلوقتي شغال: [{title}]({url})")
    else:
        await ctx.send("مفيش أغنية شغالة دلوقتي 😅")

# أمر مسح القائمة
@bot.command()
async def clear(ctx):
    """مسح كل الأغاني"""
    queue.clear()
    await ctx.send("🗑️ تم مسح كل الأغاني والقائمة فاضية")

# أمر مساعدة
@bot.command()
async def help(ctx):
    msg = """
**🎵 أوامر البوت**
!play <اسم أو رابط> : تشغيل الأغنية أو إضافتها للقائمة
!queue_list : عرض قائمة الانتظار
!skip : تخطي الأغنية الحالية
!nowplaying : عرض الأغنية الحالية
!clear : مسح قائمة الانتظار
"""
    await ctx.send(msg)

# ================= Token ==================
token = os.environ.get("DISCORD_TOKEN")  # خلي التوكن سيكرت في Railway
bot.run(token)
