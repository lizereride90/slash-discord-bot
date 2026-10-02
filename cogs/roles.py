"""Roles: self-roles via buttons, temp-ish assignment, bulk info."""

from __future__ import annotations

import discord
from discord.ext import commands

from core import embeds as E


class RoleView(discord.ui.View):
    def __init__(self, roles: list[discord.Role]):
        super().__init__(timeout=180)
        for r in roles[:5]:
            btn = discord.ui.Button(label=r.name[:80], style=discord.ButtonStyle.secondary, custom_id=f"slash:role:{r.id}")
            btn.callback = self._make_cb(r)  # type: ignore
            self.add_item(btn)

    def _make_cb(self, role: discord.Role):
        async def cb(interaction: discord.Interaction):
            assert isinstance(interaction.user, discord.Member)
            try:
                if role in interaction.user.roles:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message(f"Removed `{role.name}`.", ephemeral=True)
                else:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message(f"Added `{role.name}`.", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("I can't manage that role (hierarchy?).", ephemeral=True)

        return cb


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="rolemenu", description="Button role menu (up to 5 roles)")
    @commands.has_permissions(manage_roles=True)
    async def menu(self, ctx: commands.Context, r1: discord.Role, r2: discord.Role | None = None, r3: discord.Role | None = None):
        roles = [r for r in (r1, r2, r3) if r]
        await ctx.send(embed=E.make("Pick roles", "Tap to toggle.", guild=ctx.guild), view=RoleView(roles))

    @commands.hybrid_command(name="roleadd", description="Give a role")
    @commands.has_permissions(manage_roles=True)
    async def add(self, ctx: commands.Context, member: discord.Member, role: discord.Role):
        try:
            await member.add_roles(role, reason=str(ctx.author))
            await ctx.send(embed=E.success("Role added", f"{member.mention} + `{role.name}`"))
        except discord.Forbidden:
            await ctx.send(embed=E.error("Forbidden", "Role is above me or I lack perms."), ephemeral=True)

    @commands.hybrid_command(name="roledel", description="Remove a role")
    @commands.has_permissions(manage_roles=True)
    async def delete(self, ctx: commands.Context, member: discord.Member, role: discord.Role):
        await member.remove_roles(role, reason=str(ctx.author))
        await ctx.send(embed=E.success("Role removed", f"{member.mention} − `{role.name}`"))

    @commands.hybrid_command(name="roleinfo", description="About a role")
    async def info(self, ctx: commands.Context, role: discord.Role):
        await ctx.send(embed=E.make(f"Role • {role.name}", f"`{role.id}` • {len(role.members)} members • mentionable: {role.mentionable}", guild=ctx.guild, color=role.colour.value or 0x7C5CFF))

    @commands.hybrid_command(name="rolelist", description="Members with a role")
    async def list(self, ctx: commands.Context, role: discord.Role):
        names = ", ".join(m.mention for m in role.members[:30]) or "nobody"
        await ctx.send(embed=E.make(f"Role • {role.name} ({len(role.members)})", names, guild=ctx.guild))


async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))
