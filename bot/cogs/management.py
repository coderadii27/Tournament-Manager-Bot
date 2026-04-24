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


class AnnounceModal(discord.ui.Modal, title="📢 New Announcement"):
    def __init__(self, ping_everyone: bool, image_url: str):
        super().__init__(timeout=600)
        self.ping_everyone = ping_everyone
        self.image_url = image_url
        self.title_in = discord.ui.TextInput(label="Title", max_length=200, placeholder="Tournament Update")
        self.body_in = discord.ui.TextInput(
            label="Message (Shift+Enter for new line)",
            style=discord.TextStyle.paragraph,
            max_length=3800,
            placeholder="Type your announcement here...\nUse Shift+Enter to add new lines.",
        )
        self.add_item(self.title_in)
        self.add_item(self.body_in)

    async def on_submit(self, inter: discord.Interaction):
        e = discord.Embed(title=f"📢 {self.title_in}", description=str(self.body_in), color=ACCENT)
        if self.image_url:
            e.set_image(url=self.image_url)
        e.set_footer(text=f"Announced by {inter.user} • BRN ESPORTS")
        content = "@everyone" if self.ping_everyone else None
        await inter.response.send_message(
            content=content, embed=e,
            allowed_mentions=discord.AllowedMentions(everyone=self.ping_everyone),
        )


class EmbedModal(discord.ui.Modal, title="✨ Custom Embed"):
    def __init__(self, color_hex: str, image_url: str, thumbnail_url: str, footer_url: str):
        super().__init__(timeout=600)
        self.color_hex = color_hex
        self.image_url = image_url
        self.thumbnail_url = thumbnail_url
        self.footer_url = footer_url
        self.title_in = discord.ui.TextInput(label="Title", max_length=256, required=False)
        self.body_in = discord.ui.TextInput(
            label="Description (Shift+Enter for new lines)",
            style=discord.TextStyle.paragraph,
            max_length=3800,
        )
        self.footer_in = discord.ui.TextInput(label="Footer text", max_length=200, required=False, default="BRN ESPORTS OFFICIAL BOT")
        self.add_item(self.title_in)
        self.add_item(self.body_in)
        self.add_item(self.footer_in)

    async def on_submit(self, inter: discord.Interaction):
        try:
            color = int(self.color_hex.lstrip("#"), 16) if self.color_hex else BRAND
        except ValueError:
            color = BRAND
        e = discord.Embed(
            title=str(self.title_in) or None,
            description=str(self.body_in),
            color=color,
        )
        if self.image_url:
            e.set_image(url=self.image_url)
        if self.thumbnail_url:
            e.set_thumbnail(url=self.thumbnail_url)
        footer_text = str(self.footer_in) or "BRN ESPORTS OFFICIAL BOT"
        if self.footer_url:
            e.set_footer(text=footer_text, icon_url=self.footer_url)
        else:
            e.set_footer(text=footer_text)
        await inter.response.send_message(embed=e)


class DMCaptainsModal(discord.ui.Modal, title="📨 DM All Captains"):
    def __init__(self, bot):
        super().__init__(timeout=600)
        self.bot = bot
        self.title_in = discord.ui.TextInput(label="Title", default="Tournament Notice", max_length=200)
        self.body_in = discord.ui.TextInput(
            label="Message (Shift+Enter for new lines)",
            style=discord.TextStyle.paragraph,
            max_length=3800,
        )
        self.add_item(self.title_in)
        self.add_item(self.body_in)

    async def on_submit(self, inter: discord.Interaction):
        await inter.response.defer(ephemeral=True, thinking=True)
        g = get_guild(inter.guild_id)
        sent, failed = 0, 0
        for t in g.get("teams", []):
            uid = t.get("captain_id")
            try:
                user = inter.guild.get_member(uid) or await self.bot.fetch_user(uid)
                e = discord.Embed(title=f"📨 {self.title_in}", description=str(self.body_in), color=BRAND)
                if inter.guild.icon:
                    e.set_thumbnail(url=inter.guild.icon.url)
                e.set_footer(text=f"From {inter.guild.name} • BRN ESPORTS")
                await user.send(embed=e)
                sent += 1
            except Exception:
                failed += 1
        await inter.followup.send(f"✅ Sent to **{sent}** captains. Failed for **{failed}**.", ephemeral=True)


class GreetModal(discord.ui.Modal, title="👋 Greet Members (DM)"):
    def __init__(self, image_url: str, footer_gif: str, only_role: discord.Role | None):
        super().__init__(timeout=600)
        self.image_url = image_url
        self.footer_gif = footer_gif
        self.only_role = only_role
        self.title_in = discord.ui.TextInput(label="DM Title", default="Welcome to BRN ESPORTS!", max_length=200)
        self.body_in = discord.ui.TextInput(
            label="DM Message (Shift+Enter for new lines)",
            style=discord.TextStyle.paragraph,
            max_length=3800,
            placeholder="Hey {user}, welcome to our tournament server!\nCheck out the rules and how to register.",
        )
        self.add_item(self.title_in)
        self.add_item(self.body_in)

    async def on_submit(self, inter: discord.Interaction):
        await inter.response.defer(ephemeral=True, thinking=True)
        guild = inter.guild
        members = [m for m in guild.members if not m.bot]
        if self.only_role:
            members = [m for m in members if self.only_role in m.roles]

        sent, failed = 0, 0
        for m in members:
            try:
                body = str(self.body_in).replace("{user}", m.mention).replace("{name}", m.display_name).replace("{server}", guild.name)
                e = discord.Embed(title=str(self.title_in), description=body, color=BRAND)
                if self.image_url:
                    e.set_image(url=self.image_url)
                if guild.icon:
                    e.set_thumbnail(url=guild.icon.url)
                if self.footer_gif:
                    e.set_footer(text=f"From {guild.name} • BRN ESPORTS", icon_url=self.footer_gif)
                else:
                    e.set_footer(text=f"From {guild.name} • BRN ESPORTS")
                await m.send(embed=e)
                sent += 1
            except Exception:
                failed += 1
        await inter.followup.send(f"✅ Greet DM sent to **{sent}** members. Failed for **{failed}** (DMs closed).", ephemeral=True)


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

    # ---------------- IDP private channel ----------------

    @app_commands.command(name="sendidp", description="Create a private IDP channel visible only to a chosen role.")
    @app_commands.describe(role="Role allowed to view the IDP channel (e.g. @idp access)")
    @app_commands.default_permissions(manage_channels=True)
    async def sendidp(self, inter: discord.Interaction, role: discord.Role):
        if not inter.user.guild_permissions.manage_channels:
            await inter.response.send_message("Manage Channels permission required.", ephemeral=True)
            return
        await inter.response.defer(ephemeral=True, thinking=True)
        guild = inter.guild
        category = discord.utils.get(guild.categories, name="🏆 BRN ESPORTS")
        if category is None:
            category = await guild.create_category("🏆 BRN ESPORTS", reason="IDP setup")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, manage_messages=True, manage_channels=True,
            ),
            role: discord.PermissionOverwrite(
                view_channel=True, send_messages=False, read_message_history=True, add_reactions=True,
            ),
        }
        for r in guild.roles:
            if r.is_default():
                continue
            p = r.permissions
            if p.administrator or p.manage_guild or p.manage_channels:
                overwrites[r] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                )

        ch = discord.utils.get(guild.text_channels, name="—͟͞͞-⨳〢idp")
        if ch is None:
            ch = await guild.create_text_channel(
                "—͟͞͞-⨳〢idp", category=category, overwrites=overwrites,
                reason=f"Private IDP channel for {role.name}",
            )
        else:
            for target, ow in overwrites.items():
                try:
                    await ch.set_permissions(target, overwrite=ow)
                except discord.Forbidden:
                    pass

        # Save IDP role so registration auto-grants it to IGLs
        g = get_guild(guild.id)
        g["idp_channel_id"] = ch.id
        g["idp_role_id"] = role.id
        save_guild(guild.id, g)

        e = discord.Embed(
            title="🎟️ IDP Channel Ready",
            description=(
                f"📡 **Room ID & Password** updates will be posted in {ch.mention}.\n"
                f"👀 Visible only to {role.mention} and staff.\n"
                f"✨ IGLs of confirmed teams will automatically get {role.mention}."
            ),
            color=BRAND,
        )
        e.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        await ch.send(content=role.mention, embed=e, allowed_mentions=discord.AllowedMentions(roles=True))
        await inter.followup.send(f"✅ IDP channel ready: {ch.mention}", ephemeral=True)

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

    @app_commands.command(name="announce", description="Open a multi-line announcement form for this channel.")
    @app_commands.describe(ping_everyone="Ping @everyone?", image_url="Optional banner image URL")
    @app_commands.default_permissions(manage_messages=True)
    async def announce(self, inter: discord.Interaction, ping_everyone: bool = False, image_url: str = ""):
        if not inter.user.guild_permissions.manage_messages:
            await inter.response.send_message("Manage Messages permission required.", ephemeral=True)
            return
        await inter.response.send_modal(AnnounceModal(ping_everyone=ping_everyone, image_url=image_url))

    @app_commands.command(name="dmcaptains", description="Open a multi-line form to DM all team captains.")
    @app_commands.default_permissions(manage_guild=True)
    async def dmcaptains(self, inter: discord.Interaction):
        if not _is_admin(inter):
            await inter.response.send_message("Manage Server permission required.", ephemeral=True)
            return
        await inter.response.send_modal(DMCaptainsModal(self.bot))

    @app_commands.command(name="greet", description="DM a welcome message + image to all members (or a role).")
    @app_commands.describe(image_url="Banner image URL (optional)", footer_gif="Footer icon/GIF URL (optional)", role="Only DM members with this role (optional)")
    @app_commands.default_permissions(manage_guild=True)
    async def greet(self, inter: discord.Interaction, image_url: str = "", footer_gif: str = "", role: discord.Role = None):
        if not _is_admin(inter):
            await inter.response.send_message("Manage Server permission required.", ephemeral=True)
            return
        await inter.response.send_modal(GreetModal(image_url=image_url, footer_gif=footer_gif, only_role=role))

    @app_commands.command(name="sayembed", description="Build a custom embed with a multi-line form.")
    @app_commands.describe(color_hex="Hex color e.g. #9B5CF6", image_url="Banner image URL", thumbnail_url="Thumbnail URL", footer_icon_url="Footer icon/GIF URL")
    @app_commands.default_permissions(manage_messages=True)
    async def sayembed(self, inter: discord.Interaction, color_hex: str = "", image_url: str = "", thumbnail_url: str = "", footer_icon_url: str = ""):
        if not inter.user.guild_permissions.manage_messages:
            await inter.response.send_message("Manage Messages permission required.", ephemeral=True)
            return
        await inter.response.send_modal(EmbedModal(color_hex=color_hex, image_url=image_url, thumbnail_url=thumbnail_url, footer_url=footer_icon_url))

    @app_commands.command(name="poll", description="Create a quick yes/no or up to 5-option poll.")
    @app_commands.describe(question="Poll question", option1="Option 1", option2="Option 2", option3="Option 3 (optional)", option4="Option 4 (optional)", option5="Option 5 (optional)")
    async def poll(self, inter: discord.Interaction, question: str, option1: str = "Yes", option2: str = "No", option3: str = "", option4: str = "", option5: str = ""):
        opts = [o for o in [option1, option2, option3, option4, option5] if o]
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        desc = "\n".join(f"{emojis[i]}  {o}" for i, o in enumerate(opts))
        e = discord.Embed(title=f"📊 {question}", description=desc, color=BRAND)
        e.set_footer(text=f"Poll by {inter.user} • BRN ESPORTS")
        await inter.response.send_message(embed=e)
        msg = await inter.original_response()
        for i in range(len(opts)):
            try:
                await msg.add_reaction(emojis[i])
            except discord.HTTPException:
                pass

    @app_commands.command(name="serverinfo", description="Show server information.")
    async def serverinfo(self, inter: discord.Interaction):
        gd = inter.guild
        e = discord.Embed(title=f"🌐 {gd.name}", color=BRAND)
        if gd.icon:
            e.set_thumbnail(url=gd.icon.url)
        e.add_field(name="Members", value=f"`{gd.member_count}`")
        e.add_field(name="Roles", value=f"`{len(gd.roles)}`")
        e.add_field(name="Channels", value=f"`{len(gd.channels)}`")
        e.add_field(name="Created", value=discord.utils.format_dt(gd.created_at, "R"))
        e.add_field(name="Owner", value=gd.owner.mention if gd.owner else "?")
        e.add_field(name="Boosts", value=f"`{gd.premium_subscription_count}`")
        e.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        await inter.response.send_message(embed=e)

    @app_commands.command(name="userinfo", description="Show info about a user.")
    @app_commands.describe(user="User (default: you)")
    async def userinfo(self, inter: discord.Interaction, user: discord.Member = None):
        u = user or inter.user
        e = discord.Embed(title=f"👤 {u}", color=BRAND)
        e.set_thumbnail(url=u.display_avatar.url)
        e.add_field(name="ID", value=f"`{u.id}`", inline=False)
        e.add_field(name="Joined Server", value=discord.utils.format_dt(u.joined_at, "R") if u.joined_at else "?")
        e.add_field(name="Account Created", value=discord.utils.format_dt(u.created_at, "R"))
        roles = [r.mention for r in u.roles if r.name != "@everyone"]
        e.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles[:20]) or "—", inline=False)
        e.set_footer(text="BRN ESPORTS OFFICIAL BOT")
        await inter.response.send_message(embed=e)

    @app_commands.command(name="avatar", description="Show a user's avatar.")
    @app_commands.describe(user="User (default: you)")
    async def avatar(self, inter: discord.Interaction, user: discord.Member = None):
        u = user or inter.user
        e = discord.Embed(title=f"🖼️ {u.display_name}'s Avatar", color=BRAND)
        e.set_image(url=u.display_avatar.url)
        await inter.response.send_message(embed=e)

    @app_commands.command(name="setwelcome", description="Set the welcome channel + message for new members (auto-greet).")
    @app_commands.describe(channel="Channel to greet new members in", message="Welcome text. Use {user}, {server}.", image_url="Optional banner image URL")
    @app_commands.default_permissions(manage_guild=True)
    async def setwelcome(self, inter: discord.Interaction, channel: discord.TextChannel, message: str, image_url: str = ""):
        if not _is_admin(inter):
            await inter.response.send_message("Manage Server permission required.", ephemeral=True)
            return
        g = get_guild(inter.guild_id)
        g["welcome"] = {"channel_id": channel.id, "message": message, "image_url": image_url}
        save_guild(inter.guild_id, g)
        await inter.response.send_message(f"✅ Welcome channel set to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="welcomeoff", description="Disable auto-welcome for new members.")
    @app_commands.default_permissions(manage_guild=True)
    async def welcomeoff(self, inter: discord.Interaction):
        if not _is_admin(inter):
            await inter.response.send_message("Manage Server permission required.", ephemeral=True)
            return
        g = get_guild(inter.guild_id)
        g.pop("welcome", None)
        save_guild(inter.guild_id, g)
        await inter.response.send_message("✅ Auto-welcome disabled.", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        g = get_guild(member.guild.id)
        w = g.get("welcome")
        if not w or not w.get("channel_id"):
            return
        ch = member.guild.get_channel(w["channel_id"])
        if ch is None:
            return
        msg = w.get("message", "Welcome {user} to {server}!").replace("{user}", member.mention).replace("{server}", member.guild.name).replace("{name}", member.display_name)
        e = discord.Embed(title=f"👋 Welcome to {member.guild.name}!", description=msg, color=BRAND)
        e.set_thumbnail(url=member.display_avatar.url)
        if w.get("image_url"):
            e.set_image(url=w["image_url"])
        e.set_footer(text=f"Member #{member.guild.member_count} • BRN ESPORTS")
        try:
            await ch.send(content=member.mention, embed=e)
        except discord.HTTPException:
            pass

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
            value="`/announce` • `/dmcaptains` • `/greet` • `/sayembed` • `/poll`",
            inline=False,
        )
        e.add_field(
            name="👋 Welcome System",
            value="`/setwelcome` • `/welcomeoff`",
            inline=False,
        )
        e.add_field(
            name="🔍 Info",
            value="`/serverinfo` • `/userinfo` • `/avatar`",
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

    # ---------------- Force resync slash commands ----------------

    @commands.command(name="sync")
    @commands.has_permissions(manage_guild=True)
    async def sync_cmds(self, ctx: commands.Context):
        """Force re-sync of all slash commands to this guild."""
        if ctx.guild is None:
            return
        msg = await ctx.reply("⏳ Resyncing slash commands…", mention_author=False)
        try:
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
            await msg.edit(content=f"✅ Resynced **{len(synced)}** commands to **{ctx.guild.name}**.")
        except Exception as e:
            await msg.edit(content=f"❌ Sync failed: `{e}`")

    @commands.command(name="syncall")
    @commands.has_permissions(manage_guild=True)
    async def sync_all(self, ctx: commands.Context):
        """Force re-sync of all slash commands to every guild the bot is in."""
        msg = await ctx.reply("⏳ Resyncing slash commands to every guild…", mention_author=False)
        total = 0
        failed = 0
        for guild in ctx.bot.guilds:
            try:
                ctx.bot.tree.copy_global_to(guild=guild)
                synced = await ctx.bot.tree.sync(guild=guild)
                total += len(synced)
            except Exception:
                failed += 1
        await msg.edit(content=f"✅ Synced **{total}** commands across **{len(ctx.bot.guilds) - failed}** guilds. Failed: **{failed}**.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Management(bot))
