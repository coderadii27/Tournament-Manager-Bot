"""Moderation slash commands: /ban /kick /mute /unmute."""

from __future__ import annotations

import re
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands


def parse_duration(text: str) -> timedelta | None:
    m = re.fullmatch(r"\s*(\d+)\s*(m|min|mins|minutes|h|hr|hrs|hours|d|day|days|s|sec|secs|seconds)?\s*", text, re.I)
    if not m:
        return None
    n = int(m.group(1))
    unit = (m.group(2) or "m").lower()
    if unit.startswith("s"):
        return timedelta(seconds=n)
    if unit.startswith("h"):
        return timedelta(hours=n)
    if unit.startswith("d"):
        return timedelta(days=n)
    return timedelta(minutes=n)


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Ban a user from the server.")
    @app_commands.describe(user="User to ban", reason="Reason")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("Missing **Ban Members** permission.", ephemeral=True)
            return
        try:
            await user.ban(reason=reason, delete_message_days=0)
        except discord.Forbidden:
            await interaction.response.send_message("I can't ban that user.", ephemeral=True)
            return
        embed = discord.Embed(title="🔨 User Banned", color=0xE74C3C)
        embed.add_field(name="User", value=f"{user} (`{user.id}`)", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"By {interaction.user}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="kick", description="Kick a user from the server.")
    @app_commands.describe(user="User to kick", reason="Reason")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("Missing **Kick Members** permission.", ephemeral=True)
            return
        try:
            await user.kick(reason=reason)
        except discord.Forbidden:
            await interaction.response.send_message("I can't kick that user.", ephemeral=True)
            return
        embed = discord.Embed(title="👢 User Kicked", color=0xE67E22)
        embed.add_field(name="User", value=f"{user} (`{user.id}`)", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"By {interaction.user}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mute", description="Timeout a user. Time examples: 10m, 2h, 1d.")
    @app_commands.describe(user="User to mute", time="Duration (e.g. 10m, 2h, 1d)", reason="Reason")
    @app_commands.default_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, user: discord.Member, time: str, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("Missing **Timeout Members** permission.", ephemeral=True)
            return
        delta = parse_duration(time)
        if delta is None or delta.total_seconds() <= 0 or delta > timedelta(days=28):
            await interaction.response.send_message("Invalid time. Use forms like `10m`, `2h`, `1d` (max 28 days).", ephemeral=True)
            return
        try:
            await user.timeout(delta, reason=reason)
        except discord.Forbidden:
            await interaction.response.send_message("I can't timeout that user.", ephemeral=True)
            return
        embed = discord.Embed(title="🔇 User Muted", color=0xF1C40F)
        embed.add_field(name="User", value=f"{user} (`{user.id}`)", inline=False)
        embed.add_field(name="Duration", value=str(delta), inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"By {interaction.user}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unmute", description="Remove timeout from a user.")
    @app_commands.describe(user="User to unmute")
    @app_commands.default_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, user: discord.Member):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("Missing **Timeout Members** permission.", ephemeral=True)
            return
        try:
            await user.timeout(None, reason=f"Unmuted by {interaction.user}")
        except discord.Forbidden:
            await interaction.response.send_message("I can't unmute that user.", ephemeral=True)
            return
        embed = discord.Embed(title="🔊 User Unmuted", color=0x2ECC71)
        embed.add_field(name="User", value=f"{user} (`{user.id}`)", inline=False)
        embed.set_footer(text=f"By {interaction.user}")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
