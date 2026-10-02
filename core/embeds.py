"""Slash embed + Components V2 helpers.

Every reply goes through here so the bot looks consistent:
compact title, short description, predictable footer, safe truncation.
Supports classic embeds everywhere, and V2 containers where the
channel/client can render them.
"""

from __future__ import annotations

import discord
from discord import ui

import config

MAX_DESC = 3800


class SlashEmbed(discord.Embed):
    """EmbedFactory marker used by the context adapter to render V2 cards."""

    slash_v2 = True


def _footer(text: str | None, guild: discord.Guild | None) -> str:
    base = config.BRAND
    if guild:
        base += f" • {guild.name}"
    if text:
        base += f" • {text}"
    return base[:100]


def _chop(s: str, limit: int = MAX_DESC) -> str:
    s = str(s or "")
    if len(s) > limit:
        return s[: limit - 3] + "..."
    return s


def make(
    title: str,
    desc: str = "",
    color: int = config.ACCENT,
    guild: discord.Guild | None = None,
    footer: str | None = None,
    thumb: str | None = None,
    image: str | None = None,
    timestamp: bool = True,
    fields: list[tuple[str, str, bool]] | None = None,
) -> discord.Embed:
    e = SlashEmbed(
        title=title[:250],
        description=_chop(desc),
        color=color,
        timestamp=discord.utils.utcnow() if timestamp else None,
    )
    for name, val, inline in fields or []:
        e.add_field(name=str(name)[:250], value=str(val)[:1000] or "—", inline=inline)
    e.set_footer(text=_footer(footer, guild))
    if thumb:
        try:
            e.set_thumbnail(url=thumb)
        except Exception:
            pass
    if image:
        try:
            e.set_image(url=image)
        except Exception:
            pass
    return e


def view_from_embed(embed: discord.Embed) -> ui.LayoutView:
    """Render a factory embed as a compact Components V2 card."""
    color = embed.color.value if embed.color else config.ACCENT
    lines = [f"## {embed.title or config.BRAND}"]
    if embed.description:
        lines.append(embed.description)
    for field in embed.fields:
        lines.append(f"**{field.name}**\n{field.value}")
    card = ui.Container(ui.TextDisplay("\n\n".join(lines)[:3900]), accent_colour=discord.Colour(color))
    if embed.footer and embed.footer.text:
        card.add_item(ui.TextDisplay(f"-# {embed.footer.text}"))
    view = ui.LayoutView()
    view.add_item(card)
    return view


def success(title: str, desc: str = "", **kw) -> discord.Embed:
    return make(f"✓ {title}", desc, color=config.SUCCESS, **kw)


def error(title: str, desc: str = "", **kw) -> discord.Embed:
    # error id style: helps users report, devs grep logs
    return make(f"✕ {title}", desc, color=config.ERROR, **kw)


def warning(title: str, desc: str = "", **kw) -> discord.Embed:
    return make(f"! {title}", desc, color=config.WARNING, **kw)


def info(title: str, desc: str = "", **kw) -> discord.Embed:
    return make(title, desc, color=config.INFO, **kw)


def loading(text: str = "Working…") -> discord.Embed:
    return make("Slash", text, color=config.DARK, timestamp=False)


def mod_embed(
    action: str,
    target: discord.User | discord.Member | str,
    mod: discord.User | discord.Member,
    reason: str,
    guild: discord.Guild | None = None,
    extra: list[tuple[str, str, bool]] | None = None,
    case_id: str | None = None,
) -> discord.Embed:
    fields: list[tuple[str, str, bool]] = [
        ("Action", str(action), True),
        ("Target", f"{target} ({getattr(target, 'id', '?')})", True),
        ("Moderator", f"{mod}", True),
        ("Reason", str(reason)[:800], False),
    ]
    if case_id:
        fields.append(("Case", case_id, True))
    if extra:
        fields.extend(extra)
    g = guild or getattr(mod, "guild", None)
    return make("Slash • Moderation", "", color=config.ACCENT, guild=g, fields=fields)


def v2_container(title: str, desc: str, accent: int = config.ACCENT) -> ui.Container:
    """Build a Components V2 container. Falls back gracefully if the
    installed discord.py doesn't render it in some context."""
    header = ui.TextDisplay(f"## {title}\n{desc[:3500]}")
    c = ui.Container(header, accent_colour=discord.Colour(accent))
    return c


class V2Paginator(ui.LayoutView):
    """Paginated Components V2 card for long discovery/help responses."""

    def __init__(self, pages: list[tuple[str, str]], author_id: int, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.author_id = author_id
        self.index = 0
        self.card = ui.Container(accent_colour=discord.Colour(config.ACCENT))
        self.row = ui.ActionRow()
        self.prev = ui.Button(label="Previous", style=discord.ButtonStyle.secondary, custom_id="slash:v2:prev")
        self.page = ui.Button(label="1/1", style=discord.ButtonStyle.secondary, disabled=True, custom_id="slash:v2:page")
        self.next = ui.Button(label="Next", style=discord.ButtonStyle.primary, custom_id="slash:v2:next")
        self.prev.callback = self._previous
        self.next.callback = self._next
        self.row.add_item(self.prev)
        self.row.add_item(self.page)
        self.row.add_item(self.next)
        self.add_item(self.card)
        self.add_item(self.row)
        self._render()

    def _render(self) -> None:
        self.card.clear_items()
        title, body = self.pages[self.index]
        self.card.add_item(ui.TextDisplay(f"## {title}\n{body}"))
        self.prev.disabled = self.index == 0
        self.next.disabled = self.index == len(self.pages) - 1
        self.page.label = f"{self.index + 1}/{len(self.pages)}"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This menu belongs to someone else.", ephemeral=True)
            return False
        return True

    async def _update(self, interaction: discord.Interaction) -> None:
        self._render()
        await interaction.response.edit_message(view=self)

    async def _previous(self, interaction: discord.Interaction) -> None:
        self.index = max(0, self.index - 1)
        await self._update(interaction)

    async def _next(self, interaction: discord.Interaction) -> None:
        self.index = min(len(self.pages) - 1, self.index + 1)
        await self._update(interaction)


class Paginator(ui.View):
    """Simple embed paginator used by help / list commands."""

    def __init__(self, pages: list[discord.Embed], timeout: float = 120):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.idx = 0
        self._sync()

    def _sync(self):
        self.prev.disabled = self.idx <= 0
        self.next.disabled = self.idx >= len(self.pages) - 1
        self.label.label = f"{self.idx + 1}/{len(self.pages)}"

    async def _show(self, interaction: discord.Interaction):
        self._sync()
        await interaction.response.edit_message(embed=self.pages[self.idx], view=self)

    @ui.button(label="‹", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, _b: ui.Button):
        if self.idx > 0:
            self.idx -= 1
        await self._show(interaction)

    @ui.button(label="1/1", style=discord.ButtonStyle.secondary, disabled=True)
    async def label(self, interaction: discord.Interaction, _b: ui.Button):
        pass

    @ui.button(label="›", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, _b: ui.Button):
        if self.idx < len(self.pages) - 1:
            self.idx += 1
        await self._show(interaction)


class Confirm(ui.View):
    def __init__(self, author_id: int, timeout: float = 30):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.value: bool | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            try:
                await interaction.response.send_message("Not your confirm.", ephemeral=True)
            except Exception:
                pass
            return False
        return True

    @ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def yes(self, interaction: discord.Interaction, _b: ui.Button):
        self.value = True
        self.stop()
        try:
            await interaction.response.defer()
        except Exception:
            pass

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def no(self, interaction: discord.Interaction, _b: ui.Button):
        self.value = False
        self.stop()
        try:
            await interaction.response.defer()
        except Exception:
            pass
