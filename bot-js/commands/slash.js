import {
  EmbedBuilder, ModalBuilder, TextInputBuilder, TextInputStyle, ActionRowBuilder, PermissionFlagsBits,
  ChannelType,
} from "discord.js";
import { BRAND, ACCENT, parseDurationSec } from "../constants.js";
import { getGuild, saveGuild } from "../state.js";

const isAdmin = (i) => i.memberPermissions?.has(PermissionFlagsBits.ManageGuild);

export async function handleSlash(i) {
  const n = i.commandName;

  if (n === "ban") return doBan(i);
  if (n === "kick") return doKick(i);
  if (n === "mute") return doMute(i);
  if (n === "unmute") return doUnmute(i);

  if (n === "info") return doInfo(i);
  if (n === "teamlist") return doTeamlist(i);
  if (n === "setslots") return doSetSlots(i);
  if (n === "setteamsize") return doSetTeamSize(i);
  if (n === "settournamentname") return doSetName(i);
  if (n === "endtournament") return doEnd(i);
  if (n === "removeteam") return doRemoveTeam(i);
  if (n === "lineup") return doLineup(i);

  if (n === "addmatch") return doAddMatch(i);
  if (n === "removematch") return doRemoveMatch(i);
  if (n === "schedule") return doSchedule(i);
  if (n === "idp") return doIdp(i);

  if (n === "setpoints") return doSetPoints(i);
  if (n === "addpoints") return doAddPoints(i);
  if (n === "resetpoints") return doResetPoints(i);
  if (n === "points") return doPoints(i);

  if (n === "announce") return openAnnounceModal(i);
  if (n === "dmcaptains") return openDMCaptainsModal(i);
  if (n === "greet") return openGreetModal(i);
  if (n === "sayembed") return openEmbedModal(i);
  if (n === "poll") return doPoll(i);

  if (n === "serverinfo") return doServerInfo(i);
  if (n === "userinfo") return doUserInfo(i);
  if (n === "avatar") return doAvatar(i);

  if (n === "setwelcome") return doSetWelcome(i);
  if (n === "welcomeoff") return doWelcomeOff(i);

  if (n === "help") return doHelp(i);
}

async function doBan(i) {
  const u = i.options.getMember("user");
  const reason = i.options.getString("reason") || "No reason provided";
  if (!u) return i.reply({ content: "User not found.", ephemeral: true });
  try { await u.ban({ reason }); }
  catch { return i.reply({ content: "I can't ban that user.", ephemeral: true }); }
  const e = new EmbedBuilder().setTitle("🔨 User Banned").setColor(0xe74c3c)
    .addFields({ name: "User", value: `${u.user.tag} (\`${u.id}\`)` }, { name: "Reason", value: reason })
    .setFooter({ text: `By ${i.user.tag}` });
  return i.reply({ embeds: [e] });
}

async function doKick(i) {
  const u = i.options.getMember("user");
  const reason = i.options.getString("reason") || "No reason provided";
  if (!u) return i.reply({ content: "User not found.", ephemeral: true });
  try { await u.kick(reason); }
  catch { return i.reply({ content: "I can't kick that user.", ephemeral: true }); }
  const e = new EmbedBuilder().setTitle("👢 User Kicked").setColor(0xe67e22)
    .addFields({ name: "User", value: `${u.user.tag} (\`${u.id}\`)` }, { name: "Reason", value: reason })
    .setFooter({ text: `By ${i.user.tag}` });
  return i.reply({ embeds: [e] });
}

async function doMute(i) {
  const u = i.options.getMember("user");
  const time = i.options.getString("time");
  const reason = i.options.getString("reason") || "No reason provided";
  if (!u) return i.reply({ content: "User not found.", ephemeral: true });
  const secs = parseDurationSec(time);
  const max = 28 * 86400;
  if (!secs || secs <= 0 || secs > max) return i.reply({ content: "Invalid time. Use forms like `10m`, `2h`, `1d` (max 28 days).", ephemeral: true });
  try { await u.timeout(secs * 1000, reason); }
  catch { return i.reply({ content: "I can't timeout that user.", ephemeral: true }); }
  const e = new EmbedBuilder().setTitle("🔇 User Muted").setColor(0xf1c40f)
    .addFields(
      { name: "User", value: `${u.user.tag} (\`${u.id}\`)` },
      { name: "Duration", value: time, inline: true },
      { name: "Reason", value: reason },
    ).setFooter({ text: `By ${i.user.tag}` });
  return i.reply({ embeds: [e] });
}

async function doUnmute(i) {
  const u = i.options.getMember("user");
  if (!u) return i.reply({ content: "User not found.", ephemeral: true });
  try { await u.timeout(null, `Unmuted by ${i.user.tag}`); }
  catch { return i.reply({ content: "I can't unmute that user.", ephemeral: true }); }
  const e = new EmbedBuilder().setTitle("🔊 User Unmuted").setColor(0x2ecc71)
    .addFields({ name: "User", value: `${u.user.tag} (\`${u.id}\`)` })
    .setFooter({ text: `By ${i.user.tag}` });
  return i.reply({ embeds: [e] });
}

async function doInfo(i) {
  const g = getGuild(i.guildId);
  const status = g.running && !g.paused ? "🟢 Running" : g.paused ? "🟡 Paused" : "⚪ Idle";
  const e = new EmbedBuilder().setTitle(`🏆 ${g.tournament_name}`).setColor(BRAND)
    .addFields(
      { name: "Slots", value: `\`${g.teams.length}/${g.max_slots}\``, inline: true },
      { name: "Team Size", value: `\`${g.team_size}\``, inline: true },
      { name: "Status", value: status, inline: true },
      { name: "Groups", value: `\`${Object.keys(g.groups || {}).length}\``, inline: true },
    ).setFooter({ text: "BRN ESPORTS OFFICIAL BOT" });
  return i.reply({ embeds: [e] });
}

async function doTeamlist(i) {
  const g = getGuild(i.guildId);
  if (!g.teams.length) return i.reply({ content: "No teams registered yet.", ephemeral: true });
  const lines = g.teams.map((t, idx) => `\`${String(idx + 1).padStart(2)}.\` **${t.name}** — <@${t.captain_id}>`);
  const chunks = [];
  let cur = "";
  for (const ln of lines) {
    if (cur.length + ln.length + 1 > 3800) { chunks.push(cur); cur = ""; }
    cur += ln + "\n";
  }
  if (cur) chunks.push(cur);
  for (let idx = 0; idx < chunks.length; idx++) {
    const e = new EmbedBuilder().setColor(BRAND)
      .setTitle(`📋 Confirmed Teams (${g.teams.length}/${g.max_slots})${chunks.length > 1 ? ` — page ${idx + 1}` : ""}`)
      .setDescription(chunks[idx]).setFooter({ text: "BRN ESPORTS OFFICIAL BOT" });
    if (idx === 0) await i.reply({ embeds: [e] });
    else await i.followUp({ embeds: [e] });
  }
}

async function doSetSlots(i) {
  if (!isAdmin(i)) return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  const g = getGuild(i.guildId);
  g.max_slots = i.options.getInteger("slots");
  saveGuild(i.guildId, g);
  return i.reply(`✅ Slots updated to **${g.max_slots}**.`);
}

async function doSetTeamSize(i) {
  if (!isAdmin(i)) return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  const g = getGuild(i.guildId);
  g.team_size = i.options.getInteger("size");
  saveGuild(i.guildId, g);
  return i.reply(`✅ Team size updated to **${g.team_size}**.`);
}

async function doSetName(i) {
  if (!isAdmin(i)) return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  const g = getGuild(i.guildId);
  g.tournament_name = i.options.getString("name").slice(0, 64);
  saveGuild(i.guildId, g);
  return i.reply(`✅ Tournament renamed to **${g.tournament_name}**.`);
}

async function doEnd(i) {
  if (!isAdmin(i)) return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  const g = getGuild(i.guildId);
  const name = g.tournament_name;
  Object.assign(g, { running: false, paused: false, teams: [], groups: {}, schedule: [], points: [] });
  saveGuild(i.guildId, g);
  const e = new EmbedBuilder().setTitle("🏁 Tournament Ended").setColor(0xe74c3c)
    .setDescription(`**${name}** is now closed. GG to all teams!`).setFooter({ text: "BRN ESPORTS OFFICIAL BOT" });
  return i.reply({ embeds: [e] });
}

async function doRemoveTeam(i) {
  if (!isAdmin(i)) return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  const team = i.options.getString("team");
  const g = getGuild(i.guildId);
  const before = g.teams.length;
  g.teams = g.teams.filter(t => t.name.toLowerCase() !== team.toLowerCase());
  saveGuild(i.guildId, g);
  return i.reply({ content: `✅ Removed **${before - g.teams.length}** team(s) named **${team}**.`, ephemeral: true });
}

async function doLineup(i) {
  const g = getGuild(i.guildId);
  const groups = g.groups || {};
  if (!Object.keys(groups).length) return i.reply({ content: "No groups created yet. Use the Manage Groups button.", ephemeral: true });
  const e = new EmbedBuilder().setTitle("📊 Group Lineup").setColor(BRAND);
  for (const [k, members] of Object.entries(groups)) {
    e.addFields({ name: `Group ${k} (${members.length})`, value: members.length ? members.map(m => `• ${m}`).join("\n") : "*empty*", inline: true });
  }
  e.setFooter({ text: "BRN ESPORTS OFFICIAL BOT" });
  return i.reply({ embeds: [e] });
}

async function doAddMatch(i) {
  if (!isAdmin(i)) return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  const g = getGuild(i.guildId);
  const no = i.options.getInteger("match_no");
  const m = {
    no, a: i.options.getString("team_a"), b: i.options.getString("team_b") || "",
    time: i.options.getString("time") || "TBD",
    room_id: i.options.getString("room_id") || "", room_pass: i.options.getString("room_pass") || "",
  };
  g.schedule = (g.schedule || []).filter(x => x.no !== no);
  g.schedule.push(m);
  g.schedule.sort((a, b) => a.no - b.no);
  saveGuild(i.guildId, g);
  return i.reply({ content: `✅ Match #${no} added/updated.`, ephemeral: true });
}

async function doRemoveMatch(i) {
  if (!isAdmin(i)) return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  const g = getGuild(i.guildId);
  const no = i.options.getInteger("match_no");
  g.schedule = (g.schedule || []).filter(x => x.no !== no);
  saveGuild(i.guildId, g);
  return i.reply({ content: `✅ Match #${no} removed.`, ephemeral: true });
}

async function doSchedule(i) {
  const g = getGuild(i.guildId);
  if (!g.schedule?.length) return i.reply({ content: "No matches scheduled yet.", ephemeral: true });
  const e = new EmbedBuilder().setTitle(`📅 ${g.tournament_name} — Schedule`).setColor(BRAND);
  for (const m of g.schedule.slice(0, 25)) {
    const vs = m.b ? `**${m.a}** vs **${m.b}**` : `**${m.a}**`;
    const extras = [];
    if (m.room_id) extras.push(`Room ID: \`${m.room_id}\``);
    if (m.room_pass) extras.push(`Pass: \`${m.room_pass}\``);
    e.addFields({ name: `Match #${m.no} — ${m.time}`, value: vs + (extras.length ? "\n" + extras.join(" • ") : "") });
  }
  e.setFooter({ text: "BRN ESPORTS OFFICIAL BOT" });
  return i.reply({ embeds: [e] });
}

async function doIdp(i) {
  if (!isAdmin(i)) return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  const no = i.options.getInteger("match_no");
  const room_id = i.options.getString("room_id");
  const room_pass = i.options.getString("room_pass");
  const g = getGuild(i.guildId);
  for (const m of g.schedule || []) if (m.no === no) { m.room_id = room_id; m.room_pass = room_pass; }
  saveGuild(i.guildId, g);
  const e = new EmbedBuilder().setTitle(`🎮 IDP — Match #${no}`).setColor(ACCENT)
    .setDescription(`**Room ID:** \`${room_id}\`\n**Password:** \`${room_pass}\`\n\nAll teams be ready 5 minutes before slot time.`)
    .setFooter({ text: "BRN ESPORTS OFFICIAL BOT" });
  return i.reply({ embeds: [e] });
}

async function doSetPoints(i) {
  if (!isAdmin(i)) return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  const g = getGuild(i.guildId);
  const team = i.options.getString("team");
  const points = i.options.getInteger("points");
  const kills = i.options.getInteger("kills") || 0;
  const wins = i.options.getInteger("wins") || 0;
  let found = false;
  for (const p of g.points) if (p.team.toLowerCase() === team.toLowerCase()) { p.points = points; p.kills = kills; p.wins = wins; found = true; break; }
  if (!found) g.points.push({ team, points, kills, wins });
  saveGuild(i.guildId, g);
  return i.reply({ content: `✅ Updated points for **${team}**.`, ephemeral: true });
}

async function doAddPoints(i) {
  if (!isAdmin(i)) return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  const g = getGuild(i.guildId);
  const team = i.options.getString("team");
  const points = i.options.getInteger("points") || 0;
  const kills = i.options.getInteger("kills") || 0;
  const wins = i.options.getInteger("wins") || 0;
  let found = false;
  for (const p of g.points) if (p.team.toLowerCase() === team.toLowerCase()) { p.points += points; p.kills += kills; p.wins += wins; found = true; break; }
  if (!found) g.points.push({ team, points, kills, wins });
  saveGuild(i.guildId, g);
  return i.reply({ content: `✅ Added to **${team}**.`, ephemeral: true });
}

async function doResetPoints(i) {
  if (!isAdmin(i)) return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  const g = getGuild(i.guildId);
  g.points = [];
  saveGuild(i.guildId, g);
  return i.reply("✅ Point table reset.");
}

async function doPoints(i) {
  const g = getGuild(i.guildId);
  const pts = [...(g.points || [])].sort((a, b) => b.points - a.points || b.kills - a.kills);
  if (!pts.length) return i.reply({ content: "Point table is empty.", ephemeral: true });
  const header = "`" + "#".padEnd(3) + "TEAM".padEnd(22) + "PTS".padStart(5) + "KIL".padStart(5) + "WIN".padStart(5) + "`\n";
  const rows = pts.slice(0, 25).map((p, idx) => {
    const tname = p.team.length > 20 ? p.team.slice(0, 20) + ".." : p.team;
    return "`" + String(idx + 1).padEnd(3) + tname.padEnd(22) + String(p.points).padStart(5) + String(p.kills).padStart(5) + String(p.wins).padStart(5) + "`";
  });
  const e = new EmbedBuilder().setTitle(`🏅 ${g.tournament_name} — Point Table`).setColor(BRAND)
    .setDescription(header + rows.join("\n")).setFooter({ text: "BRN ESPORTS OFFICIAL BOT" });
  return i.reply({ embeds: [e] });
}

function buildModal(customId, title, fields) {
  const modal = new ModalBuilder().setCustomId(customId).setTitle(title);
  for (const f of fields) {
    const ti = new TextInputBuilder().setCustomId(f.id).setLabel(f.label).setStyle(f.style || TextInputStyle.Short).setRequired(f.required ?? true);
    if (f.placeholder) ti.setPlaceholder(f.placeholder);
    if (f.value) ti.setValue(f.value);
    if (f.maxLength) ti.setMaxLength(f.maxLength);
    if (f.required === false) ti.setRequired(false);
    modal.addComponents(new ActionRowBuilder().addComponents(ti));
  }
  return modal;
}

async function openAnnounceModal(i) {
  const ping = i.options.getBoolean("ping_everyone") || false;
  const img = i.options.getString("image_url") || "";
  const cid = `announce|${ping ? "1" : "0"}|${encodeURIComponent(img)}`;
  const modal = buildModal(cid, "📢 New Announcement", [
    { id: "title", label: "Title", maxLength: 200, placeholder: "Tournament Update" },
    { id: "body", label: "Message (Shift+Enter for new line)", style: TextInputStyle.Paragraph, maxLength: 3800, placeholder: "Type your announcement here..." },
  ]);
  return i.showModal(modal);
}

async function openDMCaptainsModal(i) {
  if (!isAdmin(i)) return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  const modal = buildModal("dmcaptains", "📨 DM All Captains", [
    { id: "title", label: "Title", value: "Tournament Notice", maxLength: 200 },
    { id: "body", label: "Message (Shift+Enter for new line)", style: TextInputStyle.Paragraph, maxLength: 3800 },
  ]);
  return i.showModal(modal);
}

async function openGreetModal(i) {
  if (!isAdmin(i)) return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  const img = i.options.getString("image_url") || "";
  const gif = i.options.getString("footer_gif") || "";
  const role = i.options.getRole("role");
  const cid = `greet|${encodeURIComponent(img)}|${encodeURIComponent(gif)}|${role ? role.id : ""}`;
  const modal = buildModal(cid, "👋 Greet Members (DM)", [
    { id: "title", label: "DM Title", value: "Welcome to BRN ESPORTS!", maxLength: 200 },
    { id: "body", label: "DM Message (Shift+Enter for new line)", style: TextInputStyle.Paragraph, maxLength: 3800,
      placeholder: "Hey {user}, welcome to our tournament server!" },
  ]);
  return i.showModal(modal);
}

async function openEmbedModal(i) {
  const c = encodeURIComponent(i.options.getString("color_hex") || "");
  const im = encodeURIComponent(i.options.getString("image_url") || "");
  const th = encodeURIComponent(i.options.getString("thumbnail_url") || "");
  const fi = encodeURIComponent(i.options.getString("footer_icon_url") || "");
  const cid = `embed|${c}|${im}|${th}|${fi}`;
  const modal = buildModal(cid, "✨ Custom Embed", [
    { id: "title", label: "Title", maxLength: 256, required: false },
    { id: "body", label: "Description (Shift+Enter for new line)", style: TextInputStyle.Paragraph, maxLength: 3800 },
    { id: "footer", label: "Footer text", maxLength: 200, value: "BRN ESPORTS OFFICIAL BOT", required: false },
  ]);
  return i.showModal(modal);
}

async function doPoll(i) {
  const q = i.options.getString("question");
  const opts = ["option1", "option2", "option3", "option4", "option5"]
    .map(k => i.options.getString(k)).filter(Boolean);
  const finalOpts = opts.length ? opts : ["Yes", "No"];
  const emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"];
  const desc = finalOpts.map((o, idx) => `${emojis[idx]}  ${o}`).join("\n");
  const e = new EmbedBuilder().setTitle(`📊 ${q}`).setDescription(desc).setColor(BRAND)
    .setFooter({ text: `Poll by ${i.user.tag} • BRN ESPORTS` });
  await i.reply({ embeds: [e] });
  const msg = await i.fetchReply();
  for (let idx = 0; idx < finalOpts.length; idx++) {
    try { await msg.react(emojis[idx]); } catch {}
  }
}

async function doServerInfo(i) {
  const g = i.guild;
  const e = new EmbedBuilder().setTitle(`🌐 ${g.name}`).setColor(BRAND)
    .addFields(
      { name: "Members", value: `\`${g.memberCount}\``, inline: true },
      { name: "Roles", value: `\`${g.roles.cache.size}\``, inline: true },
      { name: "Channels", value: `\`${g.channels.cache.size}\``, inline: true },
      { name: "Created", value: `<t:${Math.floor(g.createdTimestamp / 1000)}:R>`, inline: true },
      { name: "Owner", value: `<@${g.ownerId}>`, inline: true },
      { name: "Boosts", value: `\`${g.premiumSubscriptionCount || 0}\``, inline: true },
    ).setFooter({ text: "BRN ESPORTS OFFICIAL BOT" });
  if (g.iconURL()) e.setThumbnail(g.iconURL());
  return i.reply({ embeds: [e] });
}

async function doUserInfo(i) {
  const u = i.options.getMember("user") || i.member;
  const roles = u.roles.cache.filter(r => r.name !== "@everyone").map(r => `<@&${r.id}>`);
  const e = new EmbedBuilder().setTitle(`👤 ${u.user.tag}`).setColor(BRAND)
    .setThumbnail(u.user.displayAvatarURL())
    .addFields(
      { name: "ID", value: `\`${u.id}\`` },
      { name: "Joined Server", value: u.joinedTimestamp ? `<t:${Math.floor(u.joinedTimestamp / 1000)}:R>` : "?", inline: true },
      { name: "Account Created", value: `<t:${Math.floor(u.user.createdTimestamp / 1000)}:R>`, inline: true },
      { name: `Roles (${roles.length})`, value: roles.slice(0, 20).join(" ") || "—" },
    ).setFooter({ text: "BRN ESPORTS OFFICIAL BOT" });
  return i.reply({ embeds: [e] });
}

async function doAvatar(i) {
  const u = i.options.getUser("user") || i.user;
  const e = new EmbedBuilder().setTitle(`🖼️ ${u.username}'s Avatar`).setColor(BRAND).setImage(u.displayAvatarURL({ size: 1024 }));
  return i.reply({ embeds: [e] });
}

async function doSetWelcome(i) {
  if (!isAdmin(i)) return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  const ch = i.options.getChannel("channel");
  if (ch.type !== ChannelType.GuildText) return i.reply({ content: "Pick a text channel.", ephemeral: true });
  const g = getGuild(i.guildId);
  g.welcome = { channel_id: ch.id, message: i.options.getString("message"), image_url: i.options.getString("image_url") || "" };
  saveGuild(i.guildId, g);
  return i.reply({ content: `✅ Welcome channel set to ${ch}.`, ephemeral: true });
}

async function doWelcomeOff(i) {
  if (!isAdmin(i)) return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  const g = getGuild(i.guildId);
  delete g.welcome;
  saveGuild(i.guildId, g);
  return i.reply({ content: "✅ Auto-welcome disabled.", ephemeral: true });
}

async function doHelp(i) {
  const e = new EmbedBuilder().setTitle("🤖 BRN ESPORTS BOT — Command Guide").setColor(BRAND)
    .setDescription("Everything you need to run a tournament.")
    .addFields(
      { name: "🏆 Tournament", value: "`?t` — open the tournament panel\n`/info` `/settournamentname` `/setslots` `/setteamsize` `/endtournament`" },
      { name: "📋 Teams", value: "`/teamlist` • `/removeteam` • `/lineup`" },
      { name: "📅 Schedule & IDP", value: "`/addmatch` • `/removematch` • `/schedule` • `/idp`" },
      { name: "🏅 Point Table", value: "`/setpoints` • `/addpoints` • `/resetpoints` • `/points`" },
      { name: "📢 Communication", value: "`/announce` • `/dmcaptains` • `/greet` • `/sayembed` • `/poll`" },
      { name: "👋 Welcome System", value: "`/setwelcome` • `/welcomeoff`" },
      { name: "🔍 Info", value: "`/serverinfo` • `/userinfo` • `/avatar`" },
      { name: "🛡️ Moderation", value: "`/ban` • `/kick` • `/mute` • `/unmute` • `?purge <n|@user>`" },
      { name: "🎉 Giveaway", value: "`?gstart <time> <prize> <winners>winner`\nExample: `?gstart 10m Nitro 1winner`" },
    ).setFooter({ text: "BRN ESPORTS OFFICIAL BOT" });
  return i.reply({ embeds: [e], ephemeral: true });
}
