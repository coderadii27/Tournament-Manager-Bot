<div align="center">

# 🏆 BRN ESPORTS — Tournament Manager Bot

**The official Discord bot for the BERNICS ESPORTS community.**
A complete tournament manager + ticket support system, available in **two implementations** — pick whichever you prefer.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-20+-green?logo=nodedotjs&logoColor=white)](https://nodejs.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2?logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![discord.js](https://img.shields.io/badge/discord.js-v14-5865F2?logo=discord&logoColor=white)](https://discord.js.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](#-license)

</div>

---

## ✨ Highlights

- 🏆 **Full tournament workflow** — control panel, auto channels, registration, slot manager, groups
- 📋 **Auto team registration** with format validation, duplicate guard, slot overflow guard
- 📅 **Schedule + IDP system** with Room ID / Password broadcasts
- 🏅 **Live point table** (points / kills / wins, sorted leaderboard)
- 📢 **Multi-line modals** for announcements, captain DMs, custom embeds, and member greetings (banner image, footer GIF, role filter, `{user}` `{name}` `{server}` placeholders)
- 👋 **Auto-welcome** on member join
- 🔍 **Server / user / avatar / poll** utilities
- 🛡️ **Moderation**: ban / kick / mute / unmute / purge
- 🎉 **Giveaway system** with one-click button entry and automatic winner picking
- 🎫 **Ticket support system** — private channels with **Claim** + **Close** buttons, staff role permissions
- 🆘 `/help` shows everything in-Discord

> **Bot prefix:** `?` · **Status:** Do Not Disturb · **Activity:** *Organising Tournaments in BRN ESPORTS* · **Description:** *BRN ESPORTS OFFICIAL BOT*

---

## 📦 Prerequisites

1. A Discord account and a server where you have **Administrator** permission.
2. A bot application at [discord.com/developers/applications](https://discord.com/developers/applications).
3. **Enable all 3 Privileged Gateway Intents** for your bot:
   - PRESENCE INTENT
   - SERVER MEMBERS INTENT
   - MESSAGE CONTENT INTENT
4. Invite the bot with **Administrator** permission (or at minimum: Manage Channels, Manage Roles, Manage Messages, Kick / Ban Members, Moderate Members, Send Messages, Embed Links, Add Reactions, Read Message History).
5. Set this single environment variable:

   ```
   DISCORD_BOT_TOKEN=your-bot-token-here
   ```

> ⚠️ **Don't run both versions at the same time** with the same token — Discord allows only one active gateway session per bot.

---

## 🐍 Installation — Python (`discord.py`)

> Requires **Python 3.11+**

```bash
# Clone
git clone https://github.com/<your-username>/brn-esports-bot.git
cd brn-esports-bot/bot

# Install
pip install discord.py

# Configure
export DISCORD_BOT_TOKEN="your-bot-token-here"     # macOS/Linux
# setx DISCORD_BOT_TOKEN "your-bot-token-here"     # Windows (re-open terminal after)

# Run
python main.py
```

Project layout:

```
bot/
├── main.py                  # entrypoint, intents, command sync
├── state.py                 # JSON persistence
├── data/state.json          # auto-created
└── cogs/
    ├── tournament.py        # ?t panel + buttons + modals
    ├── registration.py      # auto team registration listener
    ├── slot_manager.py      # slot list / cancel / reset
    ├── moderation.py        # ban/kick/mute/unmute
    ├── purge.py             # ?purge
    ├── giveaway.py          # ?gstart + winner picker loop
    ├── ticket.py            # /ticketsetup + Open / Claim / Close buttons
    └── management.py        # everything else (announce, schedule, points, welcome, help…)
```

---

## 🟨 Installation — JavaScript (`discord.js v14`)

> Requires **Node.js 20+**

```bash
# Clone
git clone https://github.com/<your-username>/brn-esports-bot.git
cd brn-esports-bot/bot-js

# Install
npm install

# Configure
export DISCORD_BOT_TOKEN="your-bot-token-here"     # macOS/Linux
# setx DISCORD_BOT_TOKEN "your-bot-token-here"     # Windows (re-open terminal after)

# Run
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
│   ├── definitions.js        # all slash command definitions
│   ├── slash.js              # slash command handlers
│   ├── prefix.js             # ?t · ?purge · ?gstart
│   ├── interactions.js       # buttons + modals
│   └── tickets.js            # ticket panel + claim / close
└── events/
    ├── registration.js       # auto team registration listener
    ├── giveaway.js           # winner picker loop
    └── welcome.js            # auto-welcome on member join
```

---

## 🚀 First-Run Walkthrough

1. The bot comes online (status: DND, activity: *Organising Tournaments in BRN ESPORTS*).
2. All slash commands appear in your server **instantly** (per-guild sync — no 1-hour wait).
3. Type `?t` → **Tournament Control Panel** appears with action buttons.
4. **Create Tournament** → set name, team size, total slots.
5. **Create Channels** → 11 styled channels are created with the registration format auto-posted.
6. Members register by posting the format in `#—͟͞͞-⨳〢registration` — confirmed teams appear in `#—͟͞͞-⨳〢confirm-teams`.
7. Use `/ticketsetup` to set up the support ticket panel.
8. Use `/addmatch` + `/idp` for matches, `/setpoints` for the leaderboard, `/announce` for updates.

---

## 🎫 Ticket Support System

A polished, BERNICS-branded ticket flow.

**Setup (admin runs once):**

```
/ticketsetup staff_role:@Moderator category:🎫 Tickets channel:#support
```

Posts a panel that looks like:

> **BERNICS ESPORTS • Support**
> 🎫 **Need Help? Open a Ticket**
> Welcome to support! Click the button below to open a private ticket with our staff team.
>
> **How it works**
> › A private channel is created just for you
> › Only you and staff can see it
> › Describe your issue and we'll help ASAP
> › Close the ticket when you're done
>
> *Please don't open a ticket without a real reason — abuse may result in action.*
>
> *Powered by your friendly support team*

**What happens next:**

| Action | Result |
|--------|--------|
| Member clicks **🎫 Open Ticket** | A private channel `ticket-####-username` is created under the configured category. Only the user, the configured **staff role**, and admins (Manage Channels) can see it. |
| Staff clicks **🙋 Claim** | The ticket header updates: `🟡 Open • Claimed by @Moderator`. |
| Staff or opener clicks **🔒 Close** | A "closing in 5 seconds" notice is posted, then the channel is deleted. |
| One ticket per user | If the user already has an open ticket, the bot points them to it instead of creating a duplicate. |

Slash commands:

| Command | Purpose |
|---------|---------|
| `/ticketsetup [staff_role] [category] [channel]` | Configure + post the panel |
| `/ticketpanel` | Re-post the panel in the current channel |
| `/ticketclose` | Close the current ticket (works inside any ticket channel) |

---

## 📌 Full Command Reference

### 🏆 Tournament
| Command | Description |
|---|---|
| `?t` | Open the Tournament Control Panel |
| `/info` | Show tournament info (name, slots, status, groups) |
| `/settournamentname <name>` | Rename the tournament |
| `/setslots <n>` | Set total slots |
| `/setteamsize <n>` | Set players per team |
| `/endtournament` | End and reset the tournament |

### 📋 Teams
| Command | Description |
|---|---|
| `/teamlist` | List confirmed teams |
| `/removeteam <team>` | Remove a team by name |
| `/lineup` | Show group lineup |

### 📅 Schedule & IDP
| Command | Description |
|---|---|
| `/addmatch <match_no> <team_a> [team_b] [time] [room_id] [room_pass]` | Add or update a match |
| `/removematch <match_no>` | Remove a match |
| `/schedule` | Show match schedule |
| `/idp <match_no> <room_id> <room_pass>` | Broadcast Room ID + Password |

### 🏅 Point Table
| Command | Description |
|---|---|
| `/setpoints <team> <points> [kills] [wins]` | Set points for a team |
| `/addpoints <team> [points] [kills] [wins]` | Add to team points |
| `/resetpoints` | Reset point table |
| `/points` | Show point table (sorted) |

### 📢 Communication
| Command | Description |
|---|---|
| `/announce [ping_everyone] [image_url]` | Multi-line announcement embed |
| `/dmcaptains` | DM all team captains a message |
| `/greet [image_url] [footer_gif] [role]` | DM all members (or one role) a welcome embed |
| `/sayembed [color_hex] [image_url] [thumbnail_url] [footer_icon_url]` | Build a fully custom embed |
| `/poll <question> [option1..option5]` | Quick poll with up to 5 reaction options |

### 👋 Welcome System
| Command | Description |
|---|---|
| `/setwelcome <#channel> <message> [image_url]` | Auto-greet new members. Placeholders: `{user}` `{name}` `{server}` |
| `/welcomeoff` | Disable auto-welcome |

### 🔍 Info
| Command | Description |
|---|---|
| `/serverinfo` | Server stats |
| `/userinfo [user]` | User stats |
| `/avatar [user]` | Show user's avatar |

### 🛡️ Moderation
| Command | Description |
|---|---|
| `/ban <user> [reason]` | Ban a user |
| `/kick <user> [reason]` | Kick a user |
| `/mute <user> <time> [reason]` | Timeout (`10m`, `2h`, `1d`, max 28 days) |
| `/unmute <user>` | Remove timeout |
| `?purge <1-100>` | Delete N messages |
| `?purge @user` | Delete that user's last 100 messages |

### 🎉 Giveaways
| Command | Description |
|---|---|
| `?gstart <time> <prize> <Nwinner>` | Start a giveaway. Example: `?gstart 10m Nitro 1winner` |

### 🎫 Tickets
| Command | Description |
|---|---|
| `/ticketsetup [staff_role] [category] [channel]` | Configure + post the support panel |
| `/ticketpanel` | Re-post the panel here |
| `/ticketclose` | Close the current ticket |

### 🆘 Help
| Command | Description |
|---|---|
| `/help` | Pretty in-Discord guide of every command |

---

## 🧠 How State is Stored

Each implementation persists everything to a single JSON file inside its own folder:

- Python → `bot/data/state.json`
- JavaScript → `bot-js/data/state.json`

This keeps deployment dead simple — no database required. To reset everything for a guild, stop the bot and delete that file.

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| Slash commands don't appear | Make sure the bot has the `applications.commands` scope and was invited fresh after that change. The bot syncs **per-guild on ready** so new guilds get commands instantly. |
| `MESSAGE CONTENT INTENT` errors | Enable all 3 privileged intents in the [Discord Developer Portal](https://discord.com/developers/applications). |
| Tickets / channels can't be created | Bot needs **Manage Channels** permission. Admin role works best. |
| Greet / DM Captains says "0 sent" | Members have DMs disabled, or you filtered to a role nobody has. |

---

## 📄 License

MIT — do whatever you want, just keep the credit.

---

<div align="center">

### 💜 Made with love by **Aditya aka Cyclopso**

</div>
