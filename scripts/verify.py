"""Offline release check. Does not connect to Discord or require a token."""

from __future__ import annotations

import asyncio
import sys

sys.path.insert(0, ".")

import bot


async def main() -> None:
    for module in bot.COGS:
        await bot.bot.load_extension(module)
    prefix_count = len(bot.bot.commands)
    slash_count = len(bot.bot.tree.get_commands())
    if slash_count > 100:
        raise SystemExit(f"too many slash commands: {slash_count}")
    if prefix_count < 80:
        raise SystemExit(f"production command surface too small: {prefix_count}")
    print(f"release check passed: {len(bot.COGS)} cogs, {prefix_count} reviewed prefix, {slash_count} slash")
    await bot.bot.close()


if __name__ == "__main__":
    asyncio.run(main())
