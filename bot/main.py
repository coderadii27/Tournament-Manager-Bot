"""BRN ESPORTS Discord Tournament Manager Bot."""

import asyncio
import logging
import os

import discord
from discord.ext import commands

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("brn-bot")

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN environment variable is not set.")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
intents.guilds = True

bot = commands.Bot(
    command_prefix="?",
    intents=intents,
    description="BRN ESPORTS OFFICIAL BOT",
    help_command=commands.DefaultHelpCommand(no_category="Commands"),
)

INITIAL_COGS = [
    "cogs.tournament",
    "cogs.registration",
    "cogs.slot_manager",
    "cogs.moderation",
    "cogs.purge",
    "cogs.giveaway",
    "cogs.management",
]


@bot.event
async def on_ready():
    log.info("Logged in as %s (id=%s)", bot.user, bot.user.id if bot.user else "?")
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="Organising Tournaments in BRN ESPORTS",
        ),
    )
    total = 0
    for guild in bot.guilds:
        try:
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            total += len(synced)
            log.info("Synced %d commands to guild %s", len(synced), guild.name)
        except Exception as e:
            log.exception("Sync failed for %s: %s", guild.name, e)
    log.info("Total per-guild commands synced: %d", total)


@bot.event
async def on_guild_join(guild: discord.Guild):
    try:
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        log.info("Synced %d commands to new guild %s", len(synced), guild.name)
    except Exception as e:
        log.exception("Sync on join failed: %s", e)


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("You don't have permission to use that command.", mention_author=False)
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply(f"Missing argument: `{error.param.name}`.", mention_author=False)
        return
    log.exception("Command error: %s", error)
    try:
        await ctx.reply(f"An error occurred: `{error}`", mention_author=False)
    except Exception:
        pass


async def main():
    async with bot:
        for ext in INITIAL_COGS:
            try:
                await bot.load_extension(ext)
                log.info("Loaded extension %s", ext)
            except Exception as e:
                log.exception("Failed to load %s: %s", ext, e)
        await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Shutting down.")
