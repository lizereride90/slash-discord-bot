"""Info / help / discovery. The commands people actually type daily."""

from __future__ import annotations

import json
import os
import time

import discord
from discord.ext import commands

import config
from core import embeds as E

CATALOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "commands", "catalog.json")


async def build_catalog(bot: commands.Bot) -> None:
    rows = []
    for c in sorted(bot.commands, key=lambda c: c.name):
        try:
            cog_name = c.cog_name or "uncategorized"
            rows.append(
                {
                    "name": c.name,
                    "category": cog_name,
                    "description": (c.description or c.help or "")[:200],
                    "permissions": [],
                    "cooldown": 0,
                    "implemented": True,
                    "slash": getattr(c, "app_command", None) is not None,
                }
            )
        except Exception:
            continue
    # also tree slash cmds
    for c in bot.tree.get_commands():
        if not any(r["name"] == c.name for r in rows):
            rows.append({"name": c.name, "category": "slash", "description": (c.description or "")[:200], "permissions": [], "cooldown": 0, "implemented": True, "slash": True})
    os.makedirs(os.path.dirname(CATALOG_PATH), exist_ok=True)
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Latency + uptime")
    async def ping(self, ctx: commands.Context):
        ms = round(self.bot.latency * 1000)
        up = int(time.time() - self.bot.started_at)  # type: ignore
        h, r = divmod(up, 3600)
        m, s = divmod(r, 60)
        await ctx.send(embed=E.make("Slash • Ping", f"**{ms}ms** • up `{h}h {m}m {s}s`", guild=ctx.guild))

    @commands.hybrid_command(name="help", description="Browse commands")
    async def help(self, ctx: commands.Context, query: str | None = None):
        if not query:
            commands_list = sorted(self.bot.commands, key=lambda command: command.name)
            pages: list[tuple[str, str]] = []
            for start in range(0, len(commands_list), 18):
                chunk = commands_list[start : start + 18]
                lines = []
                for command in chunk:
                    slash = f"`/{command.name}`" if getattr(command, "app_command", None) else "prefix-only"
                    lines.append(f"`{config.PREFIX}{command.name}`  {slash}  — {command.description or 'No description'}")
                pages.append((f"Slash • Help ({len(commands_list)} commands)", "\n".join(lines)))
            view = E.V2Paginator(pages or [("Slash • Help", "No commands loaded.")], ctx.author.id)
            await ctx.send(view=view)
            return
        q = query.lower().strip()
        hit = discord.utils.find(lambda c: c.name == q, self.bot.commands)
        if not hit:
            await ctx.send(view=E.V2Paginator([("Not found", f"No command named `{q}`.")], ctx.author.id), ephemeral=True)
            return
        slash = f"/{hit.name}" if getattr(hit, "app_command", None) else "prefix-only"
        body = f"{hit.description or hit.help or 'No description'}\n\nUsage: `{config.PREFIX}{hit.name}` • `{slash}`"
        await ctx.send(view=E.V2Paginator([(f"Slash • {hit.name}", body[:3500])], ctx.author.id))

    @commands.hybrid_command(name="commands", description="Count + list commands")
    async def commands_cmd(self, ctx: commands.Context):
        commands_list = sorted(self.bot.commands, key=lambda command: command.name)
        pages = []
        for start in range(0, len(commands_list), 18):
            chunk = commands_list[start : start + 18]
            pages.append((f"Slash • Commands ({len(commands_list)})", "\n".join(f"`{c.name}` — {c.description or 'No description'}" for c in chunk)))
        await ctx.send(view=E.V2Paginator(pages or [("Slash • Commands", "No commands loaded.")], ctx.author.id))

    @commands.hybrid_command(name="search", description="Search commands by text")
    async def search(self, ctx: commands.Context, *, text: str):
        t = text.lower()
        hits = [c for c in self.bot.commands if t in c.name or t in (c.description or "").lower()][:25]
        if not hits:
            await ctx.send(embed=E.warning("No matches", f"Nothing for `{text}`."), ephemeral=True)
            return
        desc = "\n".join(f"`/{c.name}` — {c.description or ''}"[:120] for c in hits)
        await ctx.send(embed=E.make("Slash • Search", desc, guild=ctx.guild))

    @commands.hybrid_command(name="botinfo", description="About Slash")
    async def botinfo(self, ctx: commands.Context):
        b = self.bot
        e = E.make(
            "Slash • About",
            "All-in-one server toolkit. Prefix + slash, V2 UI, sane defaults.",
            guild=ctx.guild,
            thumb=b.user.display_avatar.url if b.user and b.user.display_avatar else None,
            fields=[
                ("Servers", str(len(b.guilds)), True),
                ("Users", str(sum((g.member_count or 0) for g in b.guilds)), True),
                ("Latency", f"{round(b.latency*1000)}ms", True),
                ("Commands", str(len(list(b.commands))), True),
                ("Prefix", config.PREFIX, True),
                ("discord.py", discord.__version__, True),
            ],
        )
        await ctx.send(embed=e)

    @commands.hybrid_command(name="userinfo", description="Inspect a member")
    async def userinfo(self, ctx: commands.Context, member: discord.Member | None = None):
        m = member or ctx.author  # type: ignore
        roles = " ".join(r.mention for r in m.roles[1:][:8]) or "none"  # type: ignore
        e = E.make(
            f"User • {m}",
            f"{m.mention} • `{m.id}`",
            guild=ctx.guild,
            thumb=m.display_avatar.url,
            fields=[
                ("Created", discord.utils.format_dt(m.created_at, "R"), True),
                ("Joined", discord.utils.format_dt(m.joined_at, "R") if m.joined_at else "?", True),  # type: ignore
                ("Roles", roles, False),
            ],
        )
        await ctx.send(embed=e)

    @commands.hybrid_command(name="serverinfo", description="Inspect this server")
    async def serverinfo(self, ctx: commands.Context):
        g = ctx.guild
        if not g:
            await ctx.send(embed=E.error("Server only", "Run this in a server."), ephemeral=True)
            return
        e = E.make(
            f"Server • {g.name}",
            f"`{g.id}` • owned by <@{g.owner_id}>",
            guild=g,
            thumb=g.icon.url if g.icon else None,
            fields=[
                ("Members", str(g.member_count), True),
                ("Channels", str(len(g.channels)), True),
                ("Roles", str(len(g.roles)), True),
                ("Boosts", str(g.premium_subscription_count or 0), True),
                ("Created", discord.utils.format_dt(g.created_at, "D"), True),
                ("Emojis", str(len(g.emojis)), True),
            ],
        )
        await ctx.send(embed=e)

    @commands.hybrid_command(name="avatar", description="Big avatar view")
    async def avatar(self, ctx: commands.Context, member: discord.Member | None = None):
        m = member or ctx.author
        await ctx.send(embed=E.make(f"Avatar • {m}", "", guild=ctx.guild, image=m.display_avatar.url))  # type: ignore

    @commands.hybrid_command(name="banner", description="Show a user's banner if set")
    async def banner(self, ctx: commands.Context, member: discord.Member | None = None):
        m = member or ctx.author
        try:
            u = await self.bot.fetch_user(m.id)  # type: ignore
            b = getattr(u, "banner", None)
            if b:
                await ctx.send(embed=E.make(f"Banner • {m}", "", guild=ctx.guild, image=b.url))
            else:
                await ctx.send(embed=E.info("No banner", f"{m.mention} has no banner set."))  # type: ignore
        except Exception:
            await ctx.send(embed=E.error("Failed", "Couldn't fetch banner."), ephemeral=True)

    @commands.hybrid_command(name="membercount", description="Member stats")
    async def membercount(self, ctx: commands.Context):
        g = ctx.guild
        if not g:
            return
        total = g.member_count or 0
        bots = sum(1 for m in g.members if m.bot)
        await ctx.send(embed=E.make("Members", f"**{total}** total • **{total-bots}** humans • **{bots}** bots", guild=g))

    @commands.hybrid_command(name="roles", description="List server roles")
    async def roles_cmd(self, ctx: commands.Context):
        g = ctx.guild
        if not g:
            return
        top = [r.mention for r in sorted(g.roles, key=lambda r: r.position, reverse=True)[:25]]
        await ctx.send(embed=E.make(f"Roles ({len(g.roles)})", " ".join(top) or "none", guild=g))

    @commands.hybrid_command(name="channels", description="List channels")
    async def channels_cmd(self, ctx: commands.Context):
        g = ctx.guild
        if not g:
            return
        txt = "\n".join(f"{'#' if isinstance(c, discord.TextChannel) else '🔊'} {c.mention}" for c in g.channels[:25])
        await ctx.send(embed=E.make(f"Channels ({len(g.channels)})", txt or "none", guild=g))

    @commands.hybrid_command(name="emojis", description="List custom emojis")
    async def emojis(self, ctx: commands.Context):
        g = ctx.guild
        if not g:
            return
        es = [str(e) for e in g.emojis[:40]]
        await ctx.send(embed=E.make(f"Emojis ({len(g.emojis)})", " ".join(es) or "No custom emojis.", guild=g))

    @commands.hybrid_command(name="inviteinfo", description="Show channel invite stats")
    async def inviteinfo(self, ctx: commands.Context):
        if not ctx.guild:
            return
        try:
            invs = await ctx.guild.invites()
            top = sorted(invs, key=lambda i: (i.uses or 0), reverse=True)[:10]
            desc = "\n".join(f"`{i.code}` by {i.inviter} — {i.uses} uses" for i in top) or "No invites."
            await ctx.send(embed=E.make("Invites", desc, guild=ctx.guild))
        except discord.Forbidden:
            await ctx.send(embed=E.error("No permission", "I need `Manage Server` to read invites."), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Info(bot))
