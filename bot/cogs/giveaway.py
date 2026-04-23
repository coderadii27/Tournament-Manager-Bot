"""Giveaway system: ?gstart <time> <prize> <winners>winner."""

from __future__ import annotations

import asyncio
import random
import re
import time
from typing import Optional

import discord
from discord.ext import commands, tasks

from state import get_all_giveaways, remove_giveaway, set_giveaway

GIVEAWAY_EMOJI = "🎉"
BRAND_COLOR = 0x9B5CF6


def parse_time(text: str) -> Optional[int]:
    m = re.fullmatch(r"\s*(\d+)\s*(s|sec|secs|seconds|m|min|mins|minutes|h|hr|hrs|hours|d|day|days)?\s*", text, re.I)
    if not m:
        return None
    n = int(m.group(1))
    unit = (m.group(2) or "s").lower()
    if unit.startswith("s"):
        return n
    if unit.startswith("m"):
        return n * 60
    if unit.startswith("h"):
        return n * 3600
    if unit.startswith("d"):
        return n * 86400
    return None


def parse_winners(text: str) -> Optional[int]:
    m = re.fullmatch(r"\s*(\d+)\s*(?:w|winner|winners)?\s*", text, re.I)
    if not m:
        return None
    return int(m.group(1))


class GiveawayJoinView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Join Giveaway", style=discord.ButtonStyle.success, emoji=GIVEAWAY_EMOJI, custom_id="ga:join")
    async def join(self, interaction: discord.Interaction, _button: discord.ui.Button):
        ga = get_all_giveaways().get(str(interaction.message.id))
        if not ga or ga.get("ended"):
            await interaction.response.send_message("This giveaway has ended.", ephemeral=True)
            return
        entrants = set(ga.get("entrants", []))
        if interaction.user.id in entrants:
            entrants.discard(interaction.user.id)
            ga["entrants"] = list(entrants)
            set_giveaway(interaction.message.id, ga)
            await interaction.response.send_message("You left the giveaway.", ephemeral=True)
            return
        entrants.add(interaction.user.id)
        ga["entrants"] = list(entrants)
        set_giveaway(interaction.message.id, ga)
        await interaction.response.send_message(f"You joined! Total entries: **{len(entrants)}**", ephemeral=True)


def giveaway_embed(prize: str, winners: int, end_ts: int, host_id: int, entrants: int, ended: bool = False, winner_ids: list[int] = None) -> discord.Embed:
    if ended:
        desc = f"**Prize:** {prize}\n**Ended** <t:{end_ts}:R>\n"
        if winner_ids:
            desc += "**Winners:** " + ", ".join(f"<@{w}>" for w in winner_ids)
        else:
            desc += "**No valid entries.**"
        embed = discord.Embed(title=f"{GIVEAWAY_EMOJI} Giveaway Ended", description=desc, color=0x95A5A6)
    else:
        embed = discord.Embed(
            title=f"{GIVEAWAY_EMOJI} GIVEAWAY {GIVEAWAY_EMOJI}",
            description=(
                f"**Prize:** {prize}\n"
                f"**Winners:** {winners}\n"
                f"**Ends:** <t:{end_ts}:R> (<t:{end_ts}:f>)\n"
                f"**Entries:** {entrants}\n\n"
                f"Click the button below to enter!"
            ),
            color=BRAND_COLOR,
        )
    embed.set_footer(text=f"Hosted by user {host_id} • BRN ESPORTS OFFICIAL BOT")
    return embed


class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(GiveawayJoinView())
        self.checker.start()

    def cog_unload(self):
        self.checker.cancel()

    @commands.command(name="gstart")
    @commands.has_permissions(manage_guild=True)
    async def gstart(self, ctx: commands.Context, duration: str, prize: str, winners: str = "1"):
        secs = parse_time(duration)
        if secs is None or secs <= 0:
            await ctx.reply("Invalid time. Use `10s`, `5m`, `2h`, `1d`.", mention_author=False)
            return
        w = parse_winners(winners)
        if w is None or w <= 0:
            await ctx.reply("Invalid winner count.", mention_author=False)
            return
        end_ts = int(time.time()) + secs
        embed = giveaway_embed(prize, w, end_ts, ctx.author.id, 0)
        msg = await ctx.send(embed=embed, view=GiveawayJoinView())
        set_giveaway(
            msg.id,
            {
                "channel_id": ctx.channel.id,
                "guild_id": ctx.guild.id,
                "host_id": ctx.author.id,
                "prize": prize,
                "winners": w,
                "end_ts": end_ts,
                "entrants": [],
                "ended": False,
            },
        )
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

    @tasks.loop(seconds=5)
    async def checker(self):
        now = int(time.time())
        for mid_str, ga in list(get_all_giveaways().items()):
            if ga.get("ended"):
                continue
            if ga.get("end_ts", 0) > now:
                continue
            await self._end_giveaway(int(mid_str), ga)

    @checker.before_loop
    async def before_checker(self):
        await self.bot.wait_until_ready()

    async def _end_giveaway(self, message_id: int, ga: dict):
        try:
            channel = self.bot.get_channel(ga["channel_id"]) or await self.bot.fetch_channel(ga["channel_id"])
            msg = await channel.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            remove_giveaway(message_id)
            return

        entrants = list(ga.get("entrants", []))
        winners_count = int(ga.get("winners", 1))
        winner_ids: list[int] = []
        if entrants:
            random.shuffle(entrants)
            winner_ids = entrants[:winners_count]

        ga["ended"] = True
        ga["winner_ids"] = winner_ids
        set_giveaway(message_id, ga)

        embed = giveaway_embed(
            ga["prize"], winners_count, ga["end_ts"], ga["host_id"],
            len(ga.get("entrants", [])), ended=True, winner_ids=winner_ids,
        )
        try:
            await msg.edit(embed=embed, view=None)
        except discord.HTTPException:
            pass

        if winner_ids:
            mention_str = ", ".join(f"<@{w}>" for w in winner_ids)
            try:
                await channel.send(f"🎉 Congratulations {mention_str}! You won **{ga['prize']}**!")
            except discord.HTTPException:
                pass
        else:
            try:
                await channel.send(f"😔 No valid entries for **{ga['prize']}**.")
            except discord.HTTPException:
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaway(bot))
