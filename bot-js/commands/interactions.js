import {
  EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, ModalBuilder, TextInputBuilder, TextInputStyle,
  ChannelType, PermissionFlagsBits,
} from "discord.js";
import { BRAND, ACCENT, CHANNEL_NAMES, REGISTRATION_FORMAT } from "../constants.js";
import { getGuild, saveGuild, setGiveaway, getAllGiveaways } from "../state.js";
import { giveawayEmbed } from "./prefix.js";
import { handleTicketButton } from "./tickets.js";

export async function handleInteraction(i) {
  if (i.isButton()) return handleButton(i);
  if (i.isModalSubmit()) return handleModal(i);
}

async function handleButton(i) {
  const id = i.customId;
  if (id.startsWith("t:")) return tournamentButton(i, id.slice(2));
  if (id.startsWith("sm:")) return slotManagerButton(i, id.slice(3));
  if (id === "ga:join") return giveawayJoin(i);
  if (id.startsWith("ticket:")) return handleTicketButton(i, id.slice(7));
}

async function tournamentButton(i, action) {
  if (!i.memberPermissions?.has(PermissionFlagsBits.ManageGuild)) {
    return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  }
  const g = getGuild(i.guildId);

  if (action === "create") {
    const modal = new ModalBuilder().setCustomId("t:create_modal").setTitle("🛠️ Create Tournament")
      .addComponents(
        new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId("name").setLabel("Tournament Name").setStyle(TextInputStyle.Short).setRequired(true).setValue(g.tournament_name).setMaxLength(64)),
        new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId("size").setLabel("Team Size (players per team)").setStyle(TextInputStyle.Short).setValue(String(g.team_size)).setMaxLength(2)),
        new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId("slots").setLabel("Total Slots").setStyle(TextInputStyle.Short).setValue(String(g.max_slots)).setMaxLength(3)),
      );
    return i.showModal(modal);
  }

  if (action === "channels") {
    await i.deferReply({ ephemeral: true });
    const cat = await i.guild.channels.create({
      name: `🏆 ${g.tournament_name}`, type: ChannelType.GuildCategory,
    });
    const created = [];
    let regCh = null, confirmCh = null, formatCh = null;
    for (const name of CHANNEL_NAMES) {
      const ch = await i.guild.channels.create({ name, type: ChannelType.GuildText, parent: cat.id });
      created.push(ch);
      if (name.includes("registration-format")) formatCh = ch;
      else if (name.includes("registration") && !regCh) regCh = ch;
      if (name.includes("confirm-teams")) confirmCh = ch;
    }
    g.registration_channel_id = regCh?.id || null;
    g.confirm_channel_id = confirmCh?.id || null;
    saveGuild(i.guildId, g);
    if (formatCh) {
      const e = new EmbedBuilder().setTitle("📝 Registration Format").setColor(ACCENT)
        .setDescription(`Copy this format, fill it, and post it in <#${regCh?.id}>.\n\n${REGISTRATION_FORMAT}`)
        .setFooter({ text: "BRN ESPORTS OFFICIAL BOT" });
      await formatCh.send({ embeds: [e] });
    }
    return i.editReply(`✅ Created **${created.length}** channels under **${cat.name}**.`);
  }

  if (action === "start") {
    g.running = true; g.paused = false; saveGuild(i.guildId, g);
    return i.reply({ content: "▶️ Tournament started.", ephemeral: true });
  }

  if (action === "pause") {
    g.paused = !g.paused; saveGuild(i.guildId, g);
    return i.reply({ content: g.paused ? "⏸️ Tournament paused." : "▶️ Tournament resumed.", ephemeral: true });
  }

  if (action === "groups") {
    const modal = new ModalBuilder().setCustomId("t:groups_modal").setTitle("📊 Manage Groups")
      .addComponents(
        new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId("count").setLabel("Number of groups").setStyle(TextInputStyle.Short).setValue("4").setMaxLength(2)),
        new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId("per").setLabel("Teams per group (auto-fill)").setStyle(TextInputStyle.Short).setValue("4").setMaxLength(2)),
      );
    return i.showModal(modal);
  }

  if (action === "slots") {
    const e = new EmbedBuilder().setTitle("🎟️ Slot Manager").setColor(ACCENT)
      .setDescription(`Slots: **${g.teams.length}/${g.max_slots}**\nUse the buttons below.`);
    const row = new ActionRowBuilder().addComponents(
      new ButtonBuilder().setCustomId("sm:list").setLabel("List Slots").setStyle(ButtonStyle.Primary),
      new ButtonBuilder().setCustomId("sm:cancel").setLabel("Cancel a Slot").setStyle(ButtonStyle.Danger),
      new ButtonBuilder().setCustomId("sm:reset").setLabel("Reset All").setStyle(ButtonStyle.Secondary),
    );
    return i.reply({ embeds: [e], components: [row], ephemeral: true });
  }
}

async function slotManagerButton(i, action) {
  if (!i.memberPermissions?.has(PermissionFlagsBits.ManageGuild)) {
    return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  }
  const g = getGuild(i.guildId);
  if (action === "list") {
    if (!g.teams.length) return i.reply({ content: "No teams yet.", ephemeral: true });
    const desc = g.teams.map((t, idx) => `**Slot ${idx + 1}** — ${t.name} (<@${t.captain_id}>)`).join("\n").slice(0, 3800);
    return i.reply({ embeds: [new EmbedBuilder().setTitle("Slots").setDescription(desc).setColor(BRAND)], ephemeral: true });
  }
  if (action === "cancel") {
    const modal = new ModalBuilder().setCustomId("sm:cancel_modal").setTitle("Cancel a Slot")
      .addComponents(new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId("slot").setLabel("Slot number to cancel").setStyle(TextInputStyle.Short).setRequired(true)));
    return i.showModal(modal);
  }
  if (action === "reset") {
    g.teams = []; saveGuild(i.guildId, g);
    return i.reply({ content: "✅ All slots cleared.", ephemeral: true });
  }
}

async function giveawayJoin(i) {
  const all = getAllGiveaways();
  const ga = all[i.message.id];
  if (!ga || ga.ended) return i.reply({ content: "This giveaway has ended.", ephemeral: true });
  if (ga.entrants.includes(i.user.id)) {
    ga.entrants = ga.entrants.filter(x => x !== i.user.id);
    setGiveaway(i.message.id, ga);
    await refreshGiveaway(i.client, ga, i.message.id);
    return i.reply({ content: "You've left the giveaway.", ephemeral: true });
  }
  ga.entrants.push(i.user.id);
  setGiveaway(i.message.id, ga);
  await refreshGiveaway(i.client, ga, i.message.id);
  return i.reply({ content: "🎉 You're in! Good luck!", ephemeral: true });
}

async function refreshGiveaway(client, ga, msgId) {
  try {
    const ch = await client.channels.fetch(ga.channel_id);
    const m = await ch.messages.fetch(msgId);
    await m.edit({ embeds: [giveawayEmbed(ga.prize, ga.winners, ga.end_ts, ga.host_id, ga.entrants.length)] });
  } catch {}
}

async function handleModal(i) {
  const id = i.customId;

  if (id === "t:create_modal") {
    const g = getGuild(i.guildId);
    g.tournament_name = i.fields.getTextInputValue("name").slice(0, 64) || g.tournament_name;
    const size = parseInt(i.fields.getTextInputValue("size"), 10);
    const slots = parseInt(i.fields.getTextInputValue("slots"), 10);
    if (Number.isFinite(size) && size > 0 && size <= 10) g.team_size = size;
    if (Number.isFinite(slots) && slots > 0 && slots <= 256) g.max_slots = slots;
    saveGuild(i.guildId, g);
    return i.reply({ content: `✅ **${g.tournament_name}** configured: ${g.team_size} per team, ${g.max_slots} slots.`, ephemeral: true });
  }

  if (id === "t:groups_modal") {
    const g = getGuild(i.guildId);
    const count = Math.max(1, Math.min(16, parseInt(i.fields.getTextInputValue("count"), 10) || 0));
    const per = Math.max(1, Math.min(20, parseInt(i.fields.getTextInputValue("per"), 10) || 0));
    g.groups = {};
    let idx = 0;
    for (let k = 0; k < count; k++) {
      const label = String.fromCharCode(65 + k);
      g.groups[label] = g.teams.slice(idx, idx + per).map(t => t.name);
      idx += per;
    }
    saveGuild(i.guildId, g);
    return i.reply({ content: `✅ Created **${count}** groups (${per} teams each).`, ephemeral: true });
  }

  if (id === "sm:cancel_modal") {
    const slot = parseInt(i.fields.getTextInputValue("slot"), 10);
    const g = getGuild(i.guildId);
    if (!Number.isFinite(slot) || slot < 1 || slot > g.teams.length) {
      return i.reply({ content: "Invalid slot number.", ephemeral: true });
    }
    const removed = g.teams.splice(slot - 1, 1)[0];
    saveGuild(i.guildId, g);
    return i.reply({ content: `✅ Cancelled slot **${slot}** (${removed.name}).`, ephemeral: true });
  }

  if (id.startsWith("announce|")) return submitAnnounce(i);
  if (id === "dmcaptains") return submitDMCaptains(i);
  if (id.startsWith("greet|")) return submitGreet(i);
  if (id.startsWith("embed|")) return submitEmbed(i);
}

async function submitAnnounce(i) {
  const [, ping, imgEnc] = i.customId.split("|");
  const img = decodeURIComponent(imgEnc || "");
  const title = i.fields.getTextInputValue("title");
  const body = i.fields.getTextInputValue("body");
  const e = new EmbedBuilder().setTitle(`📢 ${title}`).setDescription(body).setColor(BRAND).setFooter({ text: "BRN ESPORTS OFFICIAL BOT" });
  if (img) e.setImage(img);
  const content = ping === "1" ? "@everyone" : null;
  await i.reply({ content, embeds: [e], allowedMentions: ping === "1" ? { parse: ["everyone"] } : undefined });
}

async function submitDMCaptains(i) {
  await i.deferReply({ ephemeral: true });
  const title = i.fields.getTextInputValue("title");
  const body = i.fields.getTextInputValue("body");
  const g = getGuild(i.guildId);
  const e = new EmbedBuilder().setTitle(`📨 ${title}`).setDescription(body).setColor(BRAND)
    .setFooter({ text: `From ${i.guild.name} • BRN ESPORTS OFFICIAL BOT` });
  let ok = 0, fail = 0;
  for (const t of g.teams) {
    try { const u = await i.client.users.fetch(t.captain_id); await u.send({ embeds: [e] }); ok++; }
    catch { fail++; }
  }
  return i.editReply(`✅ Sent: **${ok}** • ❌ Failed: **${fail}**`);
}

async function submitGreet(i) {
  await i.deferReply({ ephemeral: true });
  const [, imgEnc, gifEnc, roleId] = i.customId.split("|");
  const img = decodeURIComponent(imgEnc || "");
  const gif = decodeURIComponent(gifEnc || "");
  const title = i.fields.getTextInputValue("title");
  const bodyTpl = i.fields.getTextInputValue("body");

  const members = await i.guild.members.fetch();
  let targets = [...members.values()].filter(m => !m.user.bot);
  if (roleId) targets = targets.filter(m => m.roles.cache.has(roleId));

  let ok = 0, fail = 0;
  for (const m of targets) {
    const body = bodyTpl
      .replaceAll("{user}", `<@${m.id}>`)
      .replaceAll("{name}", m.user.username)
      .replaceAll("{server}", i.guild.name);
    const e = new EmbedBuilder().setTitle(title).setDescription(body).setColor(BRAND);
    if (img) e.setImage(img);
    if (gif) e.setFooter({ text: "BRN ESPORTS OFFICIAL BOT", iconURL: gif });
    else e.setFooter({ text: "BRN ESPORTS OFFICIAL BOT" });
    try { await m.send({ embeds: [e] }); ok++; }
    catch { fail++; }
  }
  return i.editReply(`✅ DMs sent: **${ok}** • ❌ Failed: **${fail}**`);
}

async function submitEmbed(i) {
  const [, cEnc, imEnc, thEnc, fiEnc] = i.customId.split("|");
  const colorHex = decodeURIComponent(cEnc || "");
  const img = decodeURIComponent(imEnc || "");
  const thumb = decodeURIComponent(thEnc || "");
  const ficon = decodeURIComponent(fiEnc || "");
  const title = i.fields.getTextInputValue("title");
  const body = i.fields.getTextInputValue("body");
  const footer = i.fields.getTextInputValue("footer") || "BRN ESPORTS OFFICIAL BOT";
  let color = BRAND;
  if (colorHex) {
    const v = parseInt(colorHex.replace("#", ""), 16);
    if (Number.isFinite(v)) color = v;
  }
  const e = new EmbedBuilder().setColor(color).setDescription(body);
  if (title) e.setTitle(title);
  if (img) e.setImage(img);
  if (thumb) e.setThumbnail(thumb);
  if (ficon) e.setFooter({ text: footer, iconURL: ficon }); else e.setFooter({ text: footer });
  await i.reply({ embeds: [e] });
}
