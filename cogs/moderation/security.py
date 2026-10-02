"""Server protection controls for moderators."""

from __future__ import annotations

import discord
from discord.ext import commands

from core import db
from core.embeds import error, success, warning


class Security(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="lockdown", description="Lock this channel for non-staff")
    @commands.has_permissions(manage_channels=True)
    async def lockdown(self, ctx: commands.Context):
        assert ctx.guild and isinstance(ctx.channel, discord.TextChannel)
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Lockdown by {ctx.author}")
        await ctx.send(embed=warning("Lockdown active", "Members cannot send messages in this channel."))

    @commands.hybrid_command(name="unlockdown", description="Remove this channel lockdown")
    @commands.has_permissions(manage_channels=True)
    async def unlockdown(self, ctx: commands.Context):
        assert ctx.guild and isinstance(ctx.channel, discord.TextChannel)
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Unlockdown by {ctx.author}")
        await ctx.send(embed=success("Lockdown removed", "Members can send messages again."))

    @commands.hybrid_command(name="quarantine", description="Remove a member's roles and isolate them")
    @commands.has_permissions(moderate_members=True)
    async def quarantine(self, ctx: commands.Context, member: discord.Member, *, reason: str = "under review"):
        assert ctx.guild
        if member == ctx.guild.owner or member == ctx.guild.me:
            await ctx.send(embed=error("Invalid target", "That member cannot be quarantined."), ephemeral=True)
            return
        role = discord.utils.get(ctx.guild.roles, name="Quarantine")
        if role is None:
            role = await ctx.guild.create_role(name="Quarantine", reason="Slash quarantine setup")
        if ctx.guild.me and role >= ctx.guild.me.top_role:
            await ctx.send(embed=error("Role hierarchy", "Move Quarantine below my highest role."), ephemeral=True)
            return
        removable = [r for r in member.roles if r != ctx.guild.default_role and r < ctx.guild.me.top_role] if ctx.guild.me else []
        if removable:
            await member.remove_roles(*removable, reason=f"Quarantine: {reason}"[:500])
        await member.add_roles(role, reason=f"Quarantine: {reason}"[:500])
        await ctx.send(embed=warning("Member quarantined", f"{member.mention}\nReason: {reason[:500]}"))

    @commands.hybrid_command(name="unquarantine", description="Release a member from quarantine")
    @commands.has_permissions(moderate_members=True)
    async def unquarantine(self, ctx: commands.Context, member: discord.Member):
        assert ctx.guild
        role = discord.utils.get(ctx.guild.roles, name="Quarantine")
        if not role or role not in member.roles:
            await ctx.send(embed=error("Not quarantined", f"{member.mention} has no Quarantine role."), ephemeral=True)
            return
        await member.remove_roles(role, reason=f"Unquarantine by {ctx.author}")
        await ctx.send(embed=success("Released", f"{member.mention} is no longer quarantined."))

    @commands.hybrid_command(name="modlog", description="Set the moderation audit channel")
    @commands.has_permissions(manage_guild=True)
    async def modlog(self, ctx: commands.Context, channel: discord.TextChannel | None = None):
        assert ctx.guild
        channel = channel or ctx.channel
        value = str(channel.id)
        await db.w("INSERT INTO kv(guild_id,key,val) VALUES(?,?,?) ON CONFLICT(guild_id,key) DO UPDATE SET val=?", (str(ctx.guild.id), "audit_channel", value, value))
        await ctx.send(embed=success("Moderation log", channel.mention))

    @commands.hybrid_command(name="announce", description="Send a staff announcement to a channel")
    @commands.has_permissions(manage_guild=True)
    async def announce(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str):
        await channel.send(embed=warning("Announcement", message[:3500], guild=ctx.guild, footer=f"by {ctx.author}"))
        await ctx.send(embed=success("Sent", f"Announcement posted in {channel.mention}."), ephemeral=True)

    @commands.hybrid_command(name="slowmodeall", description="Apply slowmode to every text channel")
    @commands.has_permissions(administrator=True)
    async def slowmode_all(self, ctx: commands.Context, seconds: int):
        assert ctx.guild
        seconds = max(0, min(21600, seconds))
        changed = 0
        for channel in ctx.guild.text_channels:
            try:
                await channel.edit(slowmode_delay=seconds, reason=f"Server slowmode by {ctx.author}")
                changed += 1
            except discord.HTTPException:
                continue
        await ctx.send(embed=success("Server slowmode", f"Updated `{changed}` channels to `{seconds}s`."))


async def setup(bot: commands.Bot):
    await bot.add_cog(Security(bot))
