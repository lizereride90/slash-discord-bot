"""Small audit logger for moderation-sensitive Discord events."""

from __future__ import annotations

import discord
from discord.ext import commands

from core import db
from core.embeds import make


class Audit(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send(self, guild: discord.Guild, title: str, description: str):
        row = await db.q("SELECT val FROM kv WHERE guild_id=? AND key='audit_channel'", (str(guild.id),), one=True)
        if not row or not str(row["val"]).isdigit():
            return
        channel = guild.get_channel(int(row["val"]))
        if isinstance(channel, discord.TextChannel):
            try:
                await channel.send(embed=make(title, description, guild=guild))
            except discord.HTTPException:
                pass

    @commands.hybrid_command(name="auditchannel", description="Set audit log channel")
    @commands.has_permissions(manage_guild=True)
    async def audit_channel(self, ctx: commands.Context, channel: discord.TextChannel | None = None):
        assert ctx.guild
        channel = channel or ctx.channel
        await db.w("INSERT INTO kv(guild_id,key,val) VALUES(?,?,?) ON CONFLICT(guild_id,key) DO UPDATE SET val=?", (str(ctx.guild.id), "audit_channel", str(channel.id), str(channel.id)))
        await ctx.send(f"Audit logs → {channel.mention}")

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        await self._send(guild, "Member banned", f"{user} (`{user.id}`)")

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        await self._send(guild, "Member unbanned", f"{user} (`{user.id}`)")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self._send(channel.guild, "Channel deleted", f"`{channel.name}` (`{channel.id}`)")


async def setup(bot: commands.Bot):
    await bot.add_cog(Audit(bot))
