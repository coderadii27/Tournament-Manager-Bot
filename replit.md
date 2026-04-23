# BRN ESPORTS Tournament Manager Bot

A Discord tournament manager bot for **BERNICS ESPORTS**, available in two implementations with identical features.

## Implementations

- **Python (`bot/`)** — `discord.py`. Entrypoint: `bot/main.py`. Runs in the `Discord Bot` workflow (`cd bot && python main.py`).
- **JavaScript (`bot-js/`)** — `discord.js v14`, ESM, Node 20+. Entrypoint: `bot-js/index.js`. Run with `cd bot-js && npm install && npm start`.

Both versions:
- Use `?` as the prefix and DND status with activity *Organising Tournaments in BRN ESPORTS*.
- Sync 31 slash commands per-guild on ready (instant availability).
- Persist state to `data/state.json` inside their own directory.
- Read the `DISCORD_BOT_TOKEN` secret. Only one version should run at a time per token.

## Feature Surface

- Tournament Control Panel (`?t`) with buttons: Create Tournament, Create Channels (11 styled channels under one category, registration format auto-posted), Start/Pause, Manage Groups, Slot Manager.
- Auto registration listener that validates the standard format, prevents duplicates/overflow, reacts ✅/⚠️/❌, and posts to a confirm channel.
- Schedule + IDP, point table, communication modals (announce / dmcaptains / greet / sayembed) with multi-line support, banner image, footer GIF, role filtering, and `{user}/{name}/{server}` placeholders.
- Auto-welcome system (`/setwelcome`, `/welcomeoff`).
- Info utilities (`/serverinfo`, `/userinfo`, `/avatar`, `/poll`).
- Moderation (`/ban`, `/kick`, `/mute`, `/unmute`, `?purge`).
- Giveaways (`?gstart <time> <prize> <Nwinner>`) with button-based entry and an end-time loop.

## Repository Layout

```
README.md                # full install + feature guide (ends with "Made with love by Aditya aka Cyclopso")
replit.md                # this file
bot/                     # Python implementation
bot-js/                  # JavaScript implementation
```

The previous TypeScript scaffold (`artifacts/api-server`, `artifacts/mockup-sandbox`, `lib/`, `package.json`, `pnpm-*`, `tsconfig*`) has been removed — this project is Python + JavaScript only.

## User Preferences

- No TypeScript anywhere.
- README must end with: *Made with love by Aditya aka Cyclopso*.
