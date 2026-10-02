"""Tickets: panel + open/close/transcript-lite. File-free, channel-based."""

from __future__ import annotations

import discord
from discord.ext import commands

from core import embeds as E


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open ticket", style=discord.ButtonStyle.primary, custom_id="slash:ticket_open")
    async def open(self, interaction: discord.Interaction, _b: discord.ui.Button):
        assert interaction.guild
        name = f"ticket-{interaction.user.name}".lower().replace(" ", "-")[:90]
        existing = discord.utils.get(interaction.guild.text_channels, name=name)
        if existing:
            await interaction.response.send_message(f"You already have {existing.mention}.", ephemeral=True)
            return
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        ch = await interaction.guild.create_text_channel(name, overwrites=overwrites, reason="Slash ticket")
        await ch.send(f"{interaction.user.mention} staff will be with you shortly.")
        await interaction.response.send_message(f"Opened {ch.mention}.", ephemeral=True)


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="ticketpanel", description="Post ticket panel (mod)")
    @commands.has_permissions(manage_channels=True)
    async def panel(self, ctx: commands.Context):
        await ctx.send(embed=E.make("Support", "Need help? Open a ticket.", guild=ctx.guild), view=TicketView())

    @commands.hybrid_command(name="ticketclose", description="Close this ticket")
    async def close(self, ctx: commands.Context):
        assert isinstance(ctx.channel, discord.TextChannel)
        if not ctx.channel.name.startswith("ticket-"):
            await ctx.send(embed=E.error("Not a ticket", "Run this inside a ticket channel."), ephemeral=True)
            return
        await ctx.send(embed=E.warning("Closing", "Archiving in 3s…"))
        import asyncio

        await asyncio.sleep(3)
        try:
            await ctx.channel.delete(reason=f"closed by {ctx.author}")
        except Exception:
            pass

    @commands.hybrid_command(name="ticketadd", description="Add user to ticket")
    @commands.has_permissions(manage_channels=True)
    async def add(self, ctx: commands.Context, member: discord.Member):
        assert isinstance(ctx.channel, discord.TextChannel)
        await ctx.channel.set_permissions(member, view_channel=True, send_messages=True)
        await ctx.send(embed=E.success("Added", f"{member.mention} can see this ticket."))

    @commands.hybrid_command(name="ticketlog", description="Save recent messages as log")
    @commands.has_permissions(manage_channels=True)
    async def log(self, ctx: commands.Context, limit: int = 50):
        assert isinstance(ctx.channel, discord.TextChannel)
        lines = []
        async for m in ctx.channel.history(limit=max(1, min(200, limit))):
            lines.append(f"{m.author}: {m.content[:200]}")
        txt = "\n".join(reversed(lines))[:1800] or "(empty)"
        await ctx.send(embed=E.make("Ticket log", f"```{txt}```", guild=ctx.guild))

    @commands.hybrid_command(name="ticketclaim", description="Claim this ticket for yourself")
    @commands.has_permissions(manage_channels=True)
    async def claim(self, ctx: commands.Context):
        assert isinstance(ctx.channel, discord.TextChannel)
        if not ctx.channel.name.startswith("ticket-"):
            await ctx.send(embed=E.error("Not a ticket", "Run this inside a ticket channel."), ephemeral=True)
            return
        await ctx.channel.edit(topic=f"Claimed by {ctx.author} ({ctx.author.id})")
        await ctx.send(embed=E.success("Ticket claimed", f"{ctx.author.mention} is handling this ticket."))

    @commands.hybrid_command(name="ticketunclaim", description="Remove the current ticket claim")
    @commands.has_permissions(manage_channels=True)
    async def unclaim(self, ctx: commands.Context):
        assert isinstance(ctx.channel, discord.TextChannel)
        if not ctx.channel.name.startswith("ticket-"):
            await ctx.send(embed=E.error("Not a ticket", "Run this inside a ticket channel."), ephemeral=True)
            return
        await ctx.channel.edit(topic=None)
        await ctx.send(embed=E.success("Ticket unclaimed", "The ticket is available to staff again."))

    @commands.hybrid_command(name="ticketrename", description="Rename this ticket")
    @commands.has_permissions(manage_channels=True)
    async def rename(self, ctx: commands.Context, *, name: str):
        assert isinstance(ctx.channel, discord.TextChannel)
        if not ctx.channel.name.startswith("ticket-"):
            await ctx.send(embed=E.error("Not a ticket", "Run this inside a ticket channel."), ephemeral=True)
            return
        clean = "ticket-" + "-".join(name.lower().split())
        await ctx.channel.edit(name=clean[:100])
        await ctx.send(embed=E.success("Ticket renamed", f"`{clean[:100]}`"))

    @commands.hybrid_command(name="ticketpriority", description="Set ticket priority in its topic")
    @commands.has_permissions(manage_channels=True)
    async def priority(self, ctx: commands.Context, level: str):
        assert isinstance(ctx.channel, discord.TextChannel)
        level = level.lower()
        if level not in {"low", "normal", "high", "urgent"}:
            await ctx.send(embed=E.error("Invalid priority", "Use low, normal, high, or urgent."), ephemeral=True)
            return
        await ctx.channel.edit(topic=f"Priority: {level}")
        await ctx.send(embed=E.success("Priority updated", f"`{level}`"))


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
