import { EmbedBuilder } from "discord.js";
import { BRAND } from "../constants.js";
import { getGuild } from "../state.js";

export async function handleMemberJoin(member) {
  const g = getGuild(member.guild.id);
  if (!g.welcome?.channel_id) return;
  try {
    const ch = await member.guild.channels.fetch(g.welcome.channel_id);
    const body = (g.welcome.message || "Welcome {user} to {server}!")
      .replaceAll("{user}", `<@${member.id}>`)
      .replaceAll("{name}", member.user.username)
      .replaceAll("{server}", member.guild.name);
    const e = new EmbedBuilder().setTitle(`👋 Welcome!`).setDescription(body).setColor(BRAND)
      .setThumbnail(member.user.displayAvatarURL()).setFooter({ text: "BRN ESPORTS OFFICIAL BOT" });
    if (g.welcome.image_url) e.setImage(g.welcome.image_url);
    await ch.send({ content: `<@${member.id}>`, embeds: [e] });
  } catch {}
}
