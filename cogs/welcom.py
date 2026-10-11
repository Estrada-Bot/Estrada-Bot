"""
Welcome System — Estrada
Short, clean welcome embed with optional animated banner.
"""

import discord
from discord.ext import commands
from discord import app_commands
import config
import settings
from cogs import emoji_loader
import requests
from io import BytesIO
import asyncio
from datetime import datetime
import db

WELCOME_COLLECTION = "welcome_settings"

def load_welcome() -> dict:
    return db.load(WELCOME_COLLECTION)

def save_welcome(data: dict):
    db.save(WELCOME_COLLECTION, data)


def _ordinal(n: int) -> str:
    """1 -> 1st, 2 -> 2nd, 3 -> 3rd, 4 -> 4th ..."""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _fill_vars(text: str, member: discord.Member, invite: "discord.Invite | None" = None) -> str:
    """يعوض كل المتغيرات المتاحة فـ نص الرسالة بالقيم الحقيقية ديال العضو
    والسيرفر. زيد أي متغير جديد هنا مرة وحدة، وغايخدم فـ setup/update/preview
    وفـ on_member_join بلا ما تحتاج تبدل شي حاجة أخرى."""
    guild = member.guild
    account_age_days = (datetime.now(member.created_at.tzinfo) - member.created_at).days
    inviter_mention = invite.inviter.mention if (invite and invite.inviter) else "—"
    invite_code = invite.code if invite else "—"
    return (
        text
        .replace("{user}", member.mention)
        .replace("{mention}", member.mention)
        .replace("{name}", member.display_name)
        .replace("{username}", member.name)
        .replace("{tag}", str(member))
        .replace("{id}", str(member.id))
        .replace("{server}", guild.name)
        .replace("{count}", str(guild.member_count))
        .replace("{ordinal_count}", _ordinal(guild.member_count))
        .replace("{boosts}", str(guild.premium_subscription_count))
        .replace("{owner}", str(guild.owner) if guild.owner else "—")
        .replace("{account_age}", f"{account_age_days} يوم")
        .replace("{created_at}", f"<t:{int(member.created_at.timestamp())}:D>")
        .replace("{invite}", inviter_mention)
        .replace("{inviter}", inviter_mention)
        .replace("{invite_code}", invite_code)
    )


class Welcome(commands.Cog):
    welcome_group = app_commands.Group(
        name="welcome",
        description="👋 Manage the welcome system",
        default_permissions=discord.Permissions(administrator=True),
    )

    def __init__(self, bot):
        self.bot = bot
        # guild_id -> {invite_code: discord.Invite} — kept independently from
        # cogs/invites.py's own cache so there's no race between the two
        # cogs' on_member_join listeners (order between cogs isn't guaranteed).
        self.invite_cache: dict[int, dict[str, discord.Invite]] = {}

    async def _fetch_invites(self, guild: discord.Guild) -> dict[str, discord.Invite]:
        try:
            invites = await guild.invites()
        except discord.Forbidden:
            return {}
        return {inv.code: inv for inv in invites}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.invite_cache[guild.id] = await self._fetch_invites(guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.invite_cache[guild.id] = await self._fetch_invites(guild)

    async def _detect_invite(self, member: discord.Member) -> discord.Invite | None:
        """كيقارن لائحة الدعوات قبل وبعد الانضمام باش يعرف شكون الدعوة
        المستعملة، بلا ما يعتمد على cogs/invites.py (تفادي أي سباق توقيت
        بين الكوجين)."""
        guild = member.guild
        before = self.invite_cache.get(guild.id, {})
        after = await self._fetch_invites(guild)
        self.invite_cache[guild.id] = after

        for code, old_invite in before.items():
            new_invite = after.get(code)
            if new_invite is None:
                return old_invite  # single-use invite just got consumed
            if new_invite.uses > old_invite.uses:
                return new_invite
        return None

    # ─── on_member_join ─────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        ws = load_welcome()
        guild_id = str(member.guild.id)
        cfg = ws.get(guild_id)
        if not cfg:
            return

        # Auto role
        auto_role_id = cfg.get("auto_role_id")
        if auto_role_id:
            role = member.guild.get_role(auto_role_id)
            if role:
                try:
                    await member.add_roles(role)
                except Exception:
                    pass

        ch_id = cfg.get("channel_id")
        channel = self.bot.get_channel(ch_id) if ch_id else None
        if not channel:
            return

        try:
            banner_url = cfg.get("banner_url") or ""
            custom_msg = cfg.get("message") or ""
            used_invite = await self._detect_invite(member)

            if custom_msg:
                desc = _fill_vars(custom_msg, member, used_invite)
            else:
                desc = f"Welcome {member.mention} 👋\n**Member #{member.guild.member_count}**"

            embed = discord.Embed(
                description=desc,
                color=0x5865F2,
                timestamp=datetime.now()
            )
            embed.set_author(
                name=f"Welcome to {member.guild.name}!",
                icon_url=member.display_avatar.url
            )
            embed.set_thumbnail(url=member.display_avatar.url)

            if banner_url:
                embed.set_image(url=banner_url)

            embed.set_footer(
                text=f"{config.SERVER_NAME}",
                icon_url=self.bot.user.display_avatar.url
            )

            await channel.send(content=member.mention, embed=embed)

        except Exception as e:
            print(f"[Welcome] Error: {e}")
            try:
                await channel.send(f"👋 Welcome {member.mention} to **{member.guild.name}**!")
            except Exception:
                pass

    # ─── /welcome setup ──────────────────────────────────────────────────────
    @welcome_group.command(name="setup", description="⚙️ Set up the welcome system")
    @app_commands.describe(
        channel="Channel where welcome messages are posted",
        auto_role="Role automatically given to new members (optional)",
        log_channel="Channel for join logs (optional)",
        message="Custom message — variables: {user} {mention} {name} {username} {tag} {id} {server} {count} {ordinal_count} {boosts} {owner} {account_age} {created_at} {invite} {invite_code} (optional)",
        banner_url="Animated or static banner image URL (optional)",
    )
    async def welcome_setup(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        auto_role: discord.Role = None,
        log_channel: discord.TextChannel = None,
        message: str = None,
        banner_url: str = None,
    ):
        data = {
            "channel_id": channel.id,
            "auto_role_id": auto_role.id if auto_role else None,
            "log_channel_id": log_channel.id if log_channel else None,
            "message": message or "",
            "banner_url": banner_url or "",
        }
        ws = load_welcome()
        ws[str(interaction.guild_id)] = data
        save_welcome(ws)
        await interaction.response.send_message(
            embed=self._summary_embed("✅ Welcome System Set Up!", channel, auto_role, log_channel, data["banner_url"], data["message"]),
            ephemeral=True
        )

    # ─── /welcome update ─────────────────────────────────────────────────────
    @welcome_group.command(name="update", description="✏️ Update welcome settings")
    @app_commands.describe(
        channel="New welcome channel (optional)",
        auto_role="New auto role (optional)",
        log_channel="New log channel (optional)",
        message="New custom message — variables: {user} {mention} {name} {username} {tag} {id} {server} {count} {ordinal_count} {boosts} {owner} {account_age} {created_at} {invite} {invite_code} (optional)",
        banner_url="New banner URL — send 'reset' to clear it (optional)",
    )
    async def welcome_update(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel = None,
        auto_role: discord.Role = None,
        log_channel: discord.TextChannel = None,
        message: str = None,
        banner_url: str = None,
    ):
        ws = load_welcome()
        guild_id = str(interaction.guild_id)
        cfg = ws.get(guild_id)
        if not cfg:
            await interaction.response.send_message("❌ Welcome system is not set up yet. Use `/welcome setup` first.", ephemeral=True)
            return

        if channel:      cfg["channel_id"]    = channel.id
        if auto_role:    cfg["auto_role_id"]  = auto_role.id
        if log_channel:  cfg["log_channel_id"]= log_channel.id
        if message:      cfg["message"]       = message
        if banner_url is not None:
            cfg["banner_url"] = "" if banner_url.lower() == "reset" else banner_url

        ws[guild_id] = cfg
        save_welcome(ws)

        ch     = interaction.guild.get_channel(cfg.get("channel_id") or 0)
        role   = interaction.guild.get_role(cfg.get("auto_role_id") or 0)
        log_ch = interaction.guild.get_channel(cfg.get("log_channel_id") or 0)
        await interaction.response.send_message(
            embed=self._summary_embed("✅ Welcome Settings Updated!", ch, role, log_ch, cfg.get("banner_url", ""), cfg.get("message", "")),
            ephemeral=True
        )

    # ─── /welcome remove ─────────────────────────────────────────────────────
    @welcome_group.command(name="remove", description="🗑️ Remove the welcome system setup")
    async def welcome_remove(self, interaction: discord.Interaction):
        ws = load_welcome()
        ws.pop(str(interaction.guild_id), None)
        save_welcome(ws)
        embed = discord.Embed(
            title="🗑️ Welcome System Removed",
            description="The welcome system has been disabled.",
            color=config.ERROR_COLOR
        )
        embed.set_footer(text=f"{config.SERVER_NAME}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ─── /welcome preview ────────────────────────────────────────────────────
    @welcome_group.command(name="preview", description="🧪 Preview the welcome message")
    async def welcome_preview(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        ws = load_welcome()
        cfg = ws.get(str(interaction.guild_id), {})
        channel = interaction.channel

        banner_url = cfg.get("banner_url") or ""
        custom_msg = cfg.get("message") or ""
        desc = (
            _fill_vars(custom_msg, interaction.user)
            if custom_msg
            else f"Welcome {interaction.user.mention} 👋\n**Member #{interaction.guild.member_count}**"
        )

        embed = discord.Embed(description=desc, color=0x5865F2, timestamp=datetime.now())
        embed.set_author(name=f"Welcome to {interaction.guild.name}!", icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        if banner_url:
            embed.set_image(url=banner_url)
        embed.set_footer(text=f"- {config.BOT_NAME}", icon_url=self.bot.user.display_avatar.url)

        await channel.send(content=f"🧪 {interaction.user.mention}", embed=embed)
        await interaction.followup.send("✅ Preview sent!", ephemeral=True)

    # ─── /welcome info ───────────────────────────────────────────────────────
    @welcome_group.command(name="info", description="📊 Show current welcome system settings")
    async def welcome_info(self, interaction: discord.Interaction):
        ws = load_welcome()
        cfg = ws.get(str(interaction.guild_id), {})
        ch     = interaction.guild.get_channel(cfg.get("channel_id") or 0)
        log_ch = interaction.guild.get_channel(cfg.get("log_channel_id") or 0)
        role   = interaction.guild.get_role(cfg.get("auto_role_id") or 0)
        await interaction.response.send_message(
            embed=self._summary_embed("📊 Welcome System Settings", ch, role, log_ch, cfg.get("banner_url", ""), cfg.get("message", "")),
            ephemeral=True
        )

    # ─── helper ─────────────────────────────────────────────────────────────
    def _summary_embed(self, title, channel, auto_role, log_channel, banner_url, message) -> discord.Embed:
        embed = discord.Embed(title=title, color=config.SUCCESS_COLOR)
        embed.add_field(name="📢 Channel",    value=channel.mention if channel else "❌ Not set", inline=True)
        embed.add_field(name="📋 Log",        value=log_channel.mention if log_channel else "None", inline=True)
        embed.add_field(name="🏷️ Auto Role",  value=auto_role.mention if auto_role else "None", inline=True)
        embed.add_field(name="🖼️ Banner",     value=f"[Link]({banner_url})" if banner_url else "None (embed only)", inline=True)
        embed.add_field(name="✏️ Message",    value=message[:200] if message else "Default", inline=False)
        embed.set_footer(text=f"{config.BOT_NAME} | Use /welcome preview to test")
        return embed


async def setup(bot):
    await bot.add_cog(Welcome(bot))
