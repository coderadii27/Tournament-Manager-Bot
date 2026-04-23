"""Tournament control panel cog (?t)."""

from __future__ import annotations

import discord
from discord.ext import commands

from state import get_guild, save_guild, update_guild

BRAND_COLOR = 0x9B5CF6
ACCENT_COLOR = 0x00E5FF

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
            description=(
                f"**{g['tournament_name']}** is ready.\n"
                f"Team Size: `{g['team_size']}` • Slots: `{g['max_slots']}`"
            ),
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
            embed.add_field(
                name=f"Group {key}",
                value="\n".join(f"• {m}" for m in members) if members else "*empty*",
                inline=True,
            )
        embed.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class TournamentPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Tournament", style=discord.ButtonStyle.success, emoji="🛠️", custom_id="t:create", row=0)
    async def create_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You need **Manage Server** permission.", ephemeral=True)
            return
        await interaction.response.send_modal(CreateTournamentModal())

    @discord.ui.button(label="Create Channels", style=discord.ButtonStyle.primary, emoji="📂", custom_id="t:channels", row=0)
    async def channels_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("You need **Manage Channels** permission.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="🏆 BRN ESPORTS")
        if category is None:
            category = await guild.create_category("🏆 BRN ESPORTS", reason="Tournament setup")

        created, existing = [], []
        reg_id = None
        confirm_id = None
        format_id = None
        for name in CHANNEL_NAMES:
            ch = discord.utils.get(guild.text_channels, name=name)
            if ch is None:
                ch = await guild.create_text_channel(name, category=category)
                created.append(ch.name)
            else:
                existing.append(ch.name)
            if "registration" in name and "format" not in name:
                reg_id = ch.id
            if "confirm-teams" in name:
                confirm_id = ch.id
            if "registration-format" in name:
                format_id = ch.id

        if format_id is not None:
            fch = guild.get_channel(format_id)
            if fch is not None:
                already_sent = False
                async for msg in fch.history(limit=20):
                    if msg.author == guild.me and "TEAM NAME" in msg.content:
                        already_sent = True
                        break
                if not already_sent:
                    embed = discord.Embed(
                        title="📋 Registration Format",
                        description=(
                            "Copy the format below, fill it in completely, and post it in "
                            "the registration channel."
                        ),
                        color=BRAND_COLOR,
                    )
                    embed.set_footer(text="BRN ESPORTS OFFICIAL BOT")
                    await fch.send(embed=embed)
                    await fch.send(REGISTRATION_FORMAT)

        update_guild(
            interaction.guild_id,
            {"registration_channel_id": reg_id, "confirm_channel_id": confirm_id},
        )

        desc = ""
        if created:
            desc += "**Created:**\n" + "\n".join(f"• {n}" for n in created) + "\n\n"
        if existing:
            desc += "**Already existed:**\n" + "\n".join(f"• {n}" for n in existing)
        embed = discord.Embed(title="📂 Channels Ready", description=desc or "No changes.", color=ACCENT_COLOR)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Start Tournament", style=discord.ButtonStyle.success, emoji="▶️", custom_id="t:start", row=1)
    async def start_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You need **Manage Server** permission.", ephemeral=True)
            return
        update_guild(interaction.guild_id, {"running": True, "paused": False})
        embed = discord.Embed(
            title="▶️ Tournament Started",
            description="Good luck to all teams! Let the battles begin.",
            color=0x2ECC71,
        )
        embed.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Pause Tournament", style=discord.ButtonStyle.secondary, emoji="⏸️", custom_id="t:pause", row=1)
    async def pause_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You need **Manage Server** permission.", ephemeral=True)
            return
        g = get_guild(interaction.guild_id)
        new_paused = not g.get("paused", False)
        update_guild(interaction.guild_id, {"paused": new_paused})
        embed = discord.Embed(
            title="⏸️ Tournament Paused" if new_paused else "▶️ Tournament Resumed",
            color=0xF1C40F if new_paused else 0x2ECC71,
        )
        embed.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Manage Groups", style=discord.ButtonStyle.primary, emoji="📊", custom_id="t:groups", row=2)
    async def groups_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You need **Manage Server** permission.", ephemeral=True)
            return
        await interaction.response.send_modal(ManageGroupsModal())

    @discord.ui.button(label="Slot Manager", style=discord.ButtonStyle.danger, emoji="🎟️", custom_id="t:slots", row=2)
    async def slots_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("You need **Manage Channels** permission.", ephemeral=True)
            return
        cog = interaction.client.get_cog("SlotManager")
        if cog is None:
            await interaction.response.send_message("Slot manager cog not loaded.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        ch = await cog.setup_panel(interaction.guild)
        await interaction.followup.send(f"Slot manager ready in {ch.mention}.", ephemeral=True)


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
