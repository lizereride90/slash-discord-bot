"""Giveaways: timed, entrants via reaction, reroll."""

from __future__ import annotations

import asyncio
import random
import time

import discord
from discord.ext import commands

from core import embeds as E

_live: dict[int, dict] = {}


class Giveaways(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="giveaway", description="Start giveaway: minutes winners prize")
    @commands.has_permissions(manage_messages=True)
    async def start(self, ctx: commands.Context, minutes: float, winners: int, *, prize: str):
        minutes = max(0.1, min(10080, minutes))
        winners = max(1, min(20, winners))
        ends = time.time() + minutes * 60
        e = E.make("Giveaway", f"**{prize[:300]}**\nReact 🎉 to enter • {winners} winner(s)\nEnds <t:{int(ends)}:R>", guild=ctx.guild)
        assert ctx.channel
        msg = await ctx.send(embed=e)
        try:
            await msg.add_reaction("🎉")
        except Exception:
            pass
        _live[msg.id] = {"ends": ends, "winners": winners, "prize": prize, "ch": ctx.channel.id}
        await asyncio.sleep(minutes * 60)
        await self._finish(ctx.guild, msg.id)  # type: ignore

    async def _finish(self, guild: discord.Guild | None, mid: int):
        info = _live.pop(mid, None)
        if not guild or not info:
            return
        ch = guild.get_channel(info["ch"])
        if not isinstance(ch, discord.TextChannel):
            return
        try:
            msg = await ch.fetch_message(mid)
        except Exception:
            return
        users: list[discord.User] = []
        for r in msg.reactions:
            if str(r.emoji) == "🎉":
                try:
                    async for u in r.users():
                        if not u.bot:
                            users.append(u)
                except Exception:
                    pass
        if not users:
            await ch.send(embed=E.info("Giveaway ended", f"No entrants for **{info['prize']}**."))
            return
        win = random.sample(users, min(info["winners"], len(users)))
        await ch.send(f"🎉 Winners for **{info['prize']}**: " + " ".join(u.mention for u in win))

    @commands.hybrid_command(name="reroll", description="Reroll a giveaway message")
    @commands.has_permissions(manage_messages=True)
    async def reroll(self, ctx: commands.Context, message_id: str):
        try:
            mid = int(message_id)
            msg = await ctx.channel.fetch_message(mid)  # type: ignore
        except Exception:
            await ctx.send(embed=E.error("Bad id", "Paste a message ID from this channel."), ephemeral=True)
            return
        users = []
        for r in msg.reactions:
            if str(r.emoji) == "🎉":
                async for u in r.users():
                    if not u.bot:
                        users.append(u)
        if not users:
            await ctx.send(embed=E.info("No entrants", "Nobody entered that one."))
            return
        await ctx.send(f"🎉 New winner: {random.choice(users).mention}")

    @commands.hybrid_command(name="glist", description="Active giveaways")
    async def glist(self, ctx: commands.Context):
        if not _live:
            await ctx.send(embed=E.info("None", "No active giveaways."))
            return
        desc = "\n".join(f"`{mid}` — **{v['prize'][:60]}** ends <t:{int(v['ends'])}:R>" for mid, v in list(_live.items())[:15])
        await ctx.send(embed=E.make("Giveaways", desc, guild=ctx.guild))


async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaways(bot))
