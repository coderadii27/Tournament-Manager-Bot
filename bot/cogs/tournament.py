"""Tournament control panel cog (?t)."""

from __future__ import annotations

import discord
from discord.ext import commands

from state import get_guild, save_guild, update_guild

BRAND_COLOR = 0x9B5CF6
ACCENT_COLOR = 0x00E5FF

CATEGORY_NAME = "🏆 BRN ESPORTS"

CHANNEL_NAMES = [
    "—͟͞͞-⨳〢info",
    "—͟͞͞-⨳〢updates",
    "—͟͞͞-⨳〢rules",
    "—͟͞͞-⨳〢how-to-register",
    "—͟͞͞-⨳〢registration-format",
    "—͟͞͞-⨳〢registration",
    "—͟͞͞-⨳〢confirm-teams",
    "—͟͞͞-⨳〢roadmaps",
    "—͟͞͞-⨳〢schedule",
    "—͟͞͞-⨳〢point-table",
    "—͟͞͞-⨳〢query",
]

# Channels users can ONLY view (not send) when tournament is running
LOCKED_KEYWORDS = (
    "info", "updates", "rules", "how-to-register", "registration-format",
    "confirm-teams", "roadmaps", "schedule", "point-table",
)
# Channels users CAN send in when tournament is running
OPEN_KEYWORDS = ("registration", "query")

REGISTRATION_FORMAT = """```
TEAM NAME -

PLAYER 1 (IGL) :
CHARACTER ID :
DISCORD TAG :

PLAYER 2 :
CHARACTER ID :
DISCORD TAG :

PLAYER 3 :
CHARACTER ID :
DISCORD TAG :

PLAYER 4 :
CHARACTER ID :
DISCORD TAG :

PLAYER 5 :
CHARACTER ID :
DISCORD TAG :
```"""


def panel_embed(g: dict) -> discord.Embed:
    status = "🟢 Running" if g.get("running") and not g.get("paused") else (
        "🟡 Paused" if g.get("paused") else "⚪ Idle"
    )
    embed = discord.Embed(
        title="🏆 BRN ESPORTS — Tournament Control Panel",
        description=(
            "Welcome to the **official tournament hub**.\n"
            "Use the buttons below to manage every part of your event.\n\u200b"
        ),
        color=BRAND_COLOR,
    )
    embed.add_field(name="Tournament", value=f"`{g.get('tournament_name', 'EliteQ-tourny')}`", inline=True)
    embed.add_field(name="Slots", value=f"`{len(g.get('teams', []))}/{g.get('max_slots', 16)}`", inline=True)
    embed.add_field(name="Team Size", value=f"`{g.get('team_size', 5)} players`", inline=True)
    embed.add_field(name="Status", value=status, inline=True)
    embed.add_field(name="Groups", value=f"`{len(g.get('groups', {}))}`", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.set_footer(text="BRN ESPORTS OFFICIAL BOT")
    return embed


# ──────────────────────────────────────────────────────────────────────────────
# Channel helpers
# ──────────────────────────────────────────────────────────────────────────────

def _is_locked(name: str) -> bool:
    return any(k in name for k in LOCKED_KEYWORDS)


def _is_open(name: str) -> bool:
    return any(k in name for k in OPEN_KEYWORDS)


def _tournament_channels(guild: discord.Guild) -> list[discord.TextChannel]:
    return [c for c in guild.text_channels if c.name in CHANNEL_NAMES]


async def ensure_category_and_channels(guild: discord.Guild) -> tuple[discord.CategoryChannel, list[discord.TextChannel], dict]:
    """Create the category + all 11 channels if missing. Returns (category, channels, ids)."""
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if category is None:
        category = await guild.create_category(CATEGORY_NAME, reason="Tournament setup")

    ids = {"registration_channel_id": None, "confirm_channel_id": None, "format_channel_id": None}
    channels: list[discord.TextChannel] = []
    for name in CHANNEL_NAMES:
        ch = discord.utils.get(guild.text_channels, name=name)
        if ch is None:
            ch = await guild.create_text_channel(name, category=category)
        channels.append(ch)
        if "registration-format" in name:
            ids["format_channel_id"] = ch.id
        elif "registration" in name:
            ids["registration_channel_id"] = ch.id
        if "confirm-teams" in name:
            ids["confirm_channel_id"] = ch.id
    return category, channels, ids


async def apply_running_perms(guild: discord.Guild) -> None:
    """Locked channels: view-only for @everyone. Open channels: view + send."""
    everyone = guild.default_role
    for ch in _tournament_channels(guild):
        if _is_open(ch.name):
            ow = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, add_reactions=True)
        elif _is_locked(ch.name):
            ow = discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True, add_reactions=False)
        else:
            continue
        try:
            await ch.set_permissions(everyone, overwrite=ow, reason="Tournament running — applying permissions")
        except discord.Forbidden:
            pass


async def apply_paused_perms(guild: discord.Guild) -> None:
    """Lock ALL tournament channels: users can only view, never send."""
    everyone = guild.default_role
    ow = discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True, add_reactions=False)
    for ch in _tournament_channels(guild):
        try:
            await ch.set_permissions(everyone, overwrite=ow, reason="Tournament paused — locking channels")
        except discord.Forbidden:
            pass


async def post_to_all_tournament_channels(guild: discord.Guild, embed: discord.Embed) -> int:
    sent = 0
    for ch in _tournament_channels(guild):
        try:
            await ch.send(embed=embed)
            sent += 1
        except Exception:
            pass
    return sent


async def post_format_message(guild: discord.Guild) -> None:
    fch = discord.utils.get(guild.text_channels, name="—͟͞͞-⨳〢registration-format")
    if fch is None:
        return
    async for msg in fch.history(limit=20):
        if msg.author == guild.me and "TEAM NAME" in (msg.content or ""):
            return
    embed = discord.Embed(
        title="📋 Registration Format",
        description="Copy the format below, fill it in completely, and post it in the registration channel.",
        color=BRAND_COLOR,
    )
    embed.set_footer(text="BRN ESPORTS OFFICIAL BOT")
    await fch.send(embed=embed)
    await fch.send(REGISTRATION_FORMAT)


# ──────────────────────────────────────────────────────────────────────────────
# Modals
# ──────────────────────────────────────────────────────────────────────────────

class CreateTournamentModal(discord.ui.Modal, title="Create Tournament"):
    name = discord.ui.TextInput(label="Tournament Name", default="EliteQ-tourny", max_length=64)
    team_size = discord.ui.TextInput(label="Team Size (players per team)", default="5", max_length=2)
    slots = discord.ui.TextInput(label="Total Slots (e.g. 16, 32, 64)", default="16", max_length=3)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            ts = int(str(self.team_size))
            sl = int(str(self.slots))
            assert 1 <= ts <= 10 and 2 <= sl <= 256
        except Exception:
            await interaction.response.send_message("Invalid numbers provided.", ephemeral=True)
            return
        update_guild(
            interaction.guild_id,
            {
                "tournament_name": str(self.name),
                "team_size": ts,
                "max_slots": sl,
                "running": False,
                "paused": False,
                "teams": [],
                "groups": {},
            },
        )
        g = get_guild(interaction.guild_id)
        embed = discord.Embed(
            title="✅ Tournament Created",
            description=f"**{g['tournament_name']}** is ready.\nTeam Size: `{g['team_size']}` • Slots: `{g['max_slots']}`",
            color=ACCENT_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ManageGroupsModal(discord.ui.Modal, title="Manage Groups"):
    group_count = discord.ui.TextInput(label="Number of Groups", default="2", max_length=2)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            n = int(str(self.group_count))
            assert 1 <= n <= 32
        except Exception:
            await interaction.response.send_message("Invalid group count.", ephemeral=True)
            return
        g = get_guild(interaction.guild_id)
        teams = list(g.get("teams", []))
        groups: dict[str, list] = {chr(ord("A") + i): [] for i in range(n)}
        for idx, t in enumerate(teams):
            key = chr(ord("A") + (idx % n))
            groups[key].append(t.get("name", f"Team {idx + 1}"))
        g["groups"] = groups
        save_guild(interaction.guild_id, g)
        embed = discord.Embed(title="📊 Groups Distributed", color=BRAND_COLOR)
        for key, members in groups.items():
            embed.add_field(name=f"Group {key}", value="\n".join(f"• {m}" for m in members) if members else "*empty*", inline=True)
        embed.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ──────────────────────────────────────────────────────────────────────────────
# View
# ──────────────────────────────────────────────────────────────────────────────

class TournamentPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Tournament", style=discord.ButtonStyle.success, emoji="🛠️", custom_id="t:create", row=0)
    async def create_btn(self, interaction: discord.Interaction, _b):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You need **Manage Server** permission.", ephemeral=True)
            return
        await interaction.response.send_modal(CreateTournamentModal())

    @discord.ui.button(label="Create Channels", style=discord.ButtonStyle.primary, emoji="📂", custom_id="t:channels", row=0)
    async def channels_btn(self, interaction: discord.Interaction, _b):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("You need **Manage Channels** permission.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        category, channels, ids = await ensure_category_and_channels(guild)
        await post_format_message(guild)
        await apply_running_perms(guild)
        update_guild(interaction.guild_id, {
            "registration_channel_id": ids["registration_channel_id"],
            "confirm_channel_id": ids["confirm_channel_id"],
        })
        embed = discord.Embed(
            title="📂 Channels Ready",
            description=f"Created/verified **{len(channels)}** channels under **{category.name}** and applied tournament permissions.",
            color=ACCENT_COLOR,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Start Tournament", style=discord.ButtonStyle.success, emoji="▶️", custom_id="t:start", row=1)
    async def start_btn(self, interaction: discord.Interaction, _b):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You need **Manage Server** permission.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        category, channels, ids = await ensure_category_and_channels(guild)
        await post_format_message(guild)
        await apply_running_perms(guild)
        update_guild(interaction.guild_id, {
            "running": True, "paused": False,
            "registration_channel_id": ids["registration_channel_id"],
            "confirm_channel_id": ids["confirm_channel_id"],
        })
        g = get_guild(interaction.guild_id)
        announce = discord.Embed(
            title="▶️ Tournament Started",
            description=(
                f"**{g.get('tournament_name', 'Tournament')}** is now LIVE!\n"
                "All info channels are view-only. Drop your registration in the registration channel.\n"
                "Good luck to all teams! 🏆"
            ),
            color=0x2ECC71,
        )
        announce.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        sent = await post_to_all_tournament_channels(guild, announce)
        await interaction.followup.send(
            f"▶️ Tournament started. Channels ready & locked, announcement posted in **{sent}** channels.",
            ephemeral=True,
        )

    @discord.ui.button(label="Pause Tournament", style=discord.ButtonStyle.secondary, emoji="⏸️", custom_id="t:pause", row=1)
    async def pause_btn(self, interaction: discord.Interaction, _b):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You need **Manage Server** permission.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        g = get_guild(interaction.guild_id)
        new_paused = not g.get("paused", False)
        update_guild(interaction.guild_id, {"paused": new_paused})

        if new_paused:
            await apply_paused_perms(guild)
            embed = discord.Embed(
                title="🔒 Tournament Closed",
                description=(
                    f"**{g.get('tournament_name', 'Tournament')}** has been **paused**.\n"
                    "All channels are now locked. You can only **view**, not send messages.\n"
                    "Please wait for staff to resume the tournament."
                ),
                color=0xE74C3C,
            )
            embed.set_footer(text="BRN ESPORTS OFFICIAL BOT")
            sent = await post_to_all_tournament_channels(guild, embed)
            await interaction.followup.send(
                f"⏸️ Tournament paused. All **{sent}** tournament channels locked.", ephemeral=True
            )
        else:
            await apply_running_perms(guild)
            embed = discord.Embed(
                title="▶️ Tournament Resumed",
                description=(
                    f"**{g.get('tournament_name', 'Tournament')}** is back **LIVE**!\n"
                    "Channels have been unlocked. Game on! 🔥"
                ),
                color=0x2ECC71,
            )
            embed.set_footer(text="BRN ESPORTS OFFICIAL BOT")
            sent = await post_to_all_tournament_channels(guild, embed)
            await interaction.followup.send(
                f"▶️ Tournament resumed. **{sent}** channels unlocked & announced.", ephemeral=True
            )

    @discord.ui.button(label="Manage Groups", style=discord.ButtonStyle.primary, emoji="📊", custom_id="t:groups", row=2)
    async def groups_btn(self, interaction: discord.Interaction, _b):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You need **Manage Server** permission.", ephemeral=True)
            return
        await interaction.response.send_modal(ManageGroupsModal())

    @discord.ui.button(label="Slot Manager", style=discord.ButtonStyle.danger, emoji="🎟️", custom_id="t:slots", row=2)
    async def slots_btn(self, interaction: discord.Interaction, _b):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("You need **Manage Channels** permission.", ephemeral=True)
            return
        cog = interaction.client.get_cog("SlotManager")
        if cog is None:
            await interaction.response.send_message("Slot manager cog not loaded.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        ch = await cog.setup_panel(interaction.guild)
        await interaction.followup.send(
            f"🔒 Private slot manager channel ready: {ch.mention}\n*Only members with **Manage Channels** can see it.*",
            ephemeral=True,
        )


class Tournament(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(TournamentPanelView())

    @commands.command(name="t")
    async def tournament_panel(self, ctx: commands.Context):
        if ctx.guild is None:
            await ctx.reply("Use this in a server.", mention_author=False)
            return
        g = get_guild(ctx.guild.id)
        await ctx.send(embed=panel_embed(g), view=TournamentPanelView())


async def setup(bot: commands.Bot):
    await bot.add_cog(Tournament(bot))
