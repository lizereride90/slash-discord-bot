"""Owner dev tools shim — real cog lives in settings.py too, this keeps import stable."""
from discord.ext import commands


class DevStub(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


async def setup(bot: commands.Bot):
    # settings.py already registers Dev; keep this as no-op so extension load succeeds
    await bot.add_cog(DevStub(bot))
