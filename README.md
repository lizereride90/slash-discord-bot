# Slash

All-in-one Discord bot. Prefix + slash, Components V2 embeds, with a quality-gated command catalog.

Discord allows a maximum of 100 global top-level slash commands. Slash registers
The production surface contains only implemented, reviewed actions. Discord's
100 global slash limit is respected; registration count is not treated as proof
of usefulness.

- Brand: compact `Slash • Title` embeds, consistent footer, paginator + confirm views
- Mod: warn/history/case IDs, kick/ban/softban/timeout, purge/slowmode/lock
- Community: polls, suggestions, reports, tickets (buttons), giveaways, roles, levels
- Economy/XP: wallet/bank, daily/weekly/work/crime/rob/pay, XP ranks
- Utility: calc, converters, text styles, base64/hex/hash/uuid/color/timestamp/json/regex
- Automod-lite: link filter + burst guard, per-guild toggle
- Custom commands: `!name` triggers stored per guild
- Dashboard API in `api/`, tests in `tests/`
- Draft/generated experiments remain under `cogs/packs/` but are not loaded

Run `python3 scripts/quality_report.py` before release. It rejects numbered or
generated-style commands so fake implementations cannot be shipped as features.

Run: `pip install -r requirements.txt && cp .env.example .env && python bot.py`

GitHub: `https://github.com/lizereride90/slash-discord-bot`
