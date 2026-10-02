"""Channels + voice + threads. All permission-guarded."""

from __future__ import annotations

import discord
from discord.ext import commands

from core import embeds as E


class Channels(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="mkchannel", description="Create a text channel (mod)")
    @commands.has_permissions(manage_channels=True)
    async def mk(self, ctx: commands.Context, name: str):
        assert ctx.guild
        ch = await ctx.guild.create_text_channel(name[:90].lower().replace(" ", "-"))
        await ctx.send(embed=E.success("Created", f"{ch.mention}"))

    @commands.hybrid_command(name="mkvoice", description="Create a voice channel (mod)")
    @commands.has_permissions(manage_channels=True)
    async def mkv(self, ctx: commands.Context, name: str):
        assert ctx.guild
        ch = await ctx.guild.create_voice_channel(name[:90])
        await ctx.send(embed=E.success("Created", f"`{ch.name}`"))

    @commands.hybrid_command(name="rename", description="Rename this channel (mod)")
    @commands.has_permissions(manage_channels=True)
    async def rename(self, ctx: commands.Context, *, name: str):
        assert isinstance(ctx.channel, discord.abc.GuildChannel)
        await ctx.channel.edit(name=name[:90].lower().replace(" ", "-"))
        await ctx.send(embed=E.success("Renamed", f"→ `{name}`"))

    @commands.hybrid_command(name="topic", description="Set channel topic (mod)")
    @commands.has_permissions(manage_channels=True)
    async def topic(self, ctx: commands.Context, *, text: str):
        assert isinstance(ctx.channel, discord.TextChannel)
        await ctx.channel.edit(topic=text[:900])
        await ctx.send(embed=E.success("Topic set", text[:300]))

    @commands.hybrid_command(name="vmove", description="Move member to your voice (mod)")
    @commands.has_permissions(move_members=True)
    async def vmove(self, ctx: commands.Context, member: discord.Member):
        author = ctx.author
        assert isinstance(author, discord.Member)
        if not author.voice or not author.voice.channel:
            await ctx.send(embed=E.error("Join voice", "Join a voice channel first."), ephemeral=True)
            return
        try:
            await member.move_to(author.voice.channel)
            await ctx.send(embed=E.success("Moved", f"{member.mention} → `{author.voice.channel.name}`"))
        except discord.HTTPException:
            await ctx.send(embed=E.error("Failed", "Can't move them."), ephemeral=True)

    @commands.command(name="vlock", description="Voice limit set (mod)")
    @commands.has_permissions(manage_channels=True)
    async def vlock(self, ctx: commands.Context, limit: int):
        a = ctx.author
        assert isinstance(a, discord.Member)
        if not a.voice or not a.voice.channel:
            await ctx.send(embed=E.error("Join voice", "Join voice first."), ephemeral=True)
            return
        await a.voice.channel.edit(user_limit=max(0, min(99, limit)))
        await ctx.send(embed=E.success("Voice limit", f"`{limit}`"))

    @commands.command(name="thread", description="Start a thread here")
    @commands.has_permissions(create_public_threads=True)
    async def thread(self, ctx: commands.Context, *, name: str):
        assert isinstance(ctx.channel, discord.TextChannel)
        t = await ctx.channel.create_thread(name=name[:90], auto_archive_duration=1440)
        await ctx.send(embed=E.success("Thread", f"{t.mention} created."))

    @commands.command(name="archive", description="Archive this thread")
    async def archive(self, ctx: commands.Context):
        if isinstance(ctx.channel, discord.Thread):
            await ctx.channel.edit(archived=True)
            await ctx.send("Archived.")
        else:
            await ctx.send(embed=E.error("Not a thread", "Run inside a thread."), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Channels(bot))
