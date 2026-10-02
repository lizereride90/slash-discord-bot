# Slash — setup

1. Create app in Discord Developer Portal → Bot → Reset Token → copy.
2. Enable intents: **Message Content** + **Server Members**.
3. `cp .env.example .env` → paste `DISCORD_TOKEN=`, set `PREFIX=!`.
4. `pip install -r requirements.txt`
5. `python bot.py`
6. Invite with `bot + applications.commands` scope, admin for full mod.

For command-only registration use `python deploy.py`. Use `GUILD_ID` during development;
leave it empty for global registration.

Docker: `docker compose up -d --build`.

Optional dashboard API: `uvicorn api.server:app --host 0.0.0.0 --port 8080`.

Slash commands sync globally (can take ~1h first time). Set `GUILD_ID=` for instant test-guild sync.
Discord caps global top-level slash commands at 100; Slash registers 100 curated
slash actions and keeps the rest as prefix commands.

## Layout

- `bot.py` — entry, prefix+slash, XP, error IDs
- `config.py` — env + brand
- `core/` — embeds (CV2), db, checks, logger, cache, errors
- `cogs/` — feature cogs (top-level) + `cogs/packs/` bulk + domain folders
  `community/ economy/ fun/ info/ management/ moderation/ system/ utility/`
- `services/` — testable business logic
- `utils/` — formatting, time
- `jobs/` — scheduler loop
- `api/` — dashboard REST (FastAPI, optional)
- `tests/` — pytest, no token needed
- `commands/catalog.json` — generated command list for `/help` + dashboard
