"""
Rotating Bot Status — Estrada
───────────────────────────────────────
Rotates through many activity names AND rotates between all activity types
(Playing / Watching / Listening to / Streaming / Competing in) automatically.

Add more names in ACTIVITIES — no other code needs to change.
"""

import random
import discord
from discord.ext import commands, tasks

# زيد هنا كلشي لي بغيتي، بلا حد — كيدورو بينهم عشوائي.
ACTIVITIES = [
    "Estrada🪐",
    "the Estrada family",
    "Estrada 🗺️",
    "online 24/7🧿",
    "Discord Server",
    "your next favorite server",
    "SA-MP Server",
    "SA-MP RolePlay",
    "GTA San Andreas MP",
    "YouTube Videos",
    "Twitch Streams",
    "Movies & Series",
    "for new members",
    "everyone chatting",
    "the community grow",
    "/help for commands",
    "🎫 /ticket | Support",
]

# الأنواع اللي غادي يدور بينهم (كلهم موجودين فـ ديسكورد)
ACTIVITY_TYPES = [
    discord.ActivityType.playing,     # Playing ...
    discord.ActivityType.watching,    # Watching ...
    discord.ActivityType.listening,   # Listening to ...
    discord.ActivityType.streaming,   # Streaming ...
    discord.ActivityType.competing,   # Competing in ...
]

STREAM_URL = "https://youtube.com/@ghostx-e2k?si=PqGLAg-KU2C6DMEu"
  # خاص يبقى رابط تويتش/يوتيوب صحيح باش يخدم Streaming
ROTATE_EVERY_SECONDS = 10


def _live_member_count(bot: commands.Bot) -> int:
    return sum(g.member_count or 0 for g in bot.guilds)


class StatusRotator(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.rotate.start()

    def cog_unload(self):
        self.rotate.cancel()

    @tasks.loop(seconds=ROTATE_EVERY_SECONDS)
    async def rotate(self):
        # كل مرة كيختار اسم ونوع عشوائي — كل شي غير مرتبط بالآخر
        activity_name = random.choice(ACTIVITIES)
        activity_type = random.choice(ACTIVITY_TYPES)

        # زيادة عضو مباشر (Live)، فرصة صغيرة تبان بدل الاسم الثابت
        if random.random() < 0.15:
            activity_name = f"{_live_member_count(self.bot)}+ Members"

        if activity_type == discord.ActivityType.streaming:
            # Streaming خاصو discord.Streaming (مع url) — ماخدامش مع Activity العادية
            activity = discord.Streaming(name=activity_name, url=STREAM_URL)
        else:
            activity = discord.Activity(type=activity_type, name=activity_name)

        await self.bot.change_presence(status=discord.Status.online, activity=activity)

    @rotate.before_loop
    async def before_rotate(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(StatusRotator(bot))
