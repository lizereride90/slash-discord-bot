"""Polls, suggestions, reports — community input loop."""

from __future__ import annotations

import discord
from discord.ext import commands

from core import embeds as E


class Polls(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="poll", description="Yes/no poll")
    @commands.has_permissions(manage_messages=True)
    async def poll(self, ctx: commands.Context, *, question: str):
        m = await ctx.send(embed=E.make("Poll", question[:1500], guild=ctx.guild, footer=str(ctx.author)))
        for e in ("✅", "❌"):
            try:
                await m.add_reaction(e)
            except Exception:
                pass

    @commands.hybrid_command(name="votepoll", description="Multi-option poll (up to 5, | separated)")
    async def votepoll(self, ctx: commands.Context, question: str, *, options: str):
        opts = [o.strip() for o in options.split("|") if o.strip()][:5]
        if len(opts) < 2:
            await ctx.send(embed=E.error("Need options", "Use `a | b | c`."), ephemeral=True)
            return
        emo = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        desc = "\n".join(f"{emo[i]} {o}" for i, o in enumerate(opts))
        m = await ctx.send(embed=E.make(f"Vote: {question[:200]}", desc, guild=ctx.guild))
        for i in range(len(opts)):
            try:
                await m.add_reaction(emo[i])
            except Exception:
                pass

    @commands.hybrid_command(name="suggest", description="Submit a suggestion")
    async def suggest(self, ctx: commands.Context, *, idea: str):
        e = E.make("Suggestion", idea[:1500], guild=ctx.guild, footer=f"by {ctx.author}")
        m = await ctx.send(embed=e)
        for r in ("👍", "👎"):
            try:
                await m.add_reaction(r)
            except Exception:
                pass

    @commands.hybrid_command(name="report", description="Report a user to staff")
    async def report(self, ctx: commands.Context, member: discord.Member, *, reason: str):
        await ctx.send(embed=E.success("Reported", f"Staff will review {member.mention}. Thanks."), ephemeral=True)
        # best-effort: ping modlog channel named mod-log
        try:
            ch = discord.utils.get(ctx.guild.text_channels, name="mod-log")  # type: ignore
            if ch:
                await ch.send(embed=E.make("Report", f"{ctx.author.mention} reported {member.mention}\n{reason[:1000]}", guild=ctx.guild))
        except Exception:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Polls(bot))
