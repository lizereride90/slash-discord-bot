"""Moderation — warns + cases. Part of cogs/moderation package."""

from __future__ import annotations

import discord
from discord.ext import commands

from core import embeds as E, db
from core.checks import can_act


class Warns(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="warn", description="Warn a member")
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "no reason"):
        ok, why = await can_act(ctx, member)
        if not ok:
            await ctx.send(embed=E.error("Can't warn", why), ephemeral=True)
            return
        n = await db.add_warn(ctx.guild.id, member.id, reason, str(ctx.author))  # type: ignore
        await ctx.send(embed=E.mod_embed("warn", member, ctx.author, reason, ctx.guild, [("Total", str(n), True)]))  # type: ignore

    @commands.hybrid_command(name="warnings", description="See warnings")
    @commands.has_permissions(moderate_members=True)
    async def warnings(self, ctx: commands.Context, member: discord.Member):
        rows = await db.get_warns(ctx.guild.id, member.id)  # type: ignore
        if not rows:
            await ctx.send(embed=E.success("Clean", f"{member.mention} has no warnings."))
            return
        desc = "\n".join(f"`{i+1}.` {r['reason'][:120]} — {r['mod']}" for i, r in enumerate(rows[:15]))
        await ctx.send(embed=E.make(f"Warnings • {member} ({len(rows)})", desc, guild=ctx.guild))

    @commands.hybrid_command(name="unwarn", description="Clear one warning by number")
    @commands.has_permissions(moderate_members=True)
    async def unwarn(self, ctx: commands.Context, member: discord.Member, index: int):
        rows = await db.get_warns(ctx.guild.id, member.id)  # type: ignore
        if not rows or index < 1 or index > len(rows):
            await ctx.send(embed=E.error("Bad index", "Check `/warnings`."), ephemeral=True)
            return
        await db.w("DELETE FROM warns WHERE rowid=?", (rows[index - 1]["rowid"],))
        await ctx.send(embed=E.success("Removed", f"Cleared warning `{index}` for {member.mention}."))

    @commands.hybrid_command(name="clearwarns", description="Clear all warnings")
    @commands.has_permissions(moderate_members=True)
    async def clearwarns(self, ctx: commands.Context, member: discord.Member):
        await db.clear_warns(ctx.guild.id, member.id)  # type: ignore
        await ctx.send(embed=E.success("Cleared", f"All warnings cleared for {member.mention}."))

    @commands.hybrid_command(name="case", description="Look up a mod case")
    @commands.has_permissions(moderate_members=True)
    async def case(self, ctx: commands.Context, case_id: str):
        num = "".join(c for c in case_id if c.isdigit())
        row = await db.q("SELECT * FROM cases WHERE id=? AND guild_id=?", (int(num or 0), str(ctx.guild.id)), one=True)  # type: ignore
        if not row:
            await ctx.send(embed=E.error("Not found", "No such case here."), ephemeral=True)
            return
        await ctx.send(embed=E.make(f"Case {case_id.upper()}", f"**{row['action']}** — {row['target']}\n{row['reason']}", guild=ctx.guild))

    @commands.hybrid_command(name="history", description="Mod history for a user")
    @commands.has_permissions(moderate_members=True)
    async def history(self, ctx: commands.Context, member: discord.Member):
        rows = await db.q("SELECT * FROM cases WHERE guild_id=? AND target LIKE ? ORDER BY id DESC LIMIT 15", (str(ctx.guild.id), f"%{member}%"), many=True)  # type: ignore
        warns = await db.get_warns(ctx.guild.id, member.id)  # type: ignore
        desc = "\n".join(f"`CASE-{r['id']:06d}` {r['action']} — {r['reason'][:80]}" for r in (rows or [])) or "No cases."
        await ctx.send(embed=E.make(f"History • {member}", f"{desc}\n\nWarnings: **{len(warns or [])}**", guild=ctx.guild))


async def setup(bot: commands.Bot):
    await bot.add_cog(Warns(bot))
