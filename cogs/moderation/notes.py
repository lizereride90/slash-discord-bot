"""Staff notes — per-user private notes for mods."""

from __future__ import annotations

import discord
from discord.ext import commands

from core import embeds as E, db


class Notes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="noteadd", description="Add staff note (mod)")
    @commands.has_permissions(moderate_members=True)
    async def add(self, ctx: commands.Context, member: discord.Member, *, text: str):
        assert ctx.guild
        await db.w(
            "CREATE TABLE IF NOT EXISTS notes(g TEXT,u TEXT,t TEXT,m TEXT,ts INTEGER)"
        )
        import time

        await db.w("INSERT INTO notes VALUES(?,?,?,?,?)", (str(ctx.guild.id), str(member.id), text[:800], str(ctx.author), int(time.time())))
        await ctx.send(embed=E.success("Noted", f"Note saved for {member.mention}."))

    @commands.hybrid_command(name="notes", description="View staff notes (mod)")
    @commands.has_permissions(moderate_members=True)
    async def view(self, ctx: commands.Context, member: discord.Member):
        assert ctx.guild
        await db.w("CREATE TABLE IF NOT EXISTS notes(g TEXT,u TEXT,t TEXT,m TEXT,ts INTEGER)")
        rows = await db.q("SELECT * FROM notes WHERE g=? AND u=? ORDER BY ts DESC LIMIT 10", (str(ctx.guild.id), str(member.id)), many=True)
        desc = "\n".join(f"• {r['t'][:150]} — {r['m']}" for r in (rows or [])) or "No notes."
        await ctx.send(embed=E.make(f"Notes • {member}", desc, guild=ctx.guild))

    @commands.hybrid_command(name="notedel", description="Clear notes (mod)")
    @commands.has_permissions(moderate_members=True)
    async def clear(self, ctx: commands.Context, member: discord.Member):
        assert ctx.guild
        await db.w("DELETE FROM notes WHERE g=? AND u=?", (str(ctx.guild.id), str(member.id)))
        await ctx.send(embed=E.success("Cleared", f"Notes cleared for {member.mention}."))


async def setup(bot: commands.Bot):
    await bot.add_cog(Notes(bot))
