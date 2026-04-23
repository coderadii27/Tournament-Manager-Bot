export const BRAND = 0x9b5cf6;
export const ACCENT = 0x00e5ff;

export const CHANNEL_NAMES = [
  "—͟͞͞-⨳〢info",
  "—͟͞͞-⨳〢updates",
  "—͟͞͞-⨳〢rules",
  "—͟͞͞-⨳〢how-to-register",
  "—͟͞͞-⨳〢registration-format",
  "—͟͞͞-⨳〢registration",
  "—͟͞͞-⨳〢confirm-teams",
  "—͟͞͞-⨳〢roadmaps",
  "—͟͞͞-⨳〢schedule",
  "—͟͞͞-⨳〢point-table",
  "—͟͞͞-⨳〢query",
];

export const REGISTRATION_FORMAT = `\`\`\`
TEAM NAME -

PLAYER 1 (IGL) :
CHARACTER ID :
DISCORD TAG :

PLAYER 2 :
CHARACTER ID :
DISCORD TAG :

PLAYER 3 :
CHARACTER ID :
DISCORD TAG :

PLAYER 4 :
CHARACTER ID :
DISCORD TAG :

PLAYER 5 :
CHARACTER ID :
DISCORD TAG :
\`\`\``;

export function parseDurationSec(text) {
  const m = /^\s*(\d+)\s*(s|sec|secs|seconds|m|min|mins|minutes|h|hr|hrs|hours|d|day|days)?\s*$/i.exec(text);
  if (!m) return null;
  const n = parseInt(m[1], 10);
  const u = (m[2] || "s").toLowerCase();
  if (u.startsWith("s")) return n;
  if (u.startsWith("m")) return n * 60;
  if (u.startsWith("h")) return n * 3600;
  if (u.startsWith("d")) return n * 86400;
  return null;
}

export function parseWinners(text) {
  const m = /^\s*(\d+)\s*(?:w|winner|winners)?\s*$/i.exec(text);
  return m ? parseInt(m[1], 10) : null;
}
