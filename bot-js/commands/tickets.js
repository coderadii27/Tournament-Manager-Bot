import {
  EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle,
  ChannelType, PermissionFlagsBits, PermissionsBitField,
} from "discord.js";
import { BRAND, ACCENT } from "../constants.js";
import { getGuild, saveGuild } from "../state.js";

export function ensureTicketState(g) {
  g.ticket ??= { staff_role_id: null, category_id: null, counter: 0, panel_channel_id: null };
  return g.ticket;
}

export function panelEmbed() {
  return new EmbedBuilder()
    .setAuthor({ name: "BERNICS ESPORTS • Support" })
    .setTitle("🎫  Need Help? Open a Ticket")
    .setDescription(
      "Welcome to support! Click the button below to open a **private ticket** with our staff team.\n\n" +
      "**How it works**\n" +
      "› A private channel is created just for you\n" +
      "› Only you and staff can see it\n" +
      "› Describe your issue and we'll help ASAP\n" +
      "› Close the ticket when you're done\n\n" +
      "*Please don't open a ticket without a real reason — abuse may result in action.*"
    )
    .setColor(BRAND)
    .setTimestamp(new Date())
    .setFooter({ text: "Powered by your friendly support team" });
}

export function panelRow() {
  return new ActionRowBuilder().addComponents(
    new ButtonBuilder().setCustomId("ticket:open").setLabel("Open Ticket").setEmoji("🎫").setStyle(ButtonStyle.Success),
  );
}

export function controlRow() {
  return new ActionRowBuilder().addComponents(
    new ButtonBuilder().setCustomId("ticket:claim").setLabel("Claim").setEmoji("🙋").setStyle(ButtonStyle.Primary),
    new ButtonBuilder().setCustomId("ticket:close").setLabel("Close").setEmoji("🔒").setStyle(ButtonStyle.Danger),
  );
}

function welcomeEmbed(member, ticketNo) {
  return new EmbedBuilder()
    .setAuthor({ name: "BERNICS ESPORTS • Support" })
    .setTitle(`🎫 Ticket #${String(ticketNo).padStart(4, "0")}`)
    .setDescription(
      `Hello ${member}, thanks for opening a ticket!\n\n` +
      "› Please describe your issue with as much detail as possible.\n" +
      "› A staff member will be with you shortly.\n" +
      "› Use **Claim** to take ownership (staff only) or **Close** when done."
    )
    .setColor(ACCENT)
    .setTimestamp(new Date())
    .addFields(
      { name: "Status", value: "🟢 Open • Unclaimed", inline: true },
      { name: "Opened by", value: `${member}`, inline: true },
    )
    .setFooter({ text: "Powered by your friendly support team" });
}

export async function ticketSetupCommand(i) {
  if (!i.memberPermissions?.has(PermissionFlagsBits.ManageGuild)) {
    return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  }
  const staff = i.options.getRole("staff_role");
  const cat = i.options.getChannel("category");
  const ch = i.options.getChannel("channel") || i.channel;
  const g = getGuild(i.guildId);
  const ts = ensureTicketState(g);
  if (staff) ts.staff_role_id = staff.id;
  if (cat) ts.category_id = cat.id;
  ts.panel_channel_id = ch.id;
  saveGuild(i.guildId, g);
  await ch.send({ embeds: [panelEmbed()], components: [panelRow()] });
  return i.reply({
    content: `✅ Ticket panel posted in <#${ch.id}>.` +
      (staff ? `\nStaff role: <@&${staff.id}>` : "") +
      (cat ? `\nCategory: **${cat.name}**` : ""),
    ephemeral: true,
    allowedMentions: { parse: [] },
  });
}

export async function ticketPanelCommand(i) {
  if (!i.memberPermissions?.has(PermissionFlagsBits.ManageGuild)) {
    return i.reply({ content: "Manage Server permission required.", ephemeral: true });
  }
  await i.channel.send({ embeds: [panelEmbed()], components: [panelRow()] });
  return i.reply({ content: "✅ Panel posted.", ephemeral: true });
}

export async function ticketCloseCommand(i) {
  if (i.channel?.type !== ChannelType.GuildText) {
    return i.reply({ content: "Use this inside a ticket.", ephemeral: true });
  }
  const topic = i.channel.topic || "";
  if (!topic.includes("ticket-user:")) {
    return i.reply({ content: "This is not a ticket channel.", ephemeral: true });
  }
  await i.reply({ content: "🔒 Closing in 5 seconds…" });
  setTimeout(() => i.channel.delete(`Ticket closed via /ticketclose by ${i.user.tag}`).catch(() => {}), 5000);
}

function isStaff(member, staffRoleId) {
  if (member.permissions.has(PermissionFlagsBits.ManageChannels)) return true;
  if (staffRoleId && member.roles.cache.has(staffRoleId)) return true;
  return false;
}

export async function handleTicketButton(i, action) {
  const g = getGuild(i.guildId);
  const ts = ensureTicketState(g);

  if (action === "open") {
    await i.deferReply({ ephemeral: true });
    // Prevent duplicates
    const existing = i.guild.channels.cache.find(
      c => c.type === ChannelType.GuildText && (c.topic || "").includes(`ticket-user:${i.user.id}`)
    );
    if (existing) {
      return i.editReply({ content: `You already have an open ticket: <#${existing.id}>` });
    }

    let category = ts.category_id ? i.guild.channels.cache.get(ts.category_id) : null;
    if (!category || category.type !== ChannelType.GuildCategory) {
      category = await i.guild.channels.create({ name: "🎫 Tickets", type: ChannelType.GuildCategory });
      ts.category_id = category.id;
    }

    const staffRole = ts.staff_role_id ? i.guild.roles.cache.get(ts.staff_role_id) : null;

    ts.counter = (ts.counter || 0) + 1;
    const ticketNo = ts.counter;
    saveGuild(i.guildId, g);

    const overwrites = [
      { id: i.guild.roles.everyone.id, deny: [PermissionsBitField.Flags.ViewChannel] },
      {
        id: i.user.id,
        allow: [
          PermissionsBitField.Flags.ViewChannel,
          PermissionsBitField.Flags.SendMessages,
          PermissionsBitField.Flags.ReadMessageHistory,
          PermissionsBitField.Flags.AttachFiles,
          PermissionsBitField.Flags.EmbedLinks,
        ],
      },
      {
        id: i.client.user.id,
        allow: [
          PermissionsBitField.Flags.ViewChannel,
          PermissionsBitField.Flags.SendMessages,
          PermissionsBitField.Flags.ManageChannels,
          PermissionsBitField.Flags.ManageMessages,
        ],
      },
    ];
    if (staffRole) {
      overwrites.push({
        id: staffRole.id,
        allow: [
          PermissionsBitField.Flags.ViewChannel,
          PermissionsBitField.Flags.SendMessages,
          PermissionsBitField.Flags.ReadMessageHistory,
          PermissionsBitField.Flags.ManageMessages,
        ],
      });
    }

    let channel;
    try {
      channel = await i.guild.channels.create({
        name: `ticket-${String(ticketNo).padStart(4, "0")}-${i.user.username}`.slice(0, 90),
        type: ChannelType.GuildText,
        parent: category.id,
        permissionOverwrites: overwrites,
        topic: `ticket-user:${i.user.id} • Opened by ${i.user.tag}`,
        reason: `Ticket opened by ${i.user.tag}`,
      });
    } catch {
      return i.editReply({ content: "I don't have permission to create channels here." });
    }

    await channel.send({
      content: `${i.user}${staffRole ? ` <@&${staffRole.id}>` : ""}`,
      embeds: [welcomeEmbed(i.user, ticketNo)],
      components: [controlRow()],
      allowedMentions: { users: [i.user.id], roles: staffRole ? [staffRole.id] : [] },
    });
    return i.editReply({ content: `✅ Your ticket has been created: <#${channel.id}>` });
  }

  if (action === "claim") {
    if (!isStaff(i.member, ts.staff_role_id)) {
      return i.reply({ content: "Only staff can claim tickets.", ephemeral: true });
    }
    try {
      const messages = await i.channel.messages.fetch({ limit: 10, after: "0" });
      const first = [...messages.values()].reverse().find(m => m.author.id === i.client.user.id && m.embeds.length);
      if (first) {
        const e = EmbedBuilder.from(first.embeds[0]).spliceFields(0, 1,
          { name: "Status", value: `🟡 Open • Claimed by ${i.user}`, inline: true }
        );
        await first.edit({ embeds: [e] });
      }
    } catch {}
    return i.reply({ content: `🙋 ${i.user} has claimed this ticket.`, allowedMentions: { parse: [] } });
  }

  if (action === "close") {
    const topic = i.channel.topic || "";
    const isOwner = topic.includes(`ticket-user:${i.user.id}`);
    if (!isOwner && !isStaff(i.member, ts.staff_role_id)) {
      return i.reply({ content: "Only the ticket opener or staff can close this ticket.", ephemeral: true });
    }
    const e = new EmbedBuilder().setTitle("🔒 Closing Ticket").setColor(0xe74c3c)
      .setDescription(`This ticket will be deleted in **5 seconds**.\nClosed by ${i.user}.`);
    await i.reply({ embeds: [e] });
    setTimeout(() => i.channel.delete(`Ticket closed by ${i.user.tag}`).catch(() => {}), 5000);
  }
}
