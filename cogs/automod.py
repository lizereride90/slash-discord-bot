"""Automod-lite + custom commands + reminders. Real, no fake scans."""

from __future__ import annotations

import asyncio
import re
import time

import discord
from discord.ext import commands

from core import embeds as E, db

_bad = ["discord.gg/", "http://", ".xyz", ".ru/"]
_caps_re = re.compile(r"[A-Z\s]{12,}")


class AutoMod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._hits: dict[tuple[int, int], list[float]] = {}

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot or not msg.guild:
            return
        if msg.author.guild_permissions.manage_messages:
            return
        try:
            row = await db.q("SELECT val FROM kv WHERE guild_id=? AND key='automod'", (str(msg.guild.id),), one=True)
        except Exception:
            row = None
        if not row or row.get("val") != "on":
            return
        t = msg.content.lower()
        if any(b in t for b in _bad) and len(t) < 400:
            # links are the #1 phishing vector; delete + warn once
            try:
                await msg.delete()
                await msg.channel.send(f"{msg.author.mention} links are filtered here.", delete_after=6)
            except Exception:
                pass
            return
        # burst: 5 msgs in 8s
        key = (msg.guild.id, msg.author.id)
        now = time.monotonic()
        arr = [x for x in self._hits.get(key, []) if now - x < 8] + [now]
        self._hits[key] = arr
        if len(arr) >= 5:
            self._hits[key] = []
            try:
                await msg.channel.send(f"{msg.author.mention} slow down.", delete_after=6)
            except Exception:
                pass

    @commands.hybrid_command(name="automod", description="Toggle link/burst filter (admin)")
    @commands.has_permissions(administrator=True)
    async def toggle(self, ctx: commands.Context, mode: str):
        mode = mode.lower()
        if mode not in ("on", "off"):
            await ctx.send(embed=E.error("Bad mode", "Use `on` or `off`."), ephemeral=True)
            return
        assert ctx.guild
        await db.w("INSERT INTO kv(guild_id,key,val) VALUES(?, 'automod', ?) ON CONFLICT(guild_id,key) DO UPDATE SET val=?", (str(ctx.guild.id), mode, mode))
        await ctx.send(embed=E.success("Automod", f"`{mode}`"))

    @commands.hybrid_command(name="ccadd", description="Add custom command (admin): !name text")
    @commands.has_permissions(manage_guild=True)
    async def add(self, ctx: commands.Context, name: str, *, text: str):
        assert ctx.guild
        n = name.lower().lstrip("!")[:30]
        if not n.isalnum():
            await ctx.send(embed=E.error("Bad name", "Letters/numbers only."), ephemeral=True)
            return
        await db.w("INSERT INTO custom_cmds(guild_id,name,text) VALUES(?,?,?) ON CONFLICT(guild_id,name) DO UPDATE SET text=?", (str(ctx.guild.id), n, text[:1500], text[:1500]))
        await ctx.send(embed=E.success("Custom command", f"`{config_PREFIX()}{n}` → saved."))

    @commands.hybrid_command(name="ccdel", description="Delete custom command (admin)")
    @commands.has_permissions(manage_guild=True)
    async def delete(self, ctx: commands.Context, name: str):
        assert ctx.guild
        await db.w("DELETE FROM custom_cmds WHERE guild_id=? AND name=?", (str(ctx.guild.id), name.lower().lstrip("!")))
        await ctx.send(embed=E.success("Deleted", f"`{name}` removed."))

    @commands.hybrid_command(name="cclist", description="List custom commands")
    async def list(self, ctx: commands.Context):
        assert ctx.guild
        rows = await db.q("SELECT name FROM custom_cmds WHERE guild_id=? LIMIT 50", (str(ctx.guild.id),), many=True)
        names = ", ".join(f"`{r['name']}`" for r in (rows or [])) or "none yet"
        await ctx.send(embed=E.make("Custom commands", names, guild=ctx.guild))

    @commands.hybrid_command(name="remind", description="Remind in N minutes")
    async def remind(self, ctx: commands.Context, minutes: float, *, text: str):
        if minutes <= 0 or minutes > 10080:
            await ctx.send(embed=E.error("Bad time", "1 min – 1 week."), ephemeral=True)
            return
        await ctx.send(embed=E.success("Reminder set", f"In `{minutes}m`: {text[:200]}"))
        await asyncio.sleep(minutes * 60)
        try:
            await ctx.send(f"⏰ {ctx.author.mention}: {text[:1500]}")
        except Exception:
            pass


def config_PREFIX():  # tiny local to avoid circular import in message
    try:
        import config as _c

        return _c.PREFIX
    except Exception:
        return "!"


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoMod(bot))
