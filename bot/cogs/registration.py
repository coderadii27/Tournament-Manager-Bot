"""Registration channel monitor."""

from __future__ import annotations

import re

import discord
from discord.ext import commands

from state import get_guild, save_guild

REQUIRED_LINES_BASE = ["TEAM NAME"]
PLAYER_FIELDS = ["CHARACTER ID", "DISCORD TAG"]


def parse_team(content: str, team_size: int) -> tuple[bool, str | None]:
    text = content.upper()
    if "TEAM NAME" not in text:
        return False, None
    name_match = re.search(r"TEAM\s*NAME\s*[-:]\s*(.+)", content, flags=re.IGNORECASE)
    team_name = name_match.group(1).strip().splitlines()[0] if name_match else None
    if not team_name:
        return False, None
    for i in range(1, team_size + 1):
        if not re.search(rf"PLAYER\s*{i}\b", text):
            return False, None
        for field in PLAYER_FIELDS:
            if text.count(field) < team_size:
                return False, None
    return True, team_name


class Registration(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return
        g = get_guild(message.guild.id)
        reg_id = g.get("registration_channel_id")
        if reg_id is None or message.channel.id != reg_id:
            return

        team_size = int(g.get("team_size", 5))
        max_slots = int(g.get("max_slots", 16))
        teams = list(g.get("teams", []))

        if len(teams) >= max_slots:
            try:
                await message.add_reaction("❌")
            except discord.HTTPException:
                pass
            return

        ok, team_name = parse_team(message.content, team_size)
        if not ok or not team_name:
            try:
                await message.add_reaction("❌")
            except discord.HTTPException:
                pass
            return

        if any(t.get("name", "").lower() == team_name.lower() for t in teams):
            try:
                await message.add_reaction("⚠️")
            except discord.HTTPException:
                pass
            return

        teams.append(
            {
                "name": team_name,
                "captain_id": message.author.id,
                "message_id": message.id,
            }
        )
        g["teams"] = teams
        save_guild(message.guild.id, g)

        try:
            await message.add_reaction("✅")
        except discord.HTTPException:
            pass

        confirm_id = g.get("confirm_channel_id")
        if confirm_id:
            ch = message.guild.get_channel(confirm_id)
            if ch is not None:
                embed = discord.Embed(
                    title="✅ Team Confirmed",
                    description=(
                        f"**{team_name}** is officially registered!\n"
                        f"Captain: {message.author.mention}\n"
                        f"Slot: `{len(teams)}/{max_slots}`"
                    ),
                    color=0x2ECC71,
                )
                embed.set_footer(text="BRN ESPORTS OFFICIAL BOT")
                await ch.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Registration(bot))
