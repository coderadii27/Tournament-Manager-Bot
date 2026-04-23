import {
  EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, PermissionFlagsBits,
} from "discord.js";
import { BRAND, ACCENT, parseDurationSec, parseWinners } from "../constants.js";
import { getGuild } from "../state.js";
import { setGiveaway } from "../state.js";

function panelEmbed(g) {
  const status = g.running && !g.paused ? "🟢 Running" : g.paused ? "🟡 Paused" : "⚪ Idle";
  return new EmbedBuilder()
    .setTitle("🏆 BRN ESPORTS — Tournament Control Panel")
    .setDescription("Welcome to the **official tournament hub**.\nUse the buttons below to manage every part of your event.\n\u200b")
    .setColor(BRAND)
    .addFields(
      { name: "Tournament", value: `\`${g.tournament_name}\``, inline: true },
      { name: "Slots", value: `\`${g.teams.length}/${g.max_slots}\``, inline: true },
      { name: "Team Size", value: `\`${g.team_size} players\``, inline: true },
      { name: "Status", value: status, inline: true },
      { name: "Groups", value: `\`${Object.keys(g.groups || {}).length}\``, inline: true },
      { name: "\u200b", value: "\u200b", inline: true },
    ).setFooter({ text: "BRN ESPORTS OFFICIAL BOT" });
}

function panelView() {
  const row1 = new ActionRowBuilder().addComponents(
    new ButtonBuilder().setCustomId("t:create").setLabel("Create Tournament").setEmoji("🛠️").setStyle(ButtonStyle.Success),
    new ButtonBuilder().setCustomId("t:channels").setLabel("Create Channels").setEmoji("📂").setStyle(ButtonStyle.Primary),
  );
  const row2 = new ActionRowBuilder().addComponents(
    new ButtonBuilder().setCustomId("t:start").setLabel("Start Tournament").setEmoji("▶️").setStyle(ButtonStyle.Success),
    new ButtonBuilder().setCustomId("t:pause").setLabel("Pause Tournament").setEmoji("⏸️").setStyle(ButtonStyle.Secondary),
  );
  const row3 = new ActionRowBuilder().addComponents(
    new ButtonBuilder().setCustomId("t:groups").setLabel("Manage Groups").setEmoji("📊").setStyle(ButtonStyle.Primary),
    new ButtonBuilder().setCustomId("t:slots").setLabel("Slot Manager").setEmoji("🎟️").setStyle(ButtonStyle.Danger),
  );
  return [row1, row2, row3];
}

export async function handlePrefix(msg) {
  const [cmd, ...args] = msg.content.slice(1).trim().split(/\s+/);
  const c = (cmd || "").toLowerCase();

  if (c === "t") {
    const g = getGuild(msg.guild.id);
    return msg.channel.send({ embeds: [panelEmbed(g)], components: panelView() });
  }

  if (c === "purge") return doPurge(msg, args);

  if (c === "gstart") return doGstart(msg, args);
}

async function doPurge(msg, args) {
  if (!msg.member.permissions.has(PermissionFlagsBits.ManageMessages)) {
    return msg.reply("You need **Manage Messages** permission.");
  }
  if (!args.length) return msg.reply("Usage: `?purge <1-100>` or `?purge @user`");

  try { await msg.delete(); } catch {}

  const mention = msg.mentions.users.first();
  if (mention) {
    const fetched = await msg.channel.messages.fetch({ limit: 100 });
    const toDel = fetched.filter(m => m.author.id === mention.id).first(100);
    const deleted = await msg.channel.bulkDelete(toDel, true);
    const e = new EmbedBuilder().setTitle("🧹 Purged").setColor(BRAND)
      .setDescription(`Deleted **${deleted.size}** messages from <@${mention.id}>.`);
    const reply = await msg.channel.send({ embeds: [e] });
    setTimeout(() => reply.delete().catch(() => {}), 5000);
    return;
  }

  const n = parseInt(args[0], 10);
  if (!Number.isFinite(n) || n < 1 || n > 100) {
    const r = await msg.channel.send("Provide a number 1-100 or mention a user.");
    setTimeout(() => r.delete().catch(() => {}), 5000);
    return;
  }
  const deleted = await msg.channel.bulkDelete(n, true);
  const e = new EmbedBuilder().setTitle("🧹 Purged").setColor(BRAND).setDescription(`Deleted **${deleted.size}** messages.`);
  const reply = await msg.channel.send({ embeds: [e] });
  setTimeout(() => reply.delete().catch(() => {}), 5000);
}

async function doGstart(msg, args) {
  if (!msg.member.permissions.has(PermissionFlagsBits.ManageGuild)) {
    return msg.reply("You need **Manage Server** permission.");
  }
  if (args.length < 2) return msg.reply("Usage: `?gstart <time> <prize> <winners>winner` — e.g. `?gstart 10m Nitro 1winner`");
  const duration = args[0];
  const winnersToken = args[args.length - 1];
  const w = parseWinners(winnersToken);
  let prize, winnersCount;
  if (w !== null && /[a-zA-Z]/.test(winnersToken)) {
    prize = args.slice(1, -1).join(" ");
    winnersCount = w;
  } else {
    prize = args.slice(1).join(" ");
    winnersCount = 1;
  }
  if (!prize) return msg.reply("Please provide a prize.");
  const secs = parseDurationSec(duration);
  if (!secs || secs <= 0) return msg.reply("Invalid time. Use `10s`, `5m`, `2h`, `1d`.");

  const endTs = Math.floor(Date.now() / 1000) + secs;
  const e = giveawayEmbed(prize, winnersCount, endTs, msg.author.id, 0);
  const row = new ActionRowBuilder().addComponents(
    new ButtonBuilder().setCustomId("ga:join").setLabel("Join Giveaway").setEmoji("🎉").setStyle(ButtonStyle.Success),
  );
  const sent = await msg.channel.send({ embeds: [e], components: [row] });
  setGiveaway(sent.id, {
    channel_id: msg.channel.id, guild_id: msg.guild.id, host_id: msg.author.id,
    prize, winners: winnersCount, end_ts: endTs, entrants: [], ended: false,
  });
  try { await msg.delete(); } catch {}
}

export function giveawayEmbed(prize, winners, endTs, hostId, entrants, ended = false, winnerIds = []) {
  if (ended) {
    let desc = `**Prize:** ${prize}\n**Ended** <t:${endTs}:R>\n`;
    desc += winnerIds.length ? `**Winners:** ${winnerIds.map(w => `<@${w}>`).join(", ")}` : "**No valid entries.**";
    return new EmbedBuilder().setTitle("🎉 Giveaway Ended").setDescription(desc).setColor(0x95a5a6)
      .setFooter({ text: `Hosted by user ${hostId} • BRN ESPORTS OFFICIAL BOT` });
  }
  return new EmbedBuilder().setTitle("🎉 GIVEAWAY 🎉").setColor(BRAND).setDescription(
    `**Prize:** ${prize}\n**Winners:** ${winners}\n**Ends:** <t:${endTs}:R> (<t:${endTs}:f>)\n**Entries:** ${entrants}\n\nClick the button below to enter!`
  ).setFooter({ text: `Hosted by user ${hostId} • BRN ESPORTS OFFICIAL BOT` });
}
