# Commands

Slash registers the curated interactive surface because Discord caps global
top-level slash commands at 100. The current release registers 100 slash commands.

The catalog contains only production commands. Draft/generated experiments are
not loaded or advertised. `commands/catalog.json` contains `slash: true|false`
for dashboard discovery.

Examples:

```text
/welcome #welcome true https://example.com/avatar.png Welcome {member} to {server}!
!welcome #welcome true https://example.com/avatar.png Welcome {member} to {server}!
/moderation-style commands use the curated slash surface
!text42 hello
```
