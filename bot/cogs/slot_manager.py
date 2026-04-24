"""Slot Manager: private admin channel + public slot-cancel-claim channel.

Two channels are managed by this cog under the BRN ESPORTS category:

1. `slot-manager` (private, admin-only) — for staff oversight.
2. `slot-cancel-claim` (public view, send-disabled, button-driven) —
   here anyone can use the panel buttons to cancel / transfer / view
   their own slot.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from state import get_guild, save_guild

BRAND_COLOR = 0x9B5CF6
PUBLIC_CHANNEL_NAME = "slot-cancel-claim"
ADMIN_CHANNEL_NAME = "slot-manager"


def find_team_indexes_for_user(g: dict, user_id: int) -> list[int]:
    out: list[int] = []
    for i, t in enumerate(g.get("teams", [])):
        if t.get("captain_id") == user_id:
            out.append(i)
            continue
        if user_id in (t.get("player_ids") or []):
            out.append(i)
    return out


# ──────────────────────────────────────────────────────────────────────────────
# Modals
# ──────────────────────────────────────────────────────────────────────────────

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


class TransferSlotModal(discord.ui.Modal, title="Transfer Your Slot"):
    new_owner_id = discord.ui.TextInput(
        label="New owner (User ID or @mention)",
        placeholder="e.g. 123456789012345678 or copy ID from Developer Mode",
        max_length=64,
    )

    async def on_submit(self, interaction: discord.Interaction):
        g = get_guild(interaction.guild_id)
        idxs = find_team_indexes_for_user(g, interaction.user.id)
        if not idxs:
            await interaction.response.send_message("You don't have any registered slot.", ephemeral=True)
            return
        raw = str(self.new_owner_id).strip().replace("<@", "").replace("!", "").replace(">", "")
        try:
            new_id = int(raw)
        except ValueError:
            await interaction.response.send_message(
                "Invalid user ID. Right-click the user → Copy ID (Developer Mode required).",
                ephemeral=True,
            )
            return
        new_member = interaction.guild.get_member(new_id)
        if new_member is None or new_member.bot:
            await interaction.response.send_message(
                "That user is not in this server.", ephemeral=True,
            )
            return

        slot = g["teams"][idxs[0]]
        old_owner = slot.get("captain_id")
        slot["captain_id"] = new_member.id
        # Move the new owner to position 0 in player_ids if present
        pids = list(slot.get("player_ids") or [])
        if new_member.id in pids:
            pids.remove(new_member.id)
        pids.insert(0, new_member.id)
        slot["player_ids"] = pids
        save_guild(interaction.guild_id, g)

        # Move IDP role from old owner to new
        idp_role = None
        idp_role_id = g.get("idp_role_id")
        if idp_role_id:
            idp_role = interaction.guild.get_role(int(idp_role_id))
        if idp_role:
            old = interaction.guild.get_member(int(old_owner)) if old_owner else None
            try:
                if old and idp_role in old.roles:
                    await old.remove_roles(idp_role, reason="Slot transferred")
            except (discord.Forbidden, discord.HTTPException):
                pass
            try:
                await new_member.add_roles(idp_role, reason="Slot transferred — new IGL")
            except (discord.Forbidden, discord.HTTPException):
                pass

        embed = discord.Embed(
            title="🔄 Slot Transferred",
            description=(
                f"Slot **{slot.get('name')}** has been transferred.\n"
                f"From: <@{old_owner}>\nTo: {new_member.mention}"
            ),
            color=BRAND_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ──────────────────────────────────────────────────────────────────────────────
# Public View (used in slot-cancel-claim channel)
# ──────────────────────────────────────────────────────────────────────────────

class PublicSlotView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="My Slot", style=discord.ButtonStyle.primary, emoji="🎟️", custom_id="pub_slot:my")
    async def my_slot(self, interaction: discord.Interaction, _b):
        g = get_guild(interaction.guild_id)
        idxs = find_team_indexes_for_user(g, interaction.user.id)
        if not idxs:
            await interaction.response.send_message("You have no registered slot.", ephemeral=True)
            return
        e = discord.Embed(title="🎟️ Your Slot", color=BRAND_COLOR)
        for i in idxs:
            t = g["teams"][i]
            roster = ", ".join(t.get("player_names") or [])
            e.add_field(
                name=f"Slot #{i + 1} — {t.get('name')}",
                value=f"IGL: <@{t.get('captain_id')}>\nPlayers: {roster or '—'}",
                inline=False,
            )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="Change Team Name", style=discord.ButtonStyle.secondary, emoji="✏️", custom_id="pub_slot:rename")
    async def rename(self, interaction: discord.Interaction, _b):
        await interaction.response.send_modal(ChangeTeamNameModal())

    @discord.ui.button(label="Transfer Slot", style=discord.ButtonStyle.secondary, emoji="🔄", custom_id="pub_slot:transfer")
    async def transfer(self, interaction: discord.Interaction, _b):
        await interaction.response.send_modal(TransferSlotModal())

    @discord.ui.button(label="Cancel My Slot", style=discord.ButtonStyle.danger, emoji="❌", custom_id="pub_slot:cancel")
    async def cancel_slot(self, interaction: discord.Interaction, _b):
        g = get_guild(interaction.guild_id)
        idxs = find_team_indexes_for_user(g, interaction.user.id)
        if not idxs:
            await interaction.response.send_message("You don't have a slot to cancel.", ephemeral=True)
            return
        team = g["teams"].pop(idxs[0])
        save_guild(interaction.guild_id, g)

        # Remove IDP role from former IGL
        idp_role_id = g.get("idp_role_id")
        if idp_role_id:
            role = interaction.guild.get_role(int(idp_role_id))
            cap = interaction.guild.get_member(int(team.get("captain_id", 0)))
            if role and cap and role in cap.roles:
                try:
                    await cap.remove_roles(role, reason="Slot cancelled")
                except (discord.Forbidden, discord.HTTPException):
                    pass

        embed = discord.Embed(
            title="🗑️ Slot Cancelled",
            description=f"Your team **{team.get('name')}** has been removed.\n*This action is irreversible.*",
            color=0xE74C3C,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# Legacy private admin view (kept for the private slot-manager channel)
class SlotManagerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Cancel My Slot", style=discord.ButtonStyle.danger, emoji="❌", custom_id="slot:cancel")
    async def cancel_slot(self, interaction: discord.Interaction, _b):
        await PublicSlotView.cancel_slot.callback(self, interaction, _b)  # type: ignore[arg-type]

    @discord.ui.button(label="My Slots", style=discord.ButtonStyle.primary, emoji="🎟️", custom_id="slot:my")
    async def my_slots(self, interaction: discord.Interaction, _b):
        await PublicSlotView.my_slot.callback(self, interaction, _b)  # type: ignore[arg-type]

    @discord.ui.button(label="Change Team Name", style=discord.ButtonStyle.secondary, emoji="✏️", custom_id="slot:rename")
    async def rename(self, interaction: discord.Interaction, _b):
        await interaction.response.send_modal(ChangeTeamNameModal())


# ──────────────────────────────────────────────────────────────────────────────
# Cog
# ──────────────────────────────────────────────────────────────────────────────

class SlotManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(SlotManagerView())
        self.bot.add_view(PublicSlotView())

    # ---------- private admin channel ----------
    async def setup_panel(self, guild: discord.Guild, invoker: discord.Member | None = None) -> discord.TextChannel:
        g = get_guild(guild.id)
        ch = discord.utils.get(guild.text_channels, name=ADMIN_CHANNEL_NAME)
        category = discord.utils.get(guild.categories, name="🏆 BRN ESPORTS")

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
                ADMIN_CHANNEL_NAME, category=category, overwrites=overwrites,
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
                "Admin slot manager.\n"
                "• **Cancel My Slot** — cancel a slot\n"
                "• **My Slots** — view your slot info\n"
                "• **Change Team Name** — rename your team"
            ),
            color=BRAND_COLOR,
        )
        embed.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        await self._upsert_panel(ch, embed, SlotManagerView())
        g["slot_manager_channel_id"] = ch.id
        save_guild(guild.id, g)
        return ch

    # ---------- public slot-cancel-claim channel ----------
    async def setup_public_claim_channel(self, guild: discord.Guild) -> discord.TextChannel:
        g = get_guild(guild.id)
        ch = discord.utils.get(guild.text_channels, name=PUBLIC_CHANNEL_NAME)
        category = discord.utils.get(guild.categories, name="🏆 BRN ESPORTS")

        # Everyone can VIEW but NOT send. Buttons still work via interaction.
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=True, send_messages=False, read_message_history=True, add_reactions=False,
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, manage_messages=True, manage_channels=True,
            ),
        }
        if ch is None:
            ch = await guild.create_text_channel(
                PUBLIC_CHANNEL_NAME, category=category, overwrites=overwrites,
                reason="Public slot cancel/claim/transfer channel",
            )
        else:
            for target, ow in overwrites.items():
                try:
                    await ch.set_permissions(target, overwrite=ow)
                except discord.Forbidden:
                    pass

        embed = discord.Embed(
            title=f"🎟️ Slot Center — {g.get('tournament_name', 'Tournament')}",
            description=(
                "Use the buttons below to manage **your own slot**.\n\n"
                "🎟️  **My Slot** — view your team and players\n"
                "✏️  **Change Team Name** — rename your team\n"
                "🔄  **Transfer Slot** — hand your slot to another player\n"
                "❌  **Cancel My Slot** — give up your slot (irreversible)\n\n"
                "*This channel is view-only — please use the buttons.*"
            ),
            color=BRAND_COLOR,
        )
        embed.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        await self._upsert_panel(ch, embed, PublicSlotView())
        g["public_slot_channel_id"] = ch.id
        save_guild(guild.id, g)
        return ch

    async def _upsert_panel(
        self,
        ch: discord.TextChannel,
        embed: discord.Embed,
        view: discord.ui.View,
    ) -> None:
        async for msg in ch.history(limit=20):
            if msg.author == ch.guild.me and msg.embeds and "Slot" in (msg.embeds[0].title or ""):
                try:
                    await msg.edit(embed=embed, view=view)
                    return
                except Exception:
                    pass
        await ch.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(SlotManager(bot))
