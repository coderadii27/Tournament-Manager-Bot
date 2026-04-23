import { EmbedBuilder } from "discord.js";
import { getAllGiveaways, setGiveaway, removeGiveaway } from "../state.js";
import { giveawayEmbed } from "../commands/prefix.js";

export function startGiveawayLoop(client) {
  setInterval(() => tick(client).catch(() => {}), 5000);
}

async function tick(client) {
  const all = getAllGiveaways();
  const now = Math.floor(Date.now() / 1000);
  for (const [msgId, ga] of Object.entries(all)) {
    if (ga.ended) continue;
    if (now < ga.end_ts) continue;
    try {
      const ch = await client.channels.fetch(ga.channel_id);
      const m = await ch.messages.fetch(msgId);
      const pool = [...new Set(ga.entrants)];
      const winners = [];
      while (winners.length < ga.winners && pool.length) {
        const idx = Math.floor(Math.random() * pool.length);
        winners.push(pool.splice(idx, 1)[0]);
      }
      const e = giveawayEmbed(ga.prize, ga.winners, ga.end_ts, ga.host_id, ga.entrants.length, true, winners);
      await m.edit({ embeds: [e], components: [] });
      if (winners.length) {
        await ch.send({ content: `🎉 Congrats ${winners.map(w => `<@${w}>`).join(", ")}! You won **${ga.prize}**!` });
      } else {
        await ch.send({ content: `😔 No valid entries for **${ga.prize}**.` });
      }
      ga.ended = true;
      setGiveaway(msgId, ga);
      setTimeout(() => removeGiveaway(msgId), 10 * 60 * 1000);
    } catch {
      removeGiveaway(msgId);
    }
  }
}
