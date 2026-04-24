"""Registration channel monitor.

Accepts BOTH formats:

1. Detailed format with PLAYER 1 (IGL), CHARACTER ID, DISCORD TAG, etc.
2. Simple format:
       Team name - punishers
       @user1
       @user2
       @user3
       @user4
       @user5

The first mentioned user is treated as the IGL/captain and gets the
configured IDP role automatically.
"""

from __future__ import annotations

import re

import discord
from discord.ext import commands

from state import get_guild, save_guild


def _extract_team_name(content: str) -> str | None:
    m = re.search(r"team\s*name\s*[-:]\s*(.+)", content, flags=re.IGNORECASE)
    if not m:
        # also accept "team -" or "team:"
        m = re.search(r"\bteam\s*[-:]\s*(.+)", content, flags=re.IGNORECASE)
    if not m:
        return None
    name = m.group(1).strip().splitlines()[0]
    # strip any leading mention from the name line just in case
    name = re.sub(r"<@!?\d+>", "", name).strip()
    return name or None


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

        # Slots full
        if len(teams) >= max_slots:
            try:
                await message.add_reaction("❌")
                await message.reply(
                    "❌ Sorry, all slots are full.", mention_author=False, delete_after=10,
                )
            except discord.HTTPException:
                pass
            return

        # Parse team name
        team_name = _extract_team_name(message.content)
        if not team_name:
            try:
                await message.add_reaction("❌")
            except discord.HTTPException:
                pass
            return

        # Mentions = members listed in the form (must equal team_size)
        mentions = [m for m in message.mentions if not m.bot]
        if len(mentions) != team_size:
            try:
                await message.add_reaction("⚠️")
                await message.reply(
                    f"⚠️ This tournament needs **exactly {team_size}** players "
                    f"(@mentions). You provided **{len(mentions)}**.",
                    mention_author=False, delete_after=15,
                )
            except discord.HTTPException:
                pass
            return

        # Duplicate name check
        if any(t.get("name", "").lower() == team_name.lower() for t in teams):
            try:
                await message.add_reaction("⚠️")
                await message.reply(
                    f"⚠️ Team name **{team_name}** is already registered.",
                    mention_author=False, delete_after=15,
                )
            except discord.HTTPException:
                pass
            return

        igl = mentions[0]
        teams.append(
            {
                "name": team_name,
                "captain_id": igl.id,
                "poster_id": message.author.id,
                "player_ids": [m.id for m in mentions],
                "player_names": [m.display_name for m in mentions],
                "message_id": message.id,
            }
        )
        g["teams"] = teams
        save_guild(message.guild.id, g)

        try:
            await message.add_reaction("✅")
        except discord.HTTPException:
            pass

        # Auto-assign IDP access role to the IGL (first mentioned user)
        idp_role = None
        idp_role_id = g.get("idp_role_id")
        if idp_role_id:
            idp_role = message.guild.get_role(int(idp_role_id))
        if idp_role is None:
            idp_role = discord.utils.find(
                lambda r: r.name.lower() in ("idp access", "idp-access", "idp"),
                message.guild.roles,
            )
        if idp_role is not None:
            try:
                await igl.add_roles(idp_role, reason="IGL — registration confirmed")
            except (discord.Forbidden, discord.HTTPException):
                pass

        # Confirmation embed
        confirm_id = g.get("confirm_channel_id")
        if confirm_id:
            ch = message.guild.get_channel(confirm_id)
            if ch is not None:
                roster = "\n".join(
                    f"`{i + 1}.` {m.mention}" + ("  🎟️ **IGL**" if i == 0 else "")
                    for i, m in enumerate(mentions)
                )
                desc = (
                    f"**{team_name}** is officially registered!\n"
                    f"IGL: {igl.mention}\n"
                    f"Slot: `{len(teams)}/{max_slots}`\n\n"
                    f"**Roster:**\n{roster}"
                )
                if idp_role is not None:
                    desc += f"\n\n🎟️ IGL given role: {idp_role.mention}"
                embed = discord.Embed(title="✅ Team Confirmed", description=desc, color=0x2ECC71)
                embed.set_footer(text="BRN ESPORTS OFFICIAL BOT")
                await ch.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Registration(bot))
