import { ChannelType, PermissionsBitField, EmbedBuilder } from "discord.js";
import { CHANNEL_NAMES, BRAND, ACCENT, REGISTRATION_FORMAT } from "../constants.js";

export const CATEGORY_NAME = "🏆 BRN ESPORTS";

const LOCKED_KEYWORDS = [
  "info", "updates", "rules", "how-to-register", "registration-format",
  "confirm-teams", "roadmaps", "schedule", "point-table",
];
const OPEN_KEYWORDS = ["registration", "query"];

const isLocked = (n) => LOCKED_KEYWORDS.some(k => n.includes(k));
const isOpen = (n) => OPEN_KEYWORDS.some(k => n.includes(k));

const VIEW = PermissionsBitField.Flags.ViewChannel;
const SEND = PermissionsBitField.Flags.SendMessages;
const HISTORY = PermissionsBitField.Flags.ReadMessageHistory;
const ADD_REACT = PermissionsBitField.Flags.AddReactions;

export function tournamentChannels(guild) {
  return [...guild.channels.cache.values()].filter(
    (c) => c.type === ChannelType.GuildText && CHANNEL_NAMES.includes(c.name)
  );
}

export async function ensureCategoryAndChannels(guild) {
  let category = guild.channels.cache.find(
    (c) => c.type === ChannelType.GuildCategory && c.name === CATEGORY_NAME
  );
  if (!category) {
    category = await guild.channels.create({ name: CATEGORY_NAME, type: ChannelType.GuildCategory });
  }
  const ids = { registration_channel_id: null, confirm_channel_id: null, format_channel_id: null };
  const channels = [];
  for (const name of CHANNEL_NAMES) {
    let ch = guild.channels.cache.find((c) => c.type === ChannelType.GuildText && c.name === name);
    if (!ch) {
      ch = await guild.channels.create({ name, type: ChannelType.GuildText, parent: category.id });
    }
    channels.push(ch);
    if (name.includes("registration-format")) ids.format_channel_id = ch.id;
    else if (name.includes("registration")) ids.registration_channel_id = ch.id;
    if (name.includes("confirm-teams")) ids.confirm_channel_id = ch.id;
  }
  return { category, channels, ids };
}

export async function applyRunningPerms(guild) {
  const everyone = guild.roles.everyone;
  for (const ch of tournamentChannels(guild)) {
    try {
      if (isOpen(ch.name)) {
        await ch.permissionOverwrites.edit(everyone, {
          ViewChannel: true, SendMessages: true, ReadMessageHistory: true, AddReactions: true,
        });
      } else if (isLocked(ch.name)) {
        await ch.permissionOverwrites.edit(everyone, {
          ViewChannel: true, SendMessages: false, ReadMessageHistory: true, AddReactions: false,
        });
      }
    } catch {}
  }
}

export async function applyPausedPerms(guild) {
  const everyone = guild.roles.everyone;
  for (const ch of tournamentChannels(guild)) {
    try {
      await ch.permissionOverwrites.edit(everyone, {
        ViewChannel: true, SendMessages: false, ReadMessageHistory: true, AddReactions: false,
      });
    } catch {}
  }
}

export async function postToAllTournamentChannels(guild, embed) {
  let sent = 0;
  for (const ch of tournamentChannels(guild)) {
    try { await ch.send({ embeds: [embed] }); sent++; } catch {}
  }
  return sent;
}

export async function postFormatMessage(guild) {
  const fch = guild.channels.cache.find(
    (c) => c.type === ChannelType.GuildText && c.name.includes("registration-format")
  );
  if (!fch) return;
  try {
    const recent = await fch.messages.fetch({ limit: 20 });
    if (recent.some((m) => m.author.id === guild.members.me.id && (m.content || "").includes("TEAM NAME"))) return;
  } catch {}
  const e = new EmbedBuilder()
    .setTitle("📋 Registration Format")
    .setDescription("Copy the format below, fill it in completely, and post it in the registration channel.")
    .setColor(BRAND).setFooter({ text: "BRN ESPORTS OFFICIAL BOT" });
  try {
    await fch.send({ embeds: [e] });
    await fch.send(REGISTRATION_FORMAT);
  } catch {}
}

export async function ensurePrivateSlotManagerChannel(guild) {
  let category = guild.channels.cache.find(
    (c) => c.type === ChannelType.GuildCategory && c.name === CATEGORY_NAME
  );
  if (!category) {
    category = await guild.channels.create({ name: CATEGORY_NAME, type: ChannelType.GuildCategory });
  }
  let ch = guild.channels.cache.find(
    (c) => c.type === ChannelType.GuildText && c.name === "slot-manager"
  );
  const overwrites = [
    { id: guild.roles.everyone.id, deny: [VIEW] },
    { id: guild.members.me.id, allow: [VIEW, SEND, HISTORY, PermissionsBitField.Flags.ManageMessages, PermissionsBitField.Flags.ManageChannels] },
  ];
  if (!ch) {
    ch = await guild.channels.create({
      name: "slot-manager", type: ChannelType.GuildText, parent: category.id,
      permissionOverwrites: overwrites, reason: "Private slot manager channel",
    });
  } else {
    try { await ch.permissionOverwrites.edit(guild.roles.everyone, { ViewChannel: false }); } catch {}
  }
  return ch;
}
