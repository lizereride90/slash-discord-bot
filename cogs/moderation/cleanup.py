"""Moderation — cleanup + channel locks. Part of cogs/moderation package."""

from __future__ import annotations

import asyncio

import discord
from discord.ext import commands

from core import embeds as E
from core.checks import can_act


class Cleanup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="purge", description="Bulk delete 1-200 messages")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def purge(self, ctx: commands.Context, amount: int, member: discord.Member | None = None):
        amount = max(1, min(200, amount))

        def check(m: discord.Message):
            return (member is None or m.author.id == member.id) and not m.pinned

        try:
            deleted = await ctx.channel.purge(limit=amount + 1, check=check)  # type: ignore
        except discord.HTTPException:
            await ctx.send(embed=E.error("Too old", "Can't bulk-delete messages older than 14 days."), ephemeral=True)
            return
        msg = await ctx.send(embed=E.success("Purged", f"Deleted `{max(0, len(deleted)-1)}` messages."))
        await asyncio.sleep(4)
        try:
            await msg.delete()
        except Exception:
            pass

    @commands.hybrid_command(name="slowmode", description="Slowmode seconds (0=off)")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, seconds: int):
        await ctx.channel.edit(slowmode_delay=max(0, min(21600, seconds)))  # type: ignore
        await ctx.send(embed=E.success("Slowmode", f"`{seconds}s`" if seconds else "Off"))

    @commands.hybrid_command(name="lock", description="Lock channel")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context):
        assert ctx.guild and isinstance(ctx.channel, discord.TextChannel)
        ow = ctx.channel.overwrites_for(ctx.guild.default_role)
        ow.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=ow)
        await ctx.send(embed=E.warning("Locked", "Only staff can speak."))

    @commands.hybrid_command(name="unlock", description="Unlock channel")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context):
        assert ctx.guild and isinstance(ctx.channel, discord.TextChannel)
        ow = ctx.channel.overwrites_for(ctx.guild.default_role)
        ow.send_messages = None
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=ow)
        await ctx.send(embed=E.success("Unlocked", "Everyone can speak again."))

    @commands.hybrid_command(name="nick", description="Set nickname")
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx: commands.Context, member: discord.Member, *, nickname: str = ""):
        ok, why = await can_act(ctx, member)
        if not ok:
            await ctx.send(embed=E.error("Can't rename", why), ephemeral=True)
            return
        await member.edit(nick=nickname[:32] or None, reason=str(ctx.author))
        await ctx.send(embed=E.success("Nickname", f"{member.mention} → `{nickname or 'reset'}`"))


async def setup(bot: commands.Bot):
    await bot.add_cog(Cleanup(bot))
