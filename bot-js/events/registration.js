import { EmbedBuilder } from "discord.js";
import { BRAND } from "../constants.js";
import { getGuild, saveGuild } from "../state.js";

export async function handleRegistration(msg) {
  const g = getGuild(msg.guild.id);
  if (!g.registration_channel_id || msg.channelId !== g.registration_channel_id) return;
  const text = msg.content || "";
  const teamName = matchField(text, ["TEAM NAME", "TEAM"]);
  if (!teamName) return;

  const players = [];
  const lines = text.split(/\r?\n/);
  let cur = null;
  for (const raw of lines) {
    const line = raw.trim();
    if (/^PLAYER\s*\d/i.test(line)) {
      if (cur) players.push(cur);
      cur = { tag: "" };
      const m = /:\s*(.+)$/.exec(line);
      if (m) cur.tag = m[1].trim();
    } else if (cur && /^CHARACTER ID/i.test(line)) {
      const m = /:\s*(.+)$/.exec(line);
      if (m) cur.id = m[1].trim();
    } else if (cur && /^DISCORD TAG/i.test(line)) {
      const m = /:\s*(.+)$/.exec(line);
      if (m) cur.discord = m[1].trim();
    }
  }
  if (cur) players.push(cur);

  const required = g.team_size || 5;
  const valid = players.filter(p => (p.tag || p.id || p.discord)).length;
  if (valid < required) {
    try { await msg.react("⚠️"); } catch {}
    return;
  }

  if (g.teams.length >= g.max_slots) {
    try { await msg.react("❌"); } catch {}
    return;
  }
  if (g.teams.some(t => t.name.toLowerCase() === teamName.toLowerCase())) {
    try { await msg.react("⚠️"); } catch {}
    return;
  }

  g.teams.push({
    name: teamName,
    captain_id: msg.author.id,
    players: players.slice(0, required),
    registered_at: Date.now(),
  });
  saveGuild(msg.guild.id, g);
  try { await msg.react("✅"); } catch {}

  if (g.confirm_channel_id) {
    try {
      const ch = await msg.guild.channels.fetch(g.confirm_channel_id);
      const e = new EmbedBuilder().setTitle("✅ Team Confirmed").setColor(BRAND).setDescription(
        `**${teamName}**\n**Slot:** \`${g.teams.length}/${g.max_slots}\`\n**Captain:** <@${msg.author.id}>`
      ).setFooter({ text: "BRN ESPORTS OFFICIAL BOT" });
      await ch.send({ embeds: [e] });
    } catch {}
  }
}

function matchField(text, names) {
  for (const n of names) {
    const r = new RegExp(`^\\s*${n}\\s*[:\\-]\\s*(.+)$`, "im");
    const m = r.exec(text);
    if (m) return m[1].trim();
  }
  return null;
}
