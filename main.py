import os

# ═══════════════════════════════════
# 🔐 Load .env BEFORE importing config
# ═══════════════════════════════════

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

import discord
from discord.ext import commands
from discord import app_commands
import config
from cogs import emoji_loader
import random
from datetime import datetime


# ═══════════════════════════════════
# 🚀 Estrada BOT
# ═══════════════════════════════════

class EstradaBot(commands.Bot):

    def __init__(self):
        intents = discord.Intents.all()

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

        self._persistent_views_registered = False


    async def setup_hook(self):

        # ═══════════════════════════════════
        # 📦 Load Cogs
        # ═══════════════════════════════════

        for file in os.listdir("./cogs"):

            if file.endswith(".py") and not file.startswith("_"):

                try:
                    await self.load_extension(
                        f"cogs.{file[:-3]}"
                    )

                    print(f"✅ Loaded cog: {file}")

                except Exception as e:

                    print(
                        f"❌ Failed to load cog {file}: {e}"
                    )


        # ═══════════════════════════════════
        # 🎫 Ticket Persistent Views
        # ═══════════════════════════════════

        try:

            from cogs.tickets import (
                TicketCreateView,
                TicketControlView
            )

            self.add_view(TicketCreateView())
            self.add_view(TicketControlView())

            print("✅ Ticket views registered")

        except Exception as e:

            print(
                f"⚠️ Ticket views: {e}"
            )


        # ═══════════════════════════════════
        # ✅ Verify Persistent View
        # ═══════════════════════════════════

        try:

            from cogs.verify import VerifyView

            self.add_view(
                VerifyView()
            )

            print("✅ Verify view registered")

        except Exception as e:

            print(
                f"⚠️ Verify view: {e}"
            )


        # ═══════════════════════════════════
        # 🔊 Voice Control View
        # ═══════════════════════════════════

        try:

            from cogs.create_voice import VoiceControlView

            self.add_view(
                VoiceControlView()
            )

            print(
                "✅ Voice control view registered"
            )

        except Exception as e:

            print(
                f"⚠️ Voice control view: {e}"
            )


        # ═══════════════════════════════════
        # 🛍️ Resources Views
        # ═══════════════════════════════════

        try:

            from cogs.resources import (
                ResourceReviewView,
                ResourceSubmitPanelView
            )

            self.add_view(
                ResourceReviewView()
            )

            self.add_view(
                ResourceSubmitPanelView()
            )

            print(
                "✅ Resource views registered"
            )

        except Exception as e:

            print(
                f"⚠️ Resource views: {e}"
            )


        print(
            "✅ Persistent views registered"
        )


        # ═══════════════════════════════════
        # ⚡ Sync Slash Commands
        # ═══════════════════════════════════

        try:

            await self.tree.sync()

            print(
                "✅ Slash commands synced globally"
            )

        except Exception as e:

            print(
                f"❌ Slash command sync error: {e}"
            )


    # ═══════════════════════════════════
    # 📝 Register Apply Views
    # ═══════════════════════════════════

    async def _register_apply_views(self):

        try:

            from cogs.apply_system import (
                ApplyButtonView,
                get_kind_cfg
            )

            count = 0

            for guild in self.guilds:

                for kind in (
                    "staff",
                    "whitelist"
                ):

                    cfg = get_kind_cfg(
                        guild.id,
                        kind
                    )

                    if cfg:

                        self.add_view(
                            ApplyButtonView(
                                kind,
                                cfg
                            )
                        )

                        count += 1


            print(
                f"✅ Apply panel views registered ({count})"
            )

        except Exception as e:

            print(
                f"⚠️ Apply panel views: {e}"
            )


    # ═══════════════════════════════════
    # 🟢 Bot Ready
    # ═══════════════════════════════════

    async def on_ready(self):

        if not self._persistent_views_registered:

            await self._register_apply_views()

            self._persistent_views_registered = True


        print(
            f"""
╔══════════════════════════════════╗
║     🚀 {config.BOT_NAME}
║ 🌐 Server: {config.SERVER_NAME}
║ ⚡ {self.user}
║ 📊 Servers: {len(self.guilds)}
║ 👥 Users: {len(self.users)}
╚══════════════════════════════════╝
            """
        )


# ═══════════════════════════════════
# 🤖 Create Bot
# ═══════════════════════════════════

bot = EstradaBot()


# ═══════════════════════════════════
# 🏓 PING COMMAND
# ═══════════════════════════════════

@bot.tree.command(
    name="ping",
    description="🏓 Check bot response speed"
)
async def ping(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="🏓 Pong!",
        description=(
            f"Latency: "
            f"`{round(bot.latency * 1000)}ms`"
        ),
        color=config.EMBED_COLOR
    )

    embed.set_footer(
        text=config.SERVER_NAME
    )

    await interaction.response.send_message(
        embed=embed
    )


# ═══════════════════════════════════
# 📚 HELP SECTIONS
# ═══════════════════════════════════

HELP_SECTIONS = [

    {
        "key": "admin",
        "title": "Administration",
        "emoji": "🛡️",
        "app_emoji": "80271admin",
        "description":
            "أوامر إشراف كاملة: حظر، طرد، كتم، تحذير، مسح الرسائل، قفل/فتح الروم وإدارة الرتب بشكل احترافي",
        "value": (
            "› `/ban` `/kick` — طرد أو حذف عضو\n"
            "› `/mute` `/unmute` — كتم أو رفع الكتم\n"
            "› `/warn` — إعطاء تحذير\n"
            "› `/clear` — مسح رسائل\n"
            "› `/lock` `/unlock` — قفل أو فتح الروم\n"
            "› `/slowmode` — ضبط السلو مود\n"
            "› `/role add` `/role remove` — إدارة الرتب"
        ),
    },

    {
        "key": "tickets",
        "title": "Tickets",
        "emoji": "🎫",
        "app_emoji": "29909ticket",
        "description":
            "نظام تذاكر متكامل: تفعيل، تعديل، إلغاء، إضافة أعضاء وإغلاق التذاكر بسهولة تامة",
        "value": (
            "› `/ticket setup` — تفعيل نظام التذاكر\n"
            "› `/ticket update` — تعديل الإعدادات\n"
            "› `/ticket remove` — إلغاء النظام\n"
            "› `/ticket-add` — إضافة عضو للتذكرة\n"
            "› `/ticket-close` — إغلاق التذكرة"
        ),
    },

    {
        "key": "welcome",
        "title": "Welcome, Boost & Subscribe",
        "emoji": "🏠",
        "app_emoji": "11757home",
        "description":
            "رسائل ترحيب مخصصة، إشعارات البوست وتفعيل الاشتراكات مع معاينة مباشرة قبل النشر",
        "value": (
            "› `/welcome setup` `/welcome update` `/welcome remove`\n"
            "› `/welcome preview` `/welcome info`\n"
            "› `/boost setup` `/boost update` `/boost remove`\n"
            "› `/subscribe setup` `/subscribe update` `/subscribe remove`"
        ),
    },

    {
        "key": "applications",
        "title": "Applications",
        "emoji": "📝",
        "app_emoji": "32535applicationapprivedids",
        "description":
            "استقبل ودقق طلبات الانضمام لفريق الـ Staff أو قائمة الـ Whitelist بخطوات واضحة",
        "value": (
            "› `/setup apply` — طلبات Staff / Whitelist\n"
            "› `/setup guide` — دليل إعداد البوت الكامل"
        ),
    },

    {
        "key": "emojis",
        "title": "Emojis",
        "emoji": "🙂",
        "app_emoji": "19991colorroledotspackids",
        "description":
            "انسخ إيموجي واحد أو كل إيموجيات سيرفر آخر، أو ارفع ZIP كامل بضغطة واحدة",
        "value": (
            "› `/emoji steal` — نسخ إيموجي واحد\n"
            "› `/emoji stealall` — نسخ كل إيموجيات سيرفر آخر\n"
            "› `/emoji uploadzip` — رفع ZIP فيه صور إيموجيات\n"
            "› `/emoji list` `/emoji delete` — عرض أو حذف"
        ),
    },

    {
        "key": "ai",
        "title": "AI",
        "emoji": "🤖",
        "app_emoji": "95805bot",
        "description":
            "اسأل الذكاء الاصطناعي أي سؤال واحصل على جواب فوري داخل السيرفر مباشرة",
        "value": (
            "› `/ai ask` — اسأل الـ AI أي سؤال\n"
            "› `/ai clear` — امسح سجل محادثتك"
        ),
    },

    {
        "key": "stats",
        "title": "Server Stats",
        "emoji": "📊",
        "app_emoji": "41378statistiques",
        "description":
            "رومات تعرض عدد الأعضاء والإحصائيات بشكل حي وتتحدث تلقائياً بدون تدخل يدوي",
        "value": (
            "› `/serverstats setup` — إنشاء رومات إحصائيات حية\n"
            "› `/serverstats update` — تحديث فوري\n"
            "› `/serverstats remove` — حذف الرومات"
        ),
    },

    {
        "key": "general",
        "title": "General",
        "emoji": "⭐",
        "app_emoji": "9275yellowstar",
        "description":
            "بروفايلك، رصيدك، مكافأة يومية، رتب بالرياكشن ورتب تلقائية من قائمة اختيار",
        "value": (
            "› `/ping` `/help` `/time` `/report`\n"
            "› `/profile` `/random` `/top` `/daily` `/balance`\n"
            "› `/rr add` `/rr remove` `/rr list` `/rr clear` — رتب بالرياكشن"
        ),
    },

    {
        "key": "voice",
        "title": "Voice",
        "emoji": "🔊",
        "app_emoji": "15830voicechannelgreenalt",
        "description":
            "أنشئ نظام Join-to-Create يخلي كل عضو يصنع الروم الصوتي ديالو تلقائياً",
        "value":
            "› `/voicepanel setup` — نظام Join-to-Create الصوتي",
    },

    {
        "key": "resources",
        "title": "Resources",
        "emoji": "🛍️",
        "app_emoji": "90665shoppingcart",
        "description":
            "اقترح سكريبت أو بوت أو بلوگين، وتابع مراجعته ونشره في الكاتيغوري المناسبة",
        "value": (
            "› `/resource submit` — اقترح مورد (سكريبت/بوت/بلوگين...)\n"
            "› `/resource list` `/resource search`\n"
            "› `/resource setup` — (Admin) ضبط رومات المراجعة\n"
            "› `/resource setpublish` — (Admin) روم نشر لكل كاتيغوري"
        ),
    },

    {
        "key": "announcements",
        "title": "Announcements",
        "emoji": "📢",
        "app_emoji": "6619megaphone",
        "description":
            "أرسل إعلان أو embed باسم البوت، أو رسالة خاصة لكل أعضاء رتبة معينة",
        "value": (
            "› `/say` — إرسال رسالة/embed باسم البوت، أو DM لرتبة\n"
            "› `/notify` — DM لكل أعضاء رتبة معينة"
        ),
    },
]


# ═══════════════════════════════════
# 😀 Section Emoji
# ═══════════════════════════════════

def _section_emoji(section: dict):

    return (
        emoji_loader.get_obj(
            section["app_emoji"]
        )
        or section["emoji"]
    )


# ═══════════════════════════════════
# 📋 Help Select
# ═══════════════════════════════════

class HelpSelect(discord.ui.Select):

    def __init__(
        self,
        active_key: str | None = None
    ):

        options = [

            discord.SelectOption(
                label=section["title"],
                value=section["key"],
                description=section["description"],
                emoji=_section_emoji(section),
                default=(
                    section["key"] == active_key
                ),
            )

            for section in HELP_SECTIONS
        ]

        super().__init__(
            placeholder="Command list...",
            options=options,
            custom_id="help_section_select",
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.edit_message(
            view=HelpLayoutView(
                active_key=self.values[0]
            )
        )


# ═══════════════════════════════════
# 📖 Help Layout
# ═══════════════════════════════════

class HelpLayoutView(discord.ui.LayoutView):

    def __init__(
        self,
        active_key: str | None = None
    ):

        super().__init__(
            timeout=180
        )

        section = next(
            (
                s for s in HELP_SECTIONS
                if s["key"] == active_key
            ),
            None
        )


        header_text = (
            f"**{emoji_loader.get('38083rules') or '📖'} "
            f"{config.BOT_NAME} — Commands**\n"
            f"-# {config.SERVER_NAME}"
        )


        header_section = discord.ui.Section(
            discord.ui.TextDisplay(
                header_text
            ),
            accessory=discord.ui.Thumbnail(
                media=bot.user.display_avatar.url
            ),
        )


        if section:

            body_text = (
                f"**{_section_emoji(section)} "
                f"{section['title']}**\n"
                f"{section['value']}"
            )

        else:

            body_text = (
                "اختار قسم من المنيو تحت "
                "باش تشوف الأوامر ديالو "
                f"{emoji_loader.get('34996chercher') or '🔍'}"
            )


        footer_text = (
            f"-# {config.SERVER_NAME}"
        )


        items = [

            header_section,

            discord.ui.Separator(),

            discord.ui.TextDisplay(
                body_text
            ),

            discord.ui.Separator(),

            discord.ui.ActionRow(
                HelpSelect(
                    active_key=active_key
                )
            ),

            discord.ui.TextDisplay(
                footer_text
            ),
        ]


        container = discord.ui.Container(
            *items,
            accent_color=config.EMBED_COLOR
        )

        self.add_item(container)


# ═══════════════════════════════════
# 📚 HELP COMMAND
# ═══════════════════════════════════

@bot.tree.command(
    name="help",
    description="📚 List all bot commands"
)
async def help_cmd(
    interaction: discord.Interaction
):

    if not emoji_loader._emoji_cache:

        await emoji_loader.load_emojis(
            bot
        )

    await interaction.response.send_message(
        view=HelpLayoutView()
    )


# ═══════════════════════════════════
# 🚨 REPORT COMMAND
# ═══════════════════════════════════

@bot.tree.command(
    name="report",
    description="🚨 Report a member"
)
@app_commands.describe(
    member="The member to report",
    reason="Reason for the report"
)
async def report(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str
):

    embed = discord.Embed(
        title="🚨 Report",
        color=config.ERROR_COLOR
    )

    embed.add_field(
        name="Reported by",
        value=interaction.user.mention
    )

    embed.add_field(
        name="Reported member",
        value=member.mention
    )

    embed.add_field(
        name="Reason",
        value=reason
    )

    embed.set_footer(
        text=config.SERVER_NAME
    )

    await interaction.channel.send(
        embed=embed
    )

    await interaction.response.send_message(
        "✅ Report sent successfully",
        ephemeral=True
    )


# ═══════════════════════════════════
# 🎲 RANDOM COMMAND
# ═══════════════════════════════════

@bot.tree.command(
    name="random",
    description="🎯 اختيار عشوائي — قاد أو مقاد أو من خياراتك"
)
@app_commands.describe(
    choices="الخيارات مفصولة بفاصلة — اتركها فارغة لاختيار قاد/مقاد"
)
async def random_choice(
    interaction: discord.Interaction,
    choices: str = ""
):

    # Default coin flip

    if not choices.strip():

        result = random.choice(
            [
                "قاد ✅",
                "مقاد ❌"
            ]
        )

        is_yes = result.startswith(
            "قاد"
        )

        color = (
            config.SUCCESS_COLOR
            if is_yes
            else config.ERROR_COLOR
        )

        banner = (
            "🟢 **قاد** — مفعول!"
            if is_yes
            else
            "🔴 **مقاد** — موقوف!"
        )


        embed = discord.Embed(
            title="🎲 Estrada Random",
            description=(
                "```\n"
                "[ قاد ]  vs  [ مقاد ]\n"
                "```\n"
                f"## {banner}"
            ),
            color=color,
            timestamp=datetime.now(),
        )


        embed.set_author(
            name="Estrada — Random Picker",
            icon_url=bot.user.display_avatar.url
        )

        embed.set_footer(
            text=(
                f"طلبه: "
                f"{interaction.user.display_name} | "
                f"{config.SERVER_NAME}"
            ),
            icon_url=interaction.user.display_avatar.url
        )


        await interaction.response.send_message(
            embed=embed
        )

        return


    # Custom choices

    options = [
        c.strip()
        for c in choices.split(",")
        if c.strip()
    ]


    if len(options) < 2:

        await interaction.response.send_message(

            embed=discord.Embed(
                description=(
                    "❌ أدخل خيارين على الأقل "
                    "مفصولين بفاصلة."
                ),
                color=config.ERROR_COLOR
            ),

            ephemeral=True
        )

        return


    result = random.choice(
        options
    )


    opts_display = "\n".join(

        f"{'➡️' if o == result else '  •'} {o}"

        for o in options
    )


    embed = discord.Embed(
        title="🎲 Estrada Random — Custom Pick",
        description=(
            f"```\n"
            f"{opts_display}\n"
            f"```\n"
            f"## ✅ النتيجة: **{result}**"
        ),
        color=config.EMBED_COLOR,
        timestamp=datetime.now()
    )


    embed.set_author(
        name="Estrada — Random Picker",
        icon_url=bot.user.display_avatar.url
    )


    embed.set_footer(
        text=(
            f"طلبه: "
            f"{interaction.user.display_name} | "
            f"{config.SERVER_NAME}"
        ),
        icon_url=interaction.user.display_avatar.url
    )


    await interaction.response.send_message(
        embed=embed
    )


# ═══════════════════════════════════
# 🕐 TIME COMMAND
# ═══════════════════════════════════

@bot.tree.command(
    name="time",
    description="🕐 Show current time"
)
async def time_cmd(
    interaction: discord.Interaction
):

    now = datetime.now()

    await interaction.response.send_message(
        f"🕐 <t:{int(now.timestamp())}:F>"
    )


# ═══════════════════════════════════
# 🚀 START BOT
# ═══════════════════════════════════

if __name__ == "__main__":

    if not config.TOKEN:
        raise RuntimeError(
            "❌ Discord token is missing in config.py"
        )

    print(
        f"🔐 Discord token loaded "
        f"({len(config.TOKEN)} characters)"
    )

    bot.run(config.TOKEN)

