# BRN ESPORTS — Discord Tournament Manager Bot

A clean, modern Discord bot built with **Python + discord.py** for managing esports tournaments end-to-end: registration, slot management, groups, moderation, purges, and giveaways.

- **Status:** Do Not Disturb
- **Activity:** Organising Tournaments in BRN ESPORTS
- **Description:** BRN ESPORTS OFFICIAL BOT
- **Prefix:** `?`

## Features

### Tournament Control Panel — `?t`
A modern embed with buttons:
- **Create Tournament** — set name, team size, and total slots (16 / 32 / 64 …)
- **Create Channels** — auto-creates the full tournament category and channels
- **Start Tournament** / **Pause Tournament**
- **Manage Groups** — auto-distribute teams into groups
- **Slot Manager** — sets up the slot manager channel and panel

### Auto-Created Channels
```
—͟͞͞-⨳〢info
—͟͞͞-⨳〢updates
—͟͞͞-⨳〢rules
—͟͞͞-⨳〢how-to-register
—͟͞͞-⨳〢registration-format
—͟͞͞-⨳〢registration
—͟͞͞-⨳〢confirm-teams
—͟͞͞-⨳〢roadmaps
—͟͞͞-⨳〢schedule
—͟͞͞-⨳〢point-table
—͟͞͞-⨳〢query
```

### Registration System
- The bot watches the registration channel automatically.
- Reacts with ✅ when a team posts the correct format.
- Reacts with ❌ when the format is wrong.
- Reacts with ⚠️ if the team name is already taken.
- Sends a confirmation embed to `confirm-teams` when validated.
- Tournament creator sets total slots and players per team.

### Registration Format (auto-posted)
```
TEAM NAME -

PLAYER 1 (IGL) :
CHARACTER ID :
DISCORD TAG :

PLAYER 2 :
CHARACTER ID :
DISCORD TAG :
... (up to PLAYER 5)
```

### Slot Manager Panel
Channel `slot-manager` with buttons:
- **Cancel My Slot** *(irreversible)*
- **My Slots**
- **Change Team Name**

### Moderation (Slash Commands)
- `/ban user reason`
- `/kick user reason`
- `/mute user time reason` — time examples: `10m`, `2h`, `1d` (max 28 days)
- `/unmute user`

### Purge Command
- `?purge <1-100>` — bulk delete messages
- `?purge @user` — delete recent messages from a specific user

### Giveaway System
- `?gstart <time> <prize> <winners>winner`
- Time formats: `30s`, `10m`, `2h`, `1d`
- Example: `?gstart 10m Nitro 1winner`
- Embed with **Join Giveaway** button, automatic end and random winner selection.

## File Structure
```
bot/
├── main.py
├── state.py              # Persistent JSON store
├── data/                 # Auto-created at runtime
└── cogs/
    ├── tournament.py     # ?t panel + buttons + channel/group setup
    ├── registration.py   # Registration channel monitor
    ├── slot_manager.py   # Slot manager panel
    ├── moderation.py     # /ban /kick /mute /unmute
    ├── purge.py          # ?purge
    └── giveaway.py       # ?gstart + auto-end loop
```

## How To Run

### 1. Create your bot
1. Go to <https://discord.com/developers/applications> → **New Application**.
2. Open the **Bot** tab → **Reset Token** → copy it.
3. Enable these **Privileged Gateway Intents**:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
4. Under **OAuth2 → URL Generator**, choose scopes:
   - `bot`, `applications.commands`
   And bot permissions:
   - Manage Channels, Manage Messages, Kick Members, Ban Members,
     Moderate Members, Read Message History, Send Messages,
     Embed Links, Add Reactions, Use Slash Commands.
5. Open the generated URL and invite the bot to your server.

### 2. Run on Replit
1. Open the project on Replit.
2. Add your token in **Secrets** as `DISCORD_BOT_TOKEN`.
3. The bot workflow will start automatically. The bot will appear online with status **DND** and activity **"Organising Tournaments in BRN ESPORTS"**.

### 3. Run locally
```bash
# Requires Python 3.10+
pip install "discord.py>=2.4"
export DISCORD_BOT_TOKEN="your_token_here"
cd bot
python main.py
```

### 4. First time in your server
1. Type `?t` in any channel — the control panel opens.
2. Click **Create Tournament** → fill in name, team size, slots.
3. Click **Create Channels** → all tournament channels are created.
4. Click **Slot Manager** → sets up the slot manager panel.
5. Players post their team in `—͟͞͞-⨳〢registration` using the auto-posted format.

## Notes
- Slash commands sync globally on startup (may take up to 1 hour to appear the first time).
- Persistent state is stored at `bot/data/state.json`. Back it up if needed.
- All button views use `custom_id`s and are re-registered on startup, so panels keep working after restarts.

---
**BRN ESPORTS OFFICIAL BOT**
