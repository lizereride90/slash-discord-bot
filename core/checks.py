"""Tiny permission helpers. Centralizes hierarchy checks so
individual commands stay small."""

from __future__ import annotations

import discord
from discord.ext import commands

import config


def is_owner(uid: int) -> bool:
    return uid in config.OWNER_IDS


async def can_act(
    ctx_or_inter,
    target: discord.Member,
    action: str = "moderate",
) -> tuple[bool, str]:
    """Returns (ok, reason). Checks hierarchy + self/bot/owner guards."""
    guild = getattr(ctx_or_inter, "guild", None)
    me = getattr(ctx_or_inter, "author", None) or getattr(ctx_or_inter, "user", None)
    if guild is None or me is None:
        return False, "Server-only command."
    if not isinstance(me, discord.Member):
        try:
            me = guild.get_member(me.id)  # type: ignore
        except Exception:
            pass
    bot_member = guild.me
    if target.id == me.id:
        return False, "You can't target yourself."
    if target.id == guild.owner_id:
        return False, "You can't target the server owner."
    if bot_member and target.id == bot_member.id:
        return False, "You can't target me."
    if isinstance(me, discord.Member):
        if target.top_role >= me.top_role and me.id != guild.owner_id:
            return False, "Target has equal/higher role than you."
    if bot_member and target.top_role >= bot_member.top_role:
        return False, "I can't act — target's role is above mine."
    return True, ""


def owner_only():
    async def pred(ctx: commands.Context) -> bool:
        return ctx.author.id in config.OWNER_IDS

    return commands.check(pred)
