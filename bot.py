"""Slash — all-in-one Discord bot. Prefix + slash (hybrid), CV2 embeds."""

from __future__ import annotations

import asyncio
import os
import sys
import time
import traceback

import discord
from discord.ext import commands

import config
from core import db
from core.embeds import error as err_embed, view_from_embed

COGS = [
    "cogs.info.commands",
    "cogs.moderation.warns",
    "cogs.moderation.bans",
    "cogs.moderation.cleanup",
    "cogs.moderation.notes",
    "cogs.moderation.security",
    "cogs.leveling",
    "cogs.polls",
    "cogs.tickets",
    "cogs.giveaways",
    "cogs.roles",
    "cogs.channels",
    "cogs.automod",
    "cogs.settings",
    "cogs.dev",
    "cogs.system.v2demo",
    "cogs.community.welcome",
    "cogs.community.audit",
    "cogs.management.tasks",
]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

class SlashContext(commands.Context):
    """Render factory embeds as Components V2 without changing every cog."""

    async def send(self, *args, **kwargs):
        embed = kwargs.get("embed")
        if getattr(embed, "slash_v2", False) and kwargs.get("view") is None:
            kwargs.pop("embed")
            kwargs["view"] = view_from_embed(embed)
        return await super().send(*args, **kwargs)


class SlashBot(commands.Bot):
    async def get_context(self, origin, *, cls=SlashContext):
        return await super().get_context(origin, cls=cls)


bot = SlashBot(command_prefix=config.PREFIX, intents=intents, help_command=None)
bot.started_at = time.time()  # type: ignore
_xp_cd: dict[tuple[int, int], float] = {}
_synced = False


async def _load_extensions() -> None:
    await db.init()
    for module in COGS:
        try:
            await bot.load_extension(module)
        except Exception as exc:
            print(f"[cog] {module} failed: {exc}")


@bot.event
async def setup_hook():
    await _load_extensions()


@bot.event
async def on_ready():
    global _synced
    if _synced:
        return
    try:
        if config.GUILD_ID and config.GUILD_ID.isdigit():
            g = discord.Object(id=int(config.GUILD_ID))
            bot.tree.copy_global_to(guild=g)
            s = await bot.tree.sync(guild=g)
            print(f"[ready] synced {len(s)} to test guild")
            # Development commands must live in one scope. Keeping the same
            # payload globally and in the test guild makes Discord clients
            # show apparent duplicates while their caches settle.
            bot.tree.clear_commands(guild=None)
            cleared = await bot.tree.sync()
            print(f"[ready] cleared global commands ({len(cleared)} remaining)")
        else:
            s = await bot.tree.sync()
            print(f"[ready] synced {len(s)} global slash commands")
        _synced = True
    except Exception as e:
        print(f"[ready] sync failed: {e}")
    # also dump catalog for dashboard/help
    try:
        from cogs.info.commands import build_catalog

        await build_catalog(bot)
    except Exception:
        pass
    print(f"[ready] {bot.user} in {len(bot.guilds)} guilds, prefix={config.PREFIX}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{config.PREFIX}help • /help"))


@bot.event
async def on_command_error(ctx: commands.Context, exc: Exception):
    exc = getattr(exc, "original", exc)
    if isinstance(exc, commands.CommandNotFound):
        return
    if isinstance(exc, commands.MissingPermissions):
        await ctx.send(embed=err_embed("Missing permissions", f"You need `{', '.join(exc.missing_permissions)}`."), delete_after=12)
    elif isinstance(exc, commands.BotMissingPermissions):
        await ctx.send(embed=err_embed("I lack permissions", f"I need `{', '.join(exc.missing_permissions)}`."), delete_after=12)
    elif isinstance(exc, commands.CommandOnCooldown):
        await ctx.send(embed=err_embed("Cooldown", f"Try again in {exc.retry_after:.1f}s."), delete_after=6)
    elif isinstance(exc, commands.MissingRequiredArgument):
        await ctx.send(embed=err_embed("Missing argument", f"`{exc.param.name}` is required."), delete_after=10)
    else:
        eid = f"ERR-{os.getpid():04X}{int(time.time())%65536:04X}"
        print(f"[{eid}] {type(exc).__name__}: {exc}\n{traceback.format_exc(limit=6)}")
        try:
            await ctx.send(embed=err_embed("Something broke", f"`{eid}` — try again, ping staff if it repeats."), delete_after=15)
        except Exception:
            pass


@bot.event
async def on_message(msg: discord.Message):
    if msg.author.bot or not msg.guild:
        return
    # passive xp (cheap, no db write spam)
    key = (msg.guild.id, msg.author.id)
    now = time.monotonic()
    if now - _xp_cd.get(key, 0) > 45 and len(msg.content) > 4:
        _xp_cd[key] = now
        try:
            await db.xp_add(msg.guild.id, msg.author.id, 5)
        except Exception:
            pass
    # custom command trigger: !ccname
    if msg.content.startswith(config.PREFIX) and len(msg.content) > 1:
        name = msg.content[len(config.PREFIX):].split()[0].lower()
        try:
            row = await db.q("SELECT text FROM custom_cmds WHERE guild_id=? AND name=?", (str(msg.guild.id), name), one=True)
            if row:
                await msg.channel.send(str(row["text"])[:1900])
                return
        except Exception:
            pass
    await bot.process_commands(msg)


def main() -> None:
    if not config.TOKEN:
        print("Missing DISCORD_TOKEN. cp .env.example .env and paste token.", file=sys.stderr)
        sys.exit(1)
    bot.run(config.TOKEN)


if __name__ == "__main__":
    main()
