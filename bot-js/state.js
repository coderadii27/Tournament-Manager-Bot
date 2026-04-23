import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(__dirname, "data");
fs.mkdirSync(DATA_DIR, { recursive: true });
const FILE = path.join(DATA_DIR, "state.json");

const DEFAULT = { guilds: {}, giveaways: {} };

function load() {
  if (!fs.existsSync(FILE)) return structuredClone(DEFAULT);
  try {
    const data = JSON.parse(fs.readFileSync(FILE, "utf8"));
    for (const k of Object.keys(DEFAULT)) data[k] ??= DEFAULT[k];
    return data;
  } catch {
    return structuredClone(DEFAULT);
  }
}

function save(data) {
  fs.writeFileSync(FILE + ".tmp", JSON.stringify(data, null, 2));
  fs.renameSync(FILE + ".tmp", FILE);
}

export function getGuild(guildId) {
  const data = load();
  const id = String(guildId);
  if (!data.guilds[id]) {
    data.guilds[id] = {
      tournament_name: "EliteQ-tourny",
      team_size: 5,
      max_slots: 16,
      running: false,
      paused: false,
      registration_channel_id: null,
      confirm_channel_id: null,
      slot_manager_channel_id: null,
      teams: [],
      groups: {},
      schedule: [],
      points: [],
    };
    save(data);
  }
  return data.guilds[id];
}

export function saveGuild(guildId, g) {
  const data = load();
  data.guilds[String(guildId)] = g;
  save(data);
}

export function updateGuild(guildId, patch) {
  const g = getGuild(guildId);
  Object.assign(g, patch);
  saveGuild(guildId, g);
  return g;
}

export function getAllGiveaways() {
  return load().giveaways || {};
}

export function setGiveaway(messageId, payload) {
  const data = load();
  data.giveaways[String(messageId)] = payload;
  save(data);
}

export function removeGiveaway(messageId) {
  const data = load();
  delete data.giveaways[String(messageId)];
  save(data);
}
