import { Client, GatewayIntentBits, Partials, ActivityType, Events, REST, Routes } from "discord.js";
import { handleSlash } from "./commands/slash.js";
import { handlePrefix } from "./commands/prefix.js";
import { handleInteraction } from "./commands/interactions.js";
import { handleRegistration } from "./events/registration.js";
import { startGiveawayLoop } from "./events/giveaway.js";
import { handleMemberJoin } from "./events/welcome.js";
import { buildSlashDefinitions } from "./commands/definitions.js";

const TOKEN = process.env.DISCORD_BOT_TOKEN;
if (!TOKEN) {
  console.error("DISCORD_BOT_TOKEN environment variable is not set.");
  process.exit(1);
}

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMembers,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildMessageReactions,
  ],
  partials: [Partials.Message, Partials.Channel, Partials.Reaction],
});

client.once(Events.ClientReady, async (c) => {
  console.log(`Logged in as ${c.user.tag} (id=${c.user.id})`);
  c.user.setPresence({
    status: "dnd",
    activities: [{ name: "Organising Tournaments in BRN ESPORTS", type: ActivityType.Playing }],
  });

  const rest = new REST({ version: "10" }).setToken(TOKEN);
  const defs = buildSlashDefinitions();
  let total = 0;
  for (const guild of c.guilds.cache.values()) {
    try {
      const data = await rest.put(Routes.applicationGuildCommands(c.user.id, guild.id), { body: defs });
      total += data.length;
      console.log(`Synced ${data.length} commands to guild ${guild.name}`);
    } catch (e) {
      console.error(`Sync failed for ${guild.name}:`, e?.message || e);
    }
  }
  console.log(`Total per-guild commands synced: ${total}`);
  startGiveawayLoop(c);
});

client.on(Events.GuildCreate, async (guild) => {
  try {
    const rest = new REST({ version: "10" }).setToken(TOKEN);
    const data = await rest.put(
      Routes.applicationGuildCommands(client.user.id, guild.id),
      { body: buildSlashDefinitions() },
    );
    console.log(`Synced ${data.length} commands to new guild ${guild.name}`);
  } catch (e) {
    console.error("Sync on join failed:", e?.message || e);
  }
});

client.on(Events.MessageCreate, async (msg) => {
  if (msg.author.bot || !msg.guild) return;
  try {
    await handleRegistration(msg);
  } catch (e) {
    console.error("Registration handler error:", e);
  }
  if (msg.content.startsWith("?")) {
    try {
      await handlePrefix(msg);
    } catch (e) {
      console.error("Prefix handler error:", e);
      try {
        await msg.reply(`An error occurred: \`${e.message}\``);
      } catch {}
    }
  }
});

client.on(Events.InteractionCreate, async (interaction) => {
  try {
    if (interaction.isChatInputCommand()) {
      await handleSlash(interaction);
    } else {
      await handleInteraction(interaction);
    }
  } catch (e) {
    console.error("Interaction error:", e);
    try {
      const payload = { content: `An error occurred: \`${e.message}\``, ephemeral: true };
      if (interaction.deferred || interaction.replied) await interaction.followUp(payload);
      else await interaction.reply(payload);
    } catch {}
  }
});

client.on(Events.GuildMemberAdd, async (member) => {
  try {
    await handleMemberJoin(member);
  } catch (e) {
    console.error("Welcome handler error:", e);
  }
});

client.login(TOKEN);
