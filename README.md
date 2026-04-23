# 🏆 BRN ESPORTS — Tournament Manager Bot

> **BRN ESPORTS OFFICIAL BOT** — a complete Discord tournament manager built for the **BERNICS ESPORTS** community.
> Available in **two implementations**: **Python (discord.py)** and **JavaScript (discord.js v14)**. Pick whichever you prefer — both have the **same commands and the same features**.

- **Bot prefix:** `?`
- **Status:** Do Not Disturb
- **Activity:** *Organising Tournaments in BRN ESPORTS*
- **Description:** *BRN ESPORTS OFFICIAL BOT*

---

## ✨ Features

### 🏆 Tournament Control
- `?t` opens the **Tournament Control Panel** with buttons for:
  - **Create Tournament** — set name, team size, total slots
  - **Create Channels** — auto-creates 11 styled channels (info, updates, rules, how-to-register, registration-format, registration, confirm-teams, roadmaps, schedule, point-table, query) under one category
  - **Start / Pause Tournament**
  - **Manage Groups** — split confirmed teams into groups (A, B, C…)
  - **Slot Manager** — list / cancel / reset slots
- Slash equivalents: `/info`, `/settournamentname`, `/setslots`, `/setteamsize`, `/endtournament`

### 📋 Auto Registration
- Drop the standard registration format in `#—͟͞͞-⨳〢registration-format` (auto-posted when channels are created)
- Members fill it and post in `#—͟͞͞-⨳〢registration`
- Bot validates the team size, prevents duplicates and overflow, reacts ✅ / ⚠️ / ❌, and posts a confirmation card in `#—͟͞͞-⨳〢confirm-teams`
- `/teamlist` `/removeteam` `/lineup`

### 📅 Schedule & IDP
- `/addmatch <match_no> <team_a> [team_b] [time] [room_id] [room_pass]`
- `/removematch <match_no>` · `/schedule` · `/idp <match_no> <room_id> <room_pass>`

### 🏅 Point Table
- `/setpoints` · `/addpoints` · `/resetpoints` · `/points`

### 📢 Communication (multi-line modals)
- `/announce` — banner image + optional `@everyone` ping, multi-line body
- `/dmcaptains` — DM all team captains in one click
- `/greet` — DM every member (or only members of a chosen role) with a custom welcome embed (banner image, footer GIF, `{user}`, `{name}`, `{server}` placeholders)
- `/sayembed` — full custom embed (color hex, image, thumbnail, footer + footer icon/GIF)
- `/poll` — quick poll with up to 5 options and emoji reactions

### 👋 Auto-Welcome System
- `/setwelcome <#channel> <message> [image_url]` — fires automatically when a new member joins
- `/welcomeoff` — disables it
- Placeholders: `{user}` `{name}` `{server}`

### 🔍 Info
- `/serverinfo` · `/userinfo [user]` · `/avatar [user]`

### 🛡️ Moderation
- `/ban` · `/kick` · `/mute <user> <time>` · `/unmute`
- `?purge <1-100>` — delete N messages
- `?purge @user` — delete that user's last 100 messages

### 🎉 Giveaways
- `?gstart <time> <prize> <winners>winner`
  - Example: `?gstart 10m Nitro 1winner`
  - Time formats: `30s`, `5m`, `2h`, `1d`
- Members click **Join Giveaway** to enter; bot picks winners automatically when time runs out

### 🆘 Help
- `/help` — pretty in-Discord guide of every command

---

## 📦 Prerequisites

1. A Discord account and a server where you have **Administrator** permission.
2. A bot application at [discord.com/developers/applications](https://discord.com/developers/applications).
3. **Enable all 3 Privileged Gateway Intents** for the bot:
   - PRESENCE INTENT
   - SERVER MEMBERS INTENT
   - MESSAGE CONTENT INTENT
4. Invite the bot to your server with **Administrator** permission (or at least: Manage Channels, Manage Messages, Kick/Ban Members, Moderate Members, Send Messages, Embed Links, Add Reactions, Read Message History).

You only need **one** environment variable:

```
DISCORD_BOT_TOKEN=your-bot-token-here
```

---

## 🐍 Run the Python Version

> Requires **Python 3.11+**

```bash
cd bot
pip install discord.py
export DISCORD_BOT_TOKEN="your-bot-token-here"
python main.py
```

Project layout:
```
bot/
├── main.py              # entrypoint, intents, command sync
├── state.py             # JSON persistence
├── data/state.json      # auto-created
└── cogs/
    ├── tournament.py        # ?t panel + buttons + modals
    ├── registration.py      # auto team registration listener
    ├── slot_manager.py      # slot list / cancel / reset
    ├── moderation.py        # ban/kick/mute/unmute
    ├── purge.py             # ?purge
    ├── giveaway.py          # ?gstart + winner picker loop
    └── management.py        # everything else (announce, schedule, points, welcome, help…)
```

---

## 🟨 Run the JavaScript Version

> Requires **Node.js 20+**

```bash
cd bot-js
npm install
export DISCORD_BOT_TOKEN="your-bot-token-here"
npm start
```

Project layout:
```
bot-js/
├── package.json
├── index.js                  # entrypoint, intents, command sync
├── constants.js              # colors, channel names, parsers
├── state.js                  # JSON persistence
├── data/state.json           # auto-created
├── commands/
│   ├── definitions.js        # all 31 slash command definitions
│   ├── slash.js              # slash command handlers
│   ├── prefix.js             # ?t · ?purge · ?gstart
│   └── interactions.js       # buttons + modals
└── events/
    ├── registration.js       # auto team registration listener
    ├── giveaway.js           # winner picker loop
    └── welcome.js            # auto-welcome on member join
```

> ℹ️ **Don't run both versions at the same time** with the same bot token — Discord allows only one active session per token. Pick one, or create a second bot application for the other.

---

## 🚀 First Run Checklist

1. Bot comes online (status: DND, activity: *Organising Tournaments in BRN ESPORTS*).
2. Slash commands appear in your server **instantly** (per-guild sync).
3. Run `?t` in any channel → the **Tournament Control Panel** appears.
4. Click **Create Tournament** → set name, team size, slots.
5. Click **Create Channels** → 11 styled channels are created with the registration format auto-posted.
6. Members register in `#—͟͞͞-⨳〢registration` — confirmed teams appear in `#—͟͞͞-⨳〢confirm-teams`.
7. Use `/addmatch` and `/idp` for the schedule, `/setpoints` for the leaderboard, `/announce` for updates.

---

## 📌 Quick Command Reference

| Category      | Commands |
|---------------|----------|
| Tournament    | `?t` · `/info` · `/settournamentname` · `/setslots` · `/setteamsize` · `/endtournament` |
| Teams         | `/teamlist` · `/removeteam` · `/lineup` |
| Schedule      | `/addmatch` · `/removematch` · `/schedule` · `/idp` |
| Points        | `/setpoints` · `/addpoints` · `/resetpoints` · `/points` |
| Communication | `/announce` · `/dmcaptains` · `/greet` · `/sayembed` · `/poll` |
| Welcome       | `/setwelcome` · `/welcomeoff` |
| Info          | `/serverinfo` · `/userinfo` · `/avatar` |
| Moderation    | `/ban` · `/kick` · `/mute` · `/unmute` · `?purge` |
| Giveaway      | `?gstart` |
| Help          | `/help` |

---

Made with love by **Aditya aka Cyclopso** 💜
