# Security Notes

- Keep `DISCORD_TOKEN`, `API_TOKEN`, and `.env` out of version control.
- Bot moderation checks native permissions and role hierarchy before destructive actions.
- Custom commands store plain text only; they never execute Python or JavaScript.
- Math evaluation uses an AST allow-list and an empty builtins mapping.
- Dashboard config access requires a configured constant-time-compared bearer token.
- API guild IDs are validated as Discord snowflake-shaped numeric IDs.
- SQLite data is parameterized through query arguments.
- Use HTTPS and a reverse proxy before exposing the dashboard API.
- Configure least-privilege Discord permissions instead of granting administrator in production.
