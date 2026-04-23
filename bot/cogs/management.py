"""Tournament management extras: schedule, points, announce, team list, settings, lineup, dm captains, end."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from state import get_guild, save_guild

BRAND = 0x9B5CF6
ACCENT = 0x00E5FF


def _is_admin(inter: discord.Interaction) -> bool:
    return inter.user.guild_permissions.manage_guild


class Management(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------------- Slash commands ----------------

    @app_commands.command(name="info", description="Show tournament info.")
    async def info(self, inter: discord.Interaction):
        g = get_guild(inter.guild_id)
        e = discord.Embed(title=f"🏆 {g.get('tournament_name','EliteQ-tourny')}", color=BRAND)
        e.add_field(name="Slots", value=f"`{len(g.get('teams',[]))}/{g.get('max_slots',16)}`")
        e.add_field(name="Team Size", value=f"`{g.get('team_size',5)}`")
        status = "🟢 Running" if g.get("running") and not g.get("paused") else ("🟡 Paused" if g.get("paused") else "⚪ Idle")
        e.add_field(name="Status", value=status)
        e.add_field(name="Groups", value=f"`{len(g.get('groups',{}))}`")
        e.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        await inter.response.send_message(embed=e)

    @app_commands.command(name="teamlist", description="Show all confirmed teams.")
    async def teamlist(self, inter: discord.Interaction):
        g = get_guild(inter.guild_id)
        teams = g.get("teams", [])
        if not teams:
            await inter.response.send_message("No teams registered yet.", ephemeral=True)
            return
        lines = [f"`{i+1:>2}.` **{t.get('name')}** — <@{t.get('captain_id')}>" for i, t in enumerate(teams)]
        chunks = []
        cur = ""
        for ln in lines:
            if len(cur) + len(ln) + 1 > 3800:
                chunks.append(cur)
                cur = ""
            cur += ln + "\n"
        if cur:
            chunks.append(cur)
        for i, ch in enumerate(chunks):
            e = discord.Embed(
                title=f"📋 Confirmed Teams ({len(teams)}/{g.get('max_slots',16)})" + (f" — page {i+1}" if len(chunks) > 1 else ""),
                description=ch,
                color=BRAND,
            )
            e.set_footer(text="BRN ESPORTS OFFICIAL BOT")
            if i == 0:
                await inter.response.send_message(embed=e)
            else:
                await inter.followup.send(embed=e)

    @app_commands.command(name="setslots", description="Update the number of tournament slots.")
    @app_commands.describe(slots="Total team slots (e.g. 16, 32, 64)")
    @app_commands.default_permissions(manage_guild=True)
    async def setslots(self, inter: discord.Interaction, slots: app_commands.Range[int, 2, 256]):
        if not _is_admin(inter):
            await inter.response.send_message("Manage Server permission required.", ephemeral=True)
            return
        g = get_guild(inter.guild_id)
        g["max_slots"] = int(slots)
        save_guild(inter.guild_id, g)
        await inter.response.send_message(f"✅ Slots updated to **{slots}**.")

    @app_commands.command(name="setteamsize", description="Update players per team.")
    @app_commands.describe(size="Players per team (1-10)")
    @app_commands.default_permissions(manage_guild=True)
    async def setteamsize(self, inter: discord.Interaction, size: app_commands.Range[int, 1, 10]):
        if not _is_admin(inter):
            await inter.response.send_message("Manage Server permission required.", ephemeral=True)
            return
        g = get_guild(inter.guild_id)
        g["team_size"] = int(size)
        save_guild(inter.guild_id, g)
        await inter.response.send_message(f"✅ Team size updated to **{size}**.")

    @app_commands.command(name="settournamentname", description="Rename the current tournament.")
    @app_commands.describe(name="New tournament name")
    @app_commands.default_permissions(manage_guild=True)
    async def setname(self, inter: discord.Interaction, name: str):
        if not _is_admin(inter):
            await inter.response.send_message("Manage Server permission required.", ephemeral=True)
            return
        g = get_guild(inter.guild_id)
        g["tournament_name"] = name[:64]
        save_guild(inter.guild_id, g)
        await inter.response.send_message(f"✅ Tournament renamed to **{name}**.")

    @app_commands.command(name="endtournament", description="End and reset the current tournament.")
    @app_commands.default_permissions(manage_guild=True)
    async def end_t(self, inter: discord.Interaction):
        if not _is_admin(inter):
            await inter.response.send_message("Manage Server permission required.", ephemeral=True)
            return
        g = get_guild(inter.guild_id)
        name = g.get("tournament_name", "Tournament")
        g.update({"running": False, "paused": False, "teams": [], "groups": {}, "schedule": [], "points": []})
        save_guild(inter.guild_id, g)
        e = discord.Embed(title="🏁 Tournament Ended", description=f"**{name}** is now closed. GG to all teams!", color=0xE74C3C)
        e.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        await inter.response.send_message(embed=e)

    @app_commands.command(name="announce", description="Send an announcement embed in this channel.")
    @app_commands.describe(title="Announcement title", message="Announcement message", ping_everyone="Ping @everyone?")
    @app_commands.default_permissions(manage_messages=True)
    async def announce(self, inter: discord.Interaction, title: str, message: str, ping_everyone: bool = False):
        if not inter.user.guild_permissions.manage_messages:
            await inter.response.send_message("Manage Messages permission required.", ephemeral=True)
            return
        e = discord.Embed(title=f"📢 {title}", description=message.replace("\\n", "\n"), color=ACCENT)
        e.set_footer(text=f"Announced by {inter.user} • BRN ESPORTS")
        content = "@everyone" if ping_everyone else None
        await inter.response.send_message(content=content, embed=e, allowed_mentions=discord.AllowedMentions(everyone=ping_everyone))

    @app_commands.command(name="dmcaptains", description="DM all team captains a message.")
    @app_commands.describe(message="The message to send")
    @app_commands.default_permissions(manage_guild=True)
    async def dmcaptains(self, inter: discord.Interaction, message: str):
        if not _is_admin(inter):
            await inter.response.send_message("Manage Server permission required.", ephemeral=True)
            return
        await inter.response.defer(ephemeral=True, thinking=True)
        g = get_guild(inter.guild_id)
        sent, failed = 0, 0
        for t in g.get("teams", []):
            uid = t.get("captain_id")
            try:
                user = inter.guild.get_member(uid) or await inter.client.fetch_user(uid)
                e = discord.Embed(
                    title=f"📨 {g.get('tournament_name','Tournament')} — Notice",
                    description=message.replace("\\n", "\n"),
                    color=BRAND,
                )
                e.set_footer(text=f"From {inter.guild.name} • BRN ESPORTS")
                await user.send(embed=e)
                sent += 1
            except Exception:
                failed += 1
        await inter.followup.send(f"✅ Sent to **{sent}** captains, failed for **{failed}**.", ephemeral=True)

    # ---------------- Schedule ----------------

    @app_commands.command(name="addmatch", description="Add a match to the schedule.")
    @app_commands.describe(match_no="Match number", team_a="Team A", team_b="Team B (optional)", time="When (free text, e.g. 'Sat 8pm IST')", room_id="Room ID (optional)", room_pass="Room password (optional)")
    @app_commands.default_permissions(manage_guild=True)
    async def addmatch(self, inter: discord.Interaction, match_no: int, team_a: str, team_b: str = "", time: str = "TBD", room_id: str = "", room_pass: str = ""):
        if not _is_admin(inter):
            await inter.response.send_message("Manage Server permission required.", ephemeral=True)
            return
        g = get_guild(inter.guild_id)
        sched = list(g.get("schedule", []))
        sched = [m for m in sched if int(m.get("no", 0)) != int(match_no)]
        sched.append({"no": int(match_no), "a": team_a, "b": team_b, "time": time, "room_id": room_id, "room_pass": room_pass})
        sched.sort(key=lambda m: int(m.get("no", 0)))
        g["schedule"] = sched
        save_guild(inter.guild_id, g)
        await inter.response.send_message(f"✅ Match #{match_no} added/updated.", ephemeral=True)

    @app_commands.command(name="removematch", description="Remove a match from the schedule.")
    @app_commands.describe(match_no="Match number")
    @app_commands.default_permissions(manage_guild=True)
    async def removematch(self, inter: discord.Interaction, match_no: int):
        if not _is_admin(inter):
            await inter.response.send_message("Manage Server permission required.", ephemeral=True)
            return
        g = get_guild(inter.guild_id)
        sched = [m for m in g.get("schedule", []) if int(m.get("no", 0)) != int(match_no)]
        g["schedule"] = sched
        save_guild(inter.guild_id, g)
        await inter.response.send_message(f"✅ Match #{match_no} removed.", ephemeral=True)

    @app_commands.command(name="schedule", description="Show the match schedule.")
    async def schedule(self, inter: discord.Interaction):
        g = get_guild(inter.guild_id)
        sched = g.get("schedule", [])
        if not sched:
            await inter.response.send_message("No matches scheduled yet.", ephemeral=True)
            return
        e = discord.Embed(title=f"📅 {g.get('tournament_name','Tournament')} — Schedule", color=BRAND)
        for m in sched[:25]:
            vs = f"**{m.get('a')}** vs **{m.get('b')}**" if m.get("b") else f"**{m.get('a')}**"
            extras = []
            if m.get("room_id"):
                extras.append(f"Room ID: `{m['room_id']}`")
            if m.get("room_pass"):
                extras.append(f"Pass: `{m['room_pass']}`")
            extra_str = ("\n" + " • ".join(extras)) if extras else ""
            e.add_field(name=f"Match #{m.get('no')} — {m.get('time','TBD')}", value=vs + extra_str, inline=False)
        e.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        await inter.response.send_message(embed=e)

    # ---------------- Point table ----------------

    @app_commands.command(name="setpoints", description="Set points for a team (creates entry if missing).")
    @app_commands.describe(team="Team name", points="Total points", kills="Total kills", wins="Wins (optional)")
    @app_commands.default_permissions(manage_guild=True)
    async def setpoints(self, inter: discord.Interaction, team: str, points: int, kills: int = 0, wins: int = 0):
        if not _is_admin(inter):
            await inter.response.send_message("Manage Server permission required.", ephemeral=True)
            return
        g = get_guild(inter.guild_id)
        pts = list(g.get("points", []))
        for p in pts:
            if p["team"].lower() == team.lower():
                p["points"], p["kills"], p["wins"] = int(points), int(kills), int(wins)
                break
        else:
            pts.append({"team": team, "points": int(points), "kills": int(kills), "wins": int(wins)})
        g["points"] = pts
        save_guild(inter.guild_id, g)
        await inter.response.send_message(f"✅ Updated points for **{team}**.", ephemeral=True)

    @app_commands.command(name="addpoints", description="Add points/kills/wins to a team.")
    @app_commands.describe(team="Team name", points="Points to add", kills="Kills to add", wins="Wins to add")
    @app_commands.default_permissions(manage_guild=True)
    async def addpoints(self, inter: discord.Interaction, team: str, points: int = 0, kills: int = 0, wins: int = 0):
        if not _is_admin(inter):
            await inter.response.send_message("Manage Server permission required.", ephemeral=True)
            return
        g = get_guild(inter.guild_id)
        pts = list(g.get("points", []))
        for p in pts:
            if p["team"].lower() == team.lower():
                p["points"] += int(points)
                p["kills"] += int(kills)
                p["wins"] += int(wins)
                break
        else:
            pts.append({"team": team, "points": int(points), "kills": int(kills), "wins": int(wins)})
        g["points"] = pts
        save_guild(inter.guild_id, g)
        await inter.response.send_message(f"✅ Added to **{team}**.", ephemeral=True)

    @app_commands.command(name="resetpoints", description="Reset the entire point table.")
    @app_commands.default_permissions(manage_guild=True)
    async def resetpoints(self, inter: discord.Interaction):
        if not _is_admin(inter):
            await inter.response.send_message("Manage Server permission required.", ephemeral=True)
            return
        g = get_guild(inter.guild_id)
        g["points"] = []
        save_guild(inter.guild_id, g)
        await inter.response.send_message("✅ Point table reset.")

    @app_commands.command(name="points", description="Show the point table.")
    async def points(self, inter: discord.Interaction):
        g = get_guild(inter.guild_id)
        pts = sorted(g.get("points", []), key=lambda p: (p.get("points", 0), p.get("kills", 0)), reverse=True)
        if not pts:
            await inter.response.send_message("Point table is empty.", ephemeral=True)
            return
        header = f"`{'#':<3}{'TEAM':<22}{'PTS':>5}{'KIL':>5}{'WIN':>5}`\n"
        rows = []
        for i, p in enumerate(pts[:25], 1):
            tname = (p["team"][:20] + "..") if len(p["team"]) > 20 else p["team"]
            rows.append(f"`{i:<3}{tname:<22}{p.get('points',0):>5}{p.get('kills',0):>5}{p.get('wins',0):>5}`")
        e = discord.Embed(
            title=f"🏅 {g.get('tournament_name','Tournament')} — Point Table",
            description=header + "\n".join(rows),
            color=BRAND,
        )
        e.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        await inter.response.send_message(embed=e)

    # ---------------- Lineup / Groups ----------------

    @app_commands.command(name="lineup", description="Show group distribution.")
    async def lineup(self, inter: discord.Interaction):
        g = get_guild(inter.guild_id)
        groups = g.get("groups", {})
        if not groups:
            await inter.response.send_message("No groups created yet. Use the Manage Groups button.", ephemeral=True)
            return
        e = discord.Embed(title="📊 Group Lineup", color=BRAND)
        for key, members in groups.items():
            e.add_field(
                name=f"Group {key} ({len(members)})",
                value="\n".join(f"• {m}" for m in members) if members else "*empty*",
                inline=True,
            )
        e.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        await inter.response.send_message(embed=e)

    @app_commands.command(name="removeteam", description="Remove a team by name.")
    @app_commands.describe(team="Team name to remove")
    @app_commands.default_permissions(manage_guild=True)
    async def removeteam(self, inter: discord.Interaction, team: str):
        if not _is_admin(inter):
            await inter.response.send_message("Manage Server permission required.", ephemeral=True)
            return
        g = get_guild(inter.guild_id)
        before = len(g.get("teams", []))
        g["teams"] = [t for t in g.get("teams", []) if t.get("name", "").lower() != team.lower()]
        save_guild(inter.guild_id, g)
        diff = before - len(g["teams"])
        await inter.response.send_message(f"✅ Removed **{diff}** team(s) named **{team}**.", ephemeral=True)

    @app_commands.command(name="idp", description="Send IDP (Room ID & Password) for a match.")
    @app_commands.describe(match_no="Match number", room_id="Room ID", room_pass="Room password")
    @app_commands.default_permissions(manage_guild=True)
    async def idp(self, inter: discord.Interaction, match_no: int, room_id: str, room_pass: str):
        if not _is_admin(inter):
            await inter.response.send_message("Manage Server permission required.", ephemeral=True)
            return
        g = get_guild(inter.guild_id)
        sched = list(g.get("schedule", []))
        for m in sched:
            if int(m.get("no", 0)) == int(match_no):
                m["room_id"] = room_id
                m["room_pass"] = room_pass
                break
        g["schedule"] = sched
        save_guild(inter.guild_id, g)
        e = discord.Embed(
            title=f"🎮 IDP — Match #{match_no}",
            description=f"**Room ID:** `{room_id}`\n**Password:** `{room_pass}`\n\nAll teams be ready 5 minutes before slot time.",
            color=ACCENT,
        )
        e.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        await inter.response.send_message(embed=e)

    @app_commands.command(name="help", description="Show all bot commands.")
    async def help_cmd(self, inter: discord.Interaction):
        e = discord.Embed(
            title="🤖 BRN ESPORTS BOT — Command Guide",
            color=BRAND,
            description="Everything you need to run a tournament.",
        )
        e.add_field(
            name="🏆 Tournament",
            value=(
                "`?t` — open the tournament panel\n"
                "`/info` — tournament status\n"
                "`/settournamentname` `/setslots` `/setteamsize`\n"
                "`/endtournament`"
            ),
            inline=False,
        )
        e.add_field(
            name="📋 Teams",
            value="`/teamlist` • `/removeteam` • `/lineup`",
            inline=False,
        )
        e.add_field(
            name="📅 Schedule & IDP",
            value="`/addmatch` • `/removematch` • `/schedule` • `/idp`",
            inline=False,
        )
        e.add_field(
            name="🏅 Point Table",
            value="`/setpoints` • `/addpoints` • `/resetpoints` • `/points`",
            inline=False,
        )
        e.add_field(
            name="📢 Communication",
            value="`/announce` • `/dmcaptains`",
            inline=False,
        )
        e.add_field(
            name="🛡️ Moderation",
            value="`/ban` • `/kick` • `/mute` • `/unmute` • `?purge <n|@user>`",
            inline=False,
        )
        e.add_field(
            name="🎉 Giveaway",
            value="`?gstart <time> <prize> <winners>winner`\nExample: `?gstart 10m Nitro 1winner`",
            inline=False,
        )
        e.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        await inter.response.send_message(embed=e, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Management(bot))
