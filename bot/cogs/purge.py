"""?purge command."""

from __future__ import annotations

import discord
from discord.ext import commands


class Purge(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="purge")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, target: str = None):
        if ctx.guild is None or target is None:
            await ctx.reply("Usage: `?purge <1-100>` or `?purge @user`", mention_author=False)
            return

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        if ctx.message.mentions:
            user = ctx.message.mentions[0]
            deleted = await ctx.channel.purge(
                limit=200,
                check=lambda m: m.author.id == user.id,
            )
            embed = discord.Embed(
                title="🧹 Purged",
                description=f"Deleted **{len(deleted)}** messages from {user.mention}.",
                color=0x9B5CF6,
            )
            msg = await ctx.send(embed=embed)
            await msg.delete(delay=5)
            return

        try:
            n = int(target)
        except ValueError:
            await ctx.send("Provide a number 1-100 or mention a user.", delete_after=5)
            return
        if not 1 <= n <= 100:
            await ctx.send("Number must be between 1 and 100.", delete_after=5)
            return

        deleted = await ctx.channel.purge(limit=n)
        embed = discord.Embed(
            title="🧹 Purged",
            description=f"Deleted **{len(deleted)}** messages.",
            color=0x9B5CF6,
        )
        msg = await ctx.send(embed=embed)
        await msg.delete(delay=5)


async def setup(bot: commands.Bot):
    await bot.add_cog(Purge(bot))
