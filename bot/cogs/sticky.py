"""Sticky message cog: bot keeps a configured message at the bottom of a channel.

Commands:
- ?stick <message>     → set the sticky message for the current channel
- ?stick               → (replying to a message) make that replied message sticky
- ?unstick             → remove the sticky message from the current channel
- ?stickyinfo          → show current sticky for this channel

Behaviour:
- After every 50 messages by other users in a sticky channel, the bot
  deletes its previous sticky message and re-sends it at the bottom so it
  stays visible.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from state import get_guild, save_guild

BRAND = 0x9B5CF6
REPOST_EVERY = 50


def _sticky_embed(text: str, channel_name: str) -> discord.Embed:
    e = discord.Embed(
        title="📌 Sticky Note",
        description=text,
        color=BRAND,
    )
    e.set_footer(text=f"This channel is for #{channel_name} • BRN ESPORTS OFFICIAL BOT")
    return e


class Sticky(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Commands ------------------------------------------------------------

    @commands.command(name="stick")
    @commands.has_permissions(manage_channels=True)
    async def stick(self, ctx: commands.Context, *, message: str | None = None):
        if ctx.guild is None:
            return
        text = message
        if text is None and ctx.message.reference and ctx.message.reference.message_id:
            try:
                ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                text = ref.content
            except Exception:
                text = None
        if not text:
            await ctx.reply(
                "Usage: `?stick <your message>` — or reply to a message with `?stick`.",
                mention_author=False,
            )
            return

        g = get_guild(ctx.guild.id)
        sticky = g.setdefault("sticky", {})
        counters = g.setdefault("sticky_counters", {})

        # Delete old sticky if present
        prev = sticky.get(str(ctx.channel.id))
        if prev and prev.get("message_id"):
            try:
                old = await ctx.channel.fetch_message(int(prev["message_id"]))
                await old.delete()
            except Exception:
                pass

        embed = _sticky_embed(text, ctx.channel.name)
        sent = await ctx.channel.send(embed=embed)

        sticky[str(ctx.channel.id)] = {"text": text, "message_id": sent.id}
        counters[str(ctx.channel.id)] = 0
        save_guild(ctx.guild.id, g)

        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="unstick")
    @commands.has_permissions(manage_channels=True)
    async def unstick(self, ctx: commands.Context):
        if ctx.guild is None:
            return
        g = get_guild(ctx.guild.id)
        sticky = g.setdefault("sticky", {})
        counters = g.setdefault("sticky_counters", {})

        prev = sticky.pop(str(ctx.channel.id), None)
        counters.pop(str(ctx.channel.id), None)
        save_guild(ctx.guild.id, g)

        if prev and prev.get("message_id"):
            try:
                old = await ctx.channel.fetch_message(int(prev["message_id"]))
                await old.delete()
            except Exception:
                pass
        await ctx.reply("✅ Sticky removed from this channel.", mention_author=False)

    @commands.command(name="stickyinfo")
    async def stickyinfo(self, ctx: commands.Context):
        if ctx.guild is None:
            return
        g = get_guild(ctx.guild.id)
        sticky = g.get("sticky", {})
        s = sticky.get(str(ctx.channel.id))
        if not s:
            await ctx.reply("No sticky message in this channel.", mention_author=False)
            return
        e = discord.Embed(title="📌 Current Sticky", description=s.get("text", ""), color=BRAND)
        e.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        await ctx.reply(embed=e, mention_author=False)

    # --- Listener ------------------------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return
        # Ignore command invocations from this cog
        if message.content.startswith("?stick") or message.content.startswith("?unstick"):
            return

        g = get_guild(message.guild.id)
        sticky = g.get("sticky", {})
        s = sticky.get(str(message.channel.id))
        if not s:
            return

        counters = g.setdefault("sticky_counters", {})
        n = int(counters.get(str(message.channel.id), 0)) + 1

        if n >= REPOST_EVERY:
            counters[str(message.channel.id)] = 0
            # Delete previous sticky message
            prev_id = s.get("message_id")
            if prev_id:
                try:
                    old = await message.channel.fetch_message(int(prev_id))
                    await old.delete()
                except Exception:
                    pass
            # Repost
            try:
                embed = _sticky_embed(s.get("text", ""), message.channel.name)
                sent = await message.channel.send(embed=embed)
                s["message_id"] = sent.id
                sticky[str(message.channel.id)] = s
            except Exception:
                pass
        else:
            counters[str(message.channel.id)] = n

        save_guild(message.guild.id, g)


async def setup(bot: commands.Bot):
    await bot.add_cog(Sticky(bot))
