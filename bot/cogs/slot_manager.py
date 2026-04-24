"""Slot Manager channel and panel."""

from __future__ import annotations

import discord
from discord.ext import commands

from state import get_guild, save_guild

BRAND_COLOR = 0x9B5CF6


def find_team_indexes_for_user(g: dict, user_id: int) -> list[int]:
    return [i for i, t in enumerate(g.get("teams", [])) if t.get("captain_id") == user_id]


class ChangeTeamNameModal(discord.ui.Modal, title="Change Team Name"):
    new_name = discord.ui.TextInput(label="New Team Name", max_length=64)

    async def on_submit(self, interaction: discord.Interaction):
        g = get_guild(interaction.guild_id)
        idxs = find_team_indexes_for_user(g, interaction.user.id)
        if not idxs:
            await interaction.response.send_message("You don't have any registered slot.", ephemeral=True)
            return
        new = str(self.new_name).strip()
        if not new:
            await interaction.response.send_message("Name cannot be empty.", ephemeral=True)
            return
        if any(t.get("name", "").lower() == new.lower() for t in g["teams"]):
            await interaction.response.send_message("That team name is already taken.", ephemeral=True)
            return
        old = g["teams"][idxs[0]]["name"]
        g["teams"][idxs[0]]["name"] = new
        save_guild(interaction.guild_id, g)
        embed = discord.Embed(
            title="✏️ Team Name Updated",
            description=f"**{old}** → **{new}**",
            color=BRAND_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class SlotManagerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Cancel My Slot", style=discord.ButtonStyle.danger, emoji="❌", custom_id="slot:cancel")
    async def cancel_slot(self, interaction: discord.Interaction, _button: discord.ui.Button):
        g = get_guild(interaction.guild_id)
        idxs = find_team_indexes_for_user(g, interaction.user.id)
        if not idxs:
            await interaction.response.send_message("You don't have a slot to cancel.", ephemeral=True)
            return
        team = g["teams"].pop(idxs[0])
        save_guild(interaction.guild_id, g)
        embed = discord.Embed(
            title="🗑️ Slot Cancelled",
            description=f"Your team **{team.get('name')}** has been removed.\n*This action is irreversible.*",
            color=0xE74C3C,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="My Slots", style=discord.ButtonStyle.primary, emoji="🎟️", custom_id="slot:my")
    async def my_slots(self, interaction: discord.Interaction, _button: discord.ui.Button):
        g = get_guild(interaction.guild_id)
        idxs = find_team_indexes_for_user(g, interaction.user.id)
        if not idxs:
            await interaction.response.send_message("You have no registered slots.", ephemeral=True)
            return
        embed = discord.Embed(title="🎟️ Your Slots", color=BRAND_COLOR)
        for i in idxs:
            t = g["teams"][i]
            embed.add_field(name=f"Slot #{i + 1}", value=f"Team: **{t.get('name')}**", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Change Team Name", style=discord.ButtonStyle.secondary, emoji="✏️", custom_id="slot:rename")
    async def rename(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.send_modal(ChangeTeamNameModal())


class SlotManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(SlotManagerView())

    async def setup_panel(self, guild: discord.Guild, invoker: discord.Member | None = None) -> discord.TextChannel:
        g = get_guild(guild.id)
        ch = discord.utils.get(guild.text_channels, name="slot-manager")
        category = discord.utils.get(guild.categories, name="🏆 BRN ESPORTS")
        # Private: hide from @everyone, grant view to bot + invoker + every role
        # that already has Manage Channels / Manage Guild server-wide (staff).
        overwrites: dict = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, manage_messages=True, manage_channels=True
            ),
        }
        for role in guild.roles:
            if role.is_default():
                continue
            p = role.permissions
            if p.administrator or p.manage_guild or p.manage_channels:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                )
        if invoker is not None:
            overwrites[invoker] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            )
        if ch is None:
            ch = await guild.create_text_channel(
                "slot-manager", category=category, overwrites=overwrites,
                reason="Private slot manager channel",
            )
        else:
            for target, ow in overwrites.items():
                try:
                    await ch.set_permissions(target, overwrite=ow)
                except discord.Forbidden:
                    pass
        embed = discord.Embed(
            title=f"🎟️ Tournament Slot Manager — {g.get('tournament_name', 'EliteQ-tourny')}",
            description=(
                "• Click **Cancel My Slot** below to cancel your slot.\n"
                "• Click **My Slots** to get info about all your slots.\n"
                "• Click **Change Team Name** if you want to update your team's name.\n\n"
                "*Note: slot cancellation is irreversible.*"
            ),
            color=BRAND_COLOR,
        )
        embed.set_footer(text="BRN ESPORTS OFFICIAL BOT")

        sent = False
        async for msg in ch.history(limit=20):
            if msg.author == guild.me and msg.embeds and "Slot Manager" in (msg.embeds[0].title or ""):
                await msg.edit(embed=embed, view=SlotManagerView())
                sent = True
                break
        if not sent:
            await ch.send(embed=embed, view=SlotManagerView())

        g["slot_manager_channel_id"] = ch.id
        save_guild(guild.id, g)
        return ch


async def setup(bot: commands.Bot):
    await bot.add_cog(SlotManager(bot))
