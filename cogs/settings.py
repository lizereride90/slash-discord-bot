"""Setup wizard + config surface + owner/dev tools."""

from __future__ import annotations

import time

import discord
from discord.ext import commands

import config
from core import embeds as E, db
from core.checks import owner_only


class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="setup", description="Interactive setup walkthrough (admin)")
    @commands.has_permissions(administrator=True)
    async def setup_cmd(self, ctx: commands.Context):
        steps = [
            "1. Decide prefix vs slash (both work already).",
            "2. Create `#mod-log` for reports/cases.",
            "3. `/automod on` to enable link/burst filter.",
            "4. `/ticketpanel` in #support.",
            "5. `/rolemenu` for self-roles.",
            "6. `/cclist` + `/ccadd` for custom cmds.",
        ]
        await ctx.send(embed=E.make("Slash • Setup", "\n".join(steps), guild=ctx.guild))

    @commands.command(name="config", description="Show guild config")
    @commands.has_permissions(manage_guild=True)
    async def config_cmd(self, ctx: commands.Context):
        assert ctx.guild
        rows = await db.q("SELECT key,val FROM kv WHERE guild_id=?", (str(ctx.guild.id),), many=True)
        ccs = await db.q("SELECT COUNT(*) c FROM custom_cmds WHERE guild_id=?", (str(ctx.guild.id),), one=True)
        kv = ", ".join(f"`{r['key']}={r['val']}`" for r in (rows or [])) or "defaults"
        await ctx.send(embed=E.make("Config", f"{kv}\nCustom cmds: **{(ccs or {}).get('c', 0)}**", guild=ctx.guild))

    @commands.command(name="afk", description="Set AFK status")
    async def afk(self, ctx: commands.Context, *, reason: str = "AFK"):
        assert ctx.guild
        await db.w("INSERT INTO kv(guild_id,key,val) VALUES(?, ?, ?) ON CONFLICT(guild_id,key) DO UPDATE SET val=?", (f"afk-{ctx.author.id}", "msg", reason[:200], reason[:200]))
        try:
            await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}"[:32])
        except Exception:
            pass
        await ctx.send(embed=E.success("AFK", reason[:200]))

    @commands.command(name="profile", description="Your Slash profile")
    async def profile(self, ctx: commands.Context, member: discord.Member | None = None):
        m = member or ctx.author
        assert ctx.guild
        xp = await db.q("SELECT * FROM xp WHERE guild_id=? AND user_id=?", (str(ctx.guild.id), str(m.id)), one=True)  # type: ignore
        ec = await db.econ_get(ctx.guild.id, m.id)  # type: ignore
        await ctx.send(
            embed=E.make(
                f"Profile • {m.display_name}",
                f"lvl **{(xp or {}).get('level', 0)}** • **{(xp or {}).get('xp', 0)}** xp\nwallet **{ec['wallet']}** • bank **{ec['bank']}**",
                guild=ctx.guild,
                thumb=m.display_avatar.url,  # type: ignore
            )
        )


class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="bstat", description="Bot stats (owner)")
    @owner_only()
    async def bstat(self, ctx: commands.Context):
        up = int(time.time() - self.bot.started_at)  # type: ignore
        await ctx.send(embed=E.make("Slash • Stats", f"guilds **{len(self.bot.guilds)}** • cmds **{len(list(self.bot.commands))}** • up `{up//3600}h {(up%3600)//60}m`", guild=ctx.guild))

    @commands.command(name="sync", description="Force slash resync (owner)")
    @owner_only()
    async def sync(self, ctx: commands.Context):
        s = await self.bot.tree.sync()
        await ctx.send(embed=E.success("Synced", f"`{len(s)}` commands."), ephemeral=True)

    @commands.command(name="reload", description="Reload a cog (owner)")
    @owner_only()
    async def reload(self, ctx: commands.Context, cog: str):
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
            await ctx.send(embed=E.success("Reloaded", f"`{cog}`"), ephemeral=True)
        except Exception as e:
            await ctx.send(embed=E.error("Failed", str(e)[:400]), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Settings(bot))
    await bot.add_cog(Dev(bot))
