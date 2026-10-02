"""XP + levels. Passive earn in bot.py, commands for rank/leaderboard."""

from __future__ import annotations

import discord
from discord.ext import commands

from core import embeds as E, db


class Leveling(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="level", description="Your level")
    async def level(self, ctx: commands.Context, member: discord.Member | None = None):
        m = member or ctx.author
        assert ctx.guild
        row = await db.q("SELECT * FROM xp WHERE guild_id=? AND user_id=?", (str(ctx.guild.id), str(m.id)), one=True)  # type: ignore
        xp = int(row["xp"]) if row else 0
        lvl = int(row["level"]) if row else 0
        nxt = (lvl + 1) ** 2 * 100 - xp
        await ctx.send(embed=E.make(f"Level • {m.display_name}", f"lvl **{lvl}** • **{xp}** xp • `{nxt}` to next", guild=ctx.guild, thumb=m.display_avatar.url))  # type: ignore

    @commands.hybrid_command(name="rank", description="Your server rank")
    async def rank(self, ctx: commands.Context):
        assert ctx.guild
        rows = await db.q("SELECT user_id,xp FROM xp WHERE guild_id=? ORDER BY xp DESC LIMIT 100", (str(ctx.guild.id),), many=True)
        ids = [r["user_id"] for r in (rows or [])]
        try:
            pos = ids.index(str(ctx.author.id)) + 1
            await ctx.send(embed=E.make("Rank", f"You're **#{pos}** of `{len(ids)}` ranked.", guild=ctx.guild))
        except ValueError:
            await ctx.send(embed=E.info("Unranked", "Chat a bit to earn XP."))

    @commands.hybrid_command(name="xptop", description="XP leaderboard")
    async def xptop(self, ctx: commands.Context):
        assert ctx.guild
        rows = await db.q("SELECT user_id,xp,level FROM xp WHERE guild_id=? ORDER BY xp DESC LIMIT 10", (str(ctx.guild.id),), many=True)
        if not rows:
            await ctx.send(embed=E.info("Empty", "No XP yet. Just chat."))
            return
        desc = "\n".join(f"`{i+1}.` <@{r['user_id']}> — lvl **{r['level']}** ({r['xp']} xp)" for i, r in enumerate(rows))
        await ctx.send(embed=E.make("XP leaderboard", desc, guild=ctx.guild))

    @commands.hybrid_command(name="xpadd", description="Give XP (mod)")
    @commands.has_permissions(manage_guild=True)
    async def xpadd(self, ctx: commands.Context, member: discord.Member, amount: int):
        assert ctx.guild
        xp, lvl = await db.xp_add(ctx.guild.id, member.id, max(1, min(5000, amount)))
        await ctx.send(embed=E.success("XP added", f"{member.mention} → lvl **{lvl}** ({xp} xp)"))


async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))
