# Configuration

Copy `.env.example` to `.env`.

| Variable | Required | Purpose |
|---|---:|---|
| `DISCORD_TOKEN` | yes | Bot token; never commit it |
| `PREFIX` | no | Prefix commands, defaults to `!` |
| `CLIENT_ID` | no | Discord application ID |
| `GUILD_ID` | no | Development guild for instant slash sync |
| `OWNER_IDS` | no | Comma-separated developer IDs |
| `API_TOKEN` | no | Secret for the optional dashboard API |
| `GROQ_API_KEY` | no | Optional Groq key for future AI task planning |
| `GROQ_MODEL` | no | Groq model name, defaults to `llama-3.3-70b-versatile` |

The bot stores local SQLite data at `data/slash.db`. The database is created on
startup. Do not expose the database file or API token publicly.
