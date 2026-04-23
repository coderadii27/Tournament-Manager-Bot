"""Ticket system: panel + button → private channel with claim/close."""

from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from state import get_guild, save_guild

BRAND = 0x9B5CF6
ACCENT = 0x00E5FF


def _ticket_state(g: dict) -> dict:
    g.setdefault(
        "ticket",
        {"staff_role_id": None, "category_id": None, "counter": 0, "panel_channel_id": None},
    )
    return g["ticket"]


def _panel_embed() -> discord.Embed:
    e = discord.Embed(
        title="🎫  Need Help? Open a Ticket",
        description=(
            "Welcome to support! Click the button below to open a **private ticket** with our staff team.\n\n"
            "**How it works**\n"
            "› A private channel is created just for you\n"
            "› Only you and staff can see it\n"
            "› Describe your issue and we'll help ASAP\n"
            "› Close the ticket when you're done\n\n"
            "*Please don't open a ticket without a real reason — abuse may result in action.*"
        ),
        color=BRAND,
        timestamp=datetime.now(timezone.utc),
    )
    e.set_author(name="BERNICS ESPORTS • Support")
    e.set_footer(text="Powered by your friendly support team")
    return e


def _ticket_welcome_embed(user: discord.Member, ticket_no: int) -> discord.Embed:
    e = discord.Embed(
        title=f"🎫 Ticket #{ticket_no:04d}",
        description=(
            f"Hello {user.mention}, thanks for opening a ticket!\n\n"
            "› Please describe your issue with as much detail as possible.\n"
            "› A staff member will be with you shortly.\n"
            "› Use **Claim** to take ownership (staff only) or **Close** when done."
        ),
        color=ACCENT,
        timestamp=datetime.now(timezone.utc),
    )
    e.set_author(name="BERNICS ESPORTS • Support")
    e.add_field(name="Status", value="🟢 Open • Unclaimed", inline=True)
    e.add_field(name="Opened by", value=user.mention, inline=True)
    e.set_footer(text="Powered by your friendly support team")
    return e


class TicketPanelView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Open Ticket",
        emoji="🎫",
        style=discord.ButtonStyle.success,
        custom_id="ticket:open",
    )
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        if not interaction.guild:
            return await interaction.followup.send("Guild only.", ephemeral=True)
        g = get_guild(interaction.guild.id)
        ts = _ticket_state(g)

        # Prevent duplicate ticket per user
        for ch in interaction.guild.text_channels:
            if ch.topic and f"ticket-user:{interaction.user.id}" in ch.topic:
                return await interaction.followup.send(
                    f"You already have an open ticket: {ch.mention}", ephemeral=True
                )

        category = None
        if ts.get("category_id"):
            category = interaction.guild.get_channel(ts["category_id"])
            if not isinstance(category, discord.CategoryChannel):
                category = None
        if category is None:
            category = await interaction.guild.create_category(
                "🎫 Tickets", reason="Auto-created tickets category"
            )
            ts["category_id"] = category.id

        staff_role = None
        if ts.get("staff_role_id"):
            staff_role = interaction.guild.get_role(ts["staff_role_id"])

        ts["counter"] = int(ts.get("counter", 0)) + 1
        ticket_no = ts["counter"]
        save_guild(interaction.guild.id, g)

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
            ),
            interaction.guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, manage_channels=True, manage_messages=True
            ),
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
            )

        try:
            channel = await interaction.guild.create_text_channel(
                name=f"ticket-{ticket_no:04d}-{interaction.user.name}"[:90],
                category=category,
                overwrites=overwrites,
                topic=f"ticket-user:{interaction.user.id} • Opened by {interaction.user}",
                reason=f"Ticket opened by {interaction.user}",
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                "I don't have permission to create channels here.", ephemeral=True
            )

        mention = staff_role.mention if staff_role else ""
        await channel.send(
            content=f"{interaction.user.mention} {mention}".strip(),
            embed=_ticket_welcome_embed(interaction.user, ticket_no),
            view=TicketControlView(),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )
        await interaction.followup.send(
            f"✅ Your ticket has been created: {channel.mention}", ephemeral=True
        )


class TicketControlView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Claim", emoji="🙋", style=discord.ButtonStyle.primary, custom_id="ticket:claim"
    )
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.channel, discord.TextChannel):
            return
        g = get_guild(interaction.guild.id)
        ts = _ticket_state(g)
        staff_role_id = ts.get("staff_role_id")
        member = interaction.user
        is_staff = (
            member.guild_permissions.manage_channels
            or (staff_role_id and any(r.id == staff_role_id for r in member.roles))
        )
        if not is_staff:
            return await interaction.response.send_message(
                "Only staff can claim tickets.", ephemeral=True
            )

        # Update first embed
        try:
            async for msg in interaction.channel.history(limit=10, oldest_first=True):
                if msg.author == interaction.guild.me and msg.embeds:
                    e = msg.embeds[0]
                    new = discord.Embed.from_dict(e.to_dict())
                    new.set_field_at(
                        0, name="Status", value=f"🟡 Open • Claimed by {member.mention}", inline=True
                    )
                    await msg.edit(embed=new)
                    break
        except Exception:
            pass
        await interaction.response.send_message(
            f"🙋 {member.mention} has claimed this ticket.", allowed_mentions=discord.AllowedMentions.none()
        )

    @discord.ui.button(
        label="Close", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="ticket:close"
    )
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.channel, discord.TextChannel):
            return
        g = get_guild(interaction.guild.id)
        ts = _ticket_state(g)
        staff_role_id = ts.get("staff_role_id")
        member = interaction.user
        topic = interaction.channel.topic or ""
        is_owner = f"ticket-user:{member.id}" in topic
        is_staff = (
            member.guild_permissions.manage_channels
            or (staff_role_id and any(r.id == staff_role_id for r in member.roles))
        )
        if not (is_owner or is_staff):
            return await interaction.response.send_message(
                "Only the ticket opener or staff can close this ticket.", ephemeral=True
            )

        e = discord.Embed(
            title="🔒 Closing Ticket",
            description=f"This ticket will be deleted in **5 seconds**.\nClosed by {member.mention}.",
            color=0xE74C3C,
        )
        await interaction.response.send_message(embed=e)
        try:
            await interaction.channel.delete(reason=f"Ticket closed by {member}")
        except Exception:
            pass


class Ticket(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ticketsetup", description="Configure ticket system & post the panel.")
    @app_commands.describe(
        staff_role="Role that can see, claim and close tickets",
        category="Category to host new tickets (auto-created if omitted)",
        channel="Channel to post the ticket panel in (defaults to current channel)",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def ticketsetup(
        self,
        interaction: discord.Interaction,
        staff_role: discord.Role | None = None,
        category: discord.CategoryChannel | None = None,
        channel: discord.TextChannel | None = None,
    ):
        if not interaction.guild:
            return await interaction.response.send_message("Guild only.", ephemeral=True)
        g = get_guild(interaction.guild.id)
        ts = _ticket_state(g)
        if staff_role:
            ts["staff_role_id"] = staff_role.id
        if category:
            ts["category_id"] = category.id
        target = channel or interaction.channel
        ts["panel_channel_id"] = target.id
        save_guild(interaction.guild.id, g)
        await target.send(embed=_panel_embed(), view=TicketPanelView())
        await interaction.response.send_message(
            f"✅ Ticket panel posted in {target.mention}."
            + (f"\nStaff role: {staff_role.mention}" if staff_role else "")
            + (f"\nCategory: **{category.name}**" if category else ""),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @app_commands.command(name="ticketpanel", description="Re-post the ticket panel here.")
    @app_commands.default_permissions(manage_guild=True)
    async def ticketpanel(self, interaction: discord.Interaction):
        await interaction.channel.send(embed=_panel_embed(), view=TicketPanelView())
        await interaction.response.send_message("✅ Panel posted.", ephemeral=True)

    @app_commands.command(name="ticketclose", description="Close the current ticket channel.")
    async def ticketclose(self, interaction: discord.Interaction):
        if not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message("Use this inside a ticket.", ephemeral=True)
        topic = interaction.channel.topic or ""
        if "ticket-user:" not in topic:
            return await interaction.response.send_message(
                "This is not a ticket channel.", ephemeral=True
            )
        await interaction.response.send_message("🔒 Closing in 5 seconds…")
        try:
            await interaction.channel.delete(reason=f"Ticket closed via /ticketclose by {interaction.user}")
        except Exception:
            pass


async def setup(bot: commands.Bot):
    bot.add_view(TicketPanelView())
    bot.add_view(TicketControlView())
    await bot.add_cog(Ticket(bot))
