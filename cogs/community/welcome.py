"""Welcome and goodbye messages with guild-scoped configuration."""

from __future__ import annotations

import discord
from discord.ext import commands

from core import db
from core.embeds import make, success, error


def _render(template: str, member: discord.Member, ping: bool = True) -> str:
    return (
        template.replace("{member}", member.mention if ping else member.display_name)
        .replace("{user}", member.display_name)
        .replace("{server}", member.guild.name)
        .replace("{count}", str(member.guild.member_count or 0))
    )[:1900]


class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _channel(self, guild: discord.Guild, key: str) -> discord.TextChannel | None:
        row = await db.q("SELECT val FROM kv WHERE guild_id=? AND key=?", (str(guild.id), key), one=True)
        if not row or not str(row["val"]).isdigit():
            return None
        channel = guild.get_channel(int(row["val"]))
        return channel if isinstance(channel, discord.TextChannel) else None

    async def _value(self, guild: discord.Guild, key: str, fallback: str) -> str:
        row = await db.q("SELECT val FROM kv WHERE guild_id=? AND key=?", (str(guild.id), key), one=True)
        return str(row["val"]) if row else fallback

    async def _flag(self, guild: discord.Guild, key: str, fallback: bool) -> bool:
        value = await self._value(guild, key, str(fallback).lower())
        return value.lower() == "true"

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = await self._channel(member.guild, "welcome_channel")
        if channel:
            text = await self._value(member.guild, "welcome_text", "Welcome {member} to {server}!")
            ping = await self._flag(member.guild, "welcome_ping", True)
            thumb = await self._value(member.guild, "welcome_thumbnail", member.display_avatar.url)
            await channel.send(embed=make("Welcome", _render(text, member, ping), guild=member.guild, thumb=thumb))
        role_row = await db.q("SELECT val FROM kv WHERE guild_id=? AND key='autorole'", (str(member.guild.id),), one=True)
        if role_row and str(role_row["val"]).isdigit():
            role = member.guild.get_role(int(role_row["val"]))
            if role and member.guild.me and role < member.guild.me.top_role:
                try:
                    await member.add_roles(role, reason="Slash autorole")
                except discord.HTTPException:
                    pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = await self._channel(member.guild, "goodbye_channel")
        if channel:
            text = await self._value(member.guild, "goodbye_text", "{user} left {server}.")
            ping = await self._flag(member.guild, "goodbye_ping", False)
            thumb = await self._value(member.guild, "goodbye_thumbnail", "")
            await channel.send(embed=make("Goodbye", _render(text, member, ping), guild=member.guild, thumb=thumb or None))

    @commands.hybrid_command(name="welcome", description="Configure welcome channel, message, thumbnail, and ping")
    @commands.has_permissions(manage_guild=True)
    async def welcome(self, ctx: commands.Context, channel: discord.TextChannel | None = None, ping: bool = True, thumbnail: str | None = None, *, text: str = "Welcome {member} to {server}!"):
        channel = channel or ctx.channel
        assert ctx.guild
        values = [("welcome_channel", str(channel.id)), ("welcome_text", text[:1000]), ("welcome_ping", str(ping).lower())]
        if thumbnail is not None:
            values.append(("welcome_thumbnail", thumbnail[:500]))
        for key, value in values:
            await db.w("INSERT INTO kv(guild_id,key,val) VALUES(?,?,?) ON CONFLICT(guild_id,key) DO UPDATE SET val=?", (str(ctx.guild.id), key, value, value))
        await ctx.send(embed=success("Welcome configured", f"Channel: {channel.mention}\nPing: `{ping}`\nText: {text[:500]}"))

    @commands.hybrid_command(name="goodbye", description="Configure goodbye channel, message, thumbnail, and ping")
    @commands.has_permissions(manage_guild=True)
    async def goodbye(self, ctx: commands.Context, channel: discord.TextChannel | None = None, ping: bool = False, thumbnail: str | None = None, *, text: str = "{user} left {server}."):
        channel = channel or ctx.channel
        assert ctx.guild
        values = [("goodbye_channel", str(channel.id)), ("goodbye_text", text[:1000]), ("goodbye_ping", str(ping).lower())]
        if thumbnail is not None:
            values.append(("goodbye_thumbnail", thumbnail[:500]))
        for key, value in values:
            await db.w("INSERT INTO kv(guild_id,key,val) VALUES(?,?,?) ON CONFLICT(guild_id,key) DO UPDATE SET val=?", (str(ctx.guild.id), key, value, value))
        await ctx.send(embed=success("Goodbye configured", f"Channel: {channel.mention}\nPing: `{ping}`\nText: {text[:500]}"))

    @commands.hybrid_command(name="welcometest", description="Preview the current welcome message")
    @commands.has_permissions(manage_guild=True)
    async def welcome_test(self, ctx: commands.Context, member: discord.Member | None = None):
        member = member or ctx.author  # type: ignore
        text = await self._value(ctx.guild, "welcome_text", "Welcome {member} to {server}!")  # type: ignore
        ping = await self._flag(ctx.guild, "welcome_ping", True)  # type: ignore
        thumb = await self._value(ctx.guild, "welcome_thumbnail", member.display_avatar.url)
        await ctx.send(embed=make("Welcome preview", _render(text, member, ping), guild=ctx.guild, thumb=thumb))  # type: ignore
        assert ctx.guild
        await db.w("INSERT INTO kv(guild_id,key,val) VALUES(?,?,?) ON CONFLICT(guild_id,key) DO UPDATE SET val=?", (str(ctx.guild.id), "goodbye_text", text[:1000], text[:1000]))
        await ctx.send(embed=success("Goodbye text", "Saved."))

    @commands.hybrid_command(name="autorole", description="Set automatic join role")
    @commands.has_permissions(manage_roles=True)
    async def autorole(self, ctx: commands.Context, role: discord.Role | None = None):
        assert ctx.guild
        if role and ctx.guild.me and role >= ctx.guild.me.top_role:
            await ctx.send(embed=error("Role too high", "Move the role below my highest role."), ephemeral=True)
            return
        value = str(role.id) if role else "off"
        await db.w("INSERT INTO kv(guild_id,key,val) VALUES(?,?,?) ON CONFLICT(guild_id,key) DO UPDATE SET val=?", (str(ctx.guild.id), "autorole", value, value))
        await ctx.send(embed=success("Autorole", role.mention if role else "off"))


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
