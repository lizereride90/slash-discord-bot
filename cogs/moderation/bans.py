"""Moderation — kick/ban/timeout. Part of cogs/moderation package."""

from __future__ import annotations

import datetime

import discord
from discord.ext import commands

from core import embeds as E, db
from core.checks import can_act


class Bans(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _case(self, ctx: commands.Context, target: str, action: str, reason: str) -> str:
        try:
            return await db.new_case(ctx.guild.id, target, str(ctx.author), action, reason)  # type: ignore
        except Exception:
            return "CASE-??????"

    @commands.hybrid_command(name="kick", description="Kick a member")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "no reason"):
        ok, why = await can_act(ctx, member)
        if not ok:
            await ctx.send(embed=E.error("Can't kick", why), ephemeral=True)
            return
        cid = await self._case(ctx, str(member), "kick", reason)
        await member.kick(reason=f"{ctx.author}: {reason}"[:500])
        await ctx.send(embed=E.mod_embed("kick", member, ctx.author, reason, ctx.guild, None, cid))  # type: ignore

    @commands.hybrid_command(name="ban", description="Ban a member")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, delete_days: int = 0, *, reason: str = "no reason"):
        ok, why = await can_act(ctx, member)
        if not ok:
            await ctx.send(embed=E.error("Can't ban", why), ephemeral=True)
            return
        cid = await self._case(ctx, str(member), "ban", reason)
        await member.ban(reason=f"{ctx.author}: {reason}"[:500], delete_message_days=max(0, min(7, delete_days)))
        await ctx.send(embed=E.mod_embed("ban", member, ctx.author, reason, ctx.guild, None, cid))  # type: ignore

    @commands.hybrid_command(name="unban", description="Unban by ID or name")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, *, user: str):
        assert ctx.guild
        target = None
        async for b in ctx.guild.bans():
            if str(b.user.id) == user.strip() or str(b.user) == user.strip():
                target = b.user
                break
        if not target:
            await ctx.send(embed=E.error("Not found", "No matching ban."), ephemeral=True)
            return
        await ctx.guild.unban(target, reason=str(ctx.author))
        await ctx.send(embed=E.success("Unbanned", f"**{target}** can rejoin."))

    @commands.hybrid_command(name="softban", description="Ban + instant unban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def softban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "no reason"):
        ok, why = await can_act(ctx, member)
        if not ok:
            await ctx.send(embed=E.error("Can't softban", why), ephemeral=True)
            return
        await member.ban(reason=f"{ctx.author}: {reason}"[:500], delete_message_days=1)
        await ctx.guild.unban(member)  # type: ignore
        await ctx.send(embed=E.mod_embed("softban", member, ctx.author, reason, ctx.guild))  # type: ignore

    @commands.hybrid_command(name="timeout", description="Timeout (minutes)")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def timeout(self, ctx: commands.Context, member: discord.Member, minutes: int, *, reason: str = "no reason"):
        ok, why = await can_act(ctx, member)
        if not ok:
            await ctx.send(embed=E.error("Can't timeout", why), ephemeral=True)
            return
        minutes = max(1, min(40320, minutes))
        await member.timeout(discord.utils.utcnow() + datetime.timedelta(minutes=minutes), reason=reason[:500])
        await ctx.send(embed=E.mod_embed("timeout", member, ctx.author, f"{reason} • {minutes}m", ctx.guild))  # type: ignore

    @commands.hybrid_command(name="untimeout", description="Lift a timeout")
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx: commands.Context, member: discord.Member):
        await member.timeout(None, reason=str(ctx.author))
        await ctx.send(embed=E.success("Untimed out", f"{member.mention} can speak again."))


async def setup(bot: commands.Bot):
    await bot.add_cog(Bans(bot))
