"""Register Slash commands without starting the gateway.

Use GUILD_ID for instant development registration; omit it for global deploy.
"""

from __future__ import annotations

import asyncio

import discord
from discord.ext import commands

import config
from bot import COGS


async def main() -> None:
    intents = discord.Intents.none()
    bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents)
    await bot.login(config.TOKEN)
    for module in COGS:
        await bot.load_extension(module)
    if config.GUILD_ID.isdigit():
        guild = discord.Object(id=int(config.GUILD_ID))
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"registered {len(synced)} commands to guild {config.GUILD_ID}")
    else:
        synced = await bot.tree.sync()
        print(f"registered {len(synced)} global commands")
    await bot.close()


if __name__ == "__main__":
    if not config.TOKEN:
        raise SystemExit("DISCORD_TOKEN is required")
    asyncio.run(main())
