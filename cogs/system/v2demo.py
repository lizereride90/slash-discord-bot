"""Components V2 showcase: Container + Section + buttons."""

from __future__ import annotations

import discord
from discord.ext import commands


class V2Demo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="v2demo", description="Show Components V2 card")
    async def v2demo(self, ctx: commands.Context):
        try:
            view = discord.ui.LayoutView()
            box = discord.ui.Container(accent_colour=discord.Colour(0x7C5CFF))
            box.add_item(discord.ui.TextDisplay("## Slash • V2\nCompact card. Prefix + slash both work."))
            view.add_item(box)
            await ctx.send(view=view)
        except Exception:
            from core import embeds as E

            await ctx.send(embed=E.make("Slash • V2", "V2 not renderable here — fallback embed.", guild=ctx.guild))


async def setup(bot: commands.Bot):
    await bot.add_cog(V2Demo(bot))
