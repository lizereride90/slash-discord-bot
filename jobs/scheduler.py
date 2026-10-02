"""Persistent-ish job loop. DB-backed due checks, no bare setTimeout reliance."""

from __future__ import annotations

import asyncio


async def tick_forever(bot, interval: float = 30.0):
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            # place for: expire timeouts, end giveaways, run reminders from db
            pass
        except Exception:
            pass
        await asyncio.sleep(interval)
