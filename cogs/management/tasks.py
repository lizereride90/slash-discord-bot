"""Natural-language staff task runner with an explicit, safe action allow-list.

This is deliberately not an eval/agent shell. A prompt is converted into a
small plan, shown to the moderator, and mutating plans require confirmation.
"""

from __future__ import annotations

import re

import discord
from discord.ext import commands

from core import embeds as E


class TaskConfirm(discord.ui.View):
    def __init__(self, author_id: int, execute):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.execute_plan = execute

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the task requester can confirm this.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Run task", style=discord.ButtonStyle.danger)
    async def run(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        await interaction.response.edit_message(view=self)
        try:
            result = await self.execute_plan()
            await interaction.followup.send(embed=E.success("Task complete", result), ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send(embed=E.error("Discord permission denied", "Check my role and channel permissions."), ephemeral=True)
        except discord.HTTPException as exc:
            await interaction.followup.send(embed=E.error("Discord rejected the task", str(exc)[:300]), ephemeral=True)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, _button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(embed=E.info("Task cancelled", "No changes were made."), view=None)


class Tasks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _plan(self, ctx: commands.Context, prompt: str):
        """Return (description, mutating, coroutine) or a useful rejection."""
        assert ctx.guild
        text = prompt.lower().strip()
        guild = ctx.guild

        if any(word in text for word in ("delete all", "nuke", "wipe server", "ban everyone")):
            return None

        if "revamp" in text or "server layout" in text or "server setup" in text:
            layout = {
                "INFORMATION": ["rules", "announcements"],
                "COMMUNITY": ["general", "media", "suggestions"],
                "SUPPORT": ["help", "tickets"],
                "STAFF": ["staff-chat", "mod-log"],
            }

            async def revamp():
                created_categories = 0
                created_channels = 0
                for category_name, channel_names in layout.items():
                    category = discord.utils.find(lambda c: c.name.lower() == category_name.lower(), guild.categories)
                    if category is None:
                        category = await guild.create_category(category_name, reason=f"Slash task by {ctx.author}")
                        created_categories += 1
                    for channel_name in channel_names:
                        if discord.utils.find(lambda c: c.name.lower() == channel_name.lower() and c.category_id == category.id, guild.text_channels):
                            continue
                        await guild.create_text_channel(channel_name, category=category, reason=f"Slash task by {ctx.author}")
                        created_channels += 1
                return f"Created `{created_categories}` categories and `{created_channels}` channels. Existing channels were preserved."

            return "Create a safe standard layout: Information, Community, Support, and Staff categories with useful channels", True, revamp

        match = re.search(r"(?:create|make|add)\s+(?:a\s+)?category(?:\s+called|\s+named)?\s+([\w -]{2,50})", prompt, re.IGNORECASE)
        if match:
            category_name = match.group(1).strip()[:90]

            async def create_category():
                existing = discord.utils.find(lambda c: c.name.lower() == category_name.lower(), guild.categories)
                if existing:
                    return f"Category already exists: {existing.name}."
                category = await guild.create_category(category_name, reason=f"Slash task by {ctx.author}")
                return f"Created category `{category.name}`."

            return f"Create category `{category_name}`", True, create_category

        match = re.search(r"(?:create|make|add)\s+(?:a\s+)?(?:text\s+)?channel(?:\s+called|\s+named)?\s+([\w-]{2,90})(?:\s+in\s+([\w -]{2,50}))?", prompt, re.IGNORECASE)
        if match:
            channel_name = match.group(1).strip().lower()
            category_name = match.group(2).strip() if match.group(2) else ""

            async def create_channel():
                category = discord.utils.find(lambda c: c.name.lower() == category_name.lower(), guild.categories) if category_name else None
                channel = await guild.create_text_channel(channel_name, category=category, reason=f"Slash task by {ctx.author}")
                return f"Created {channel.mention}."

            suffix = f" in `{category_name}`" if category_name else ""
            return f"Create text channel `{channel_name}`{suffix}", True, create_channel

        match = re.search(r"(?:move|position)\s+(?:category|channel)\s+([\w -]{2,50})\s+(?:to|at)\s+(\d+)", prompt, re.IGNORECASE)
        if match:
            target_name, raw_position = match.group(1).strip(), match.group(2)
            position = max(0, min(500, int(raw_position)))
            target = discord.utils.find(lambda c: c.name.lower() == target_name.lower(), guild.channels)
            if target is None:
                return None

            async def move_target():
                await target.edit(position=position, reason=f"Slash task by {ctx.author}")
                return f"Moved `{target.name}` to position `{position}`."

            return f"Move `{target.name}` to position `{position}`", True, move_target

        match = re.search(r"(?:webhook|hook)\s+(?:in|for)\s+#?([\w-]{2,90})(?:\s+(?:called|named)\s+([\w -]{2,70}))?", prompt, re.IGNORECASE)
        if match:
            channel_name, webhook_name = match.group(1), (match.group(2) or "Slash Integration").strip()[:80]
            channel = discord.utils.find(lambda c: c.name.lower() == channel_name.lower(), guild.text_channels)
            if channel is None:
                return None

            async def create_webhook():
                hook = await channel.create_webhook(name=webhook_name, reason=f"Slash task by {ctx.author}")
                return f"Created webhook `{hook.name}` in {channel.mention}. The webhook URL is intentionally not displayed."

            return f"Create webhook `{webhook_name}` in `#{channel.name}`", True, create_webhook

        if ("private" in text or "public" in text) and "channel" in text:
            mode = "private" if "private" in text else "public"
            match = re.search(r"channel\s+#?([\w-]{2,90})", prompt, re.IGNORECASE)
            channel = discord.utils.find(lambda c: c.name.lower() == match.group(1).lower(), guild.text_channels) if match else None
            if channel is None:
                return None

            async def set_visibility():
                overwrite = channel.overwrites_for(guild.default_role)
                overwrite.view_channel = mode == "public"
                await channel.set_permissions(guild.default_role, overwrite=overwrite, reason=f"Slash task by {ctx.author}")
                return f"`#{channel.name}` is now `{mode}` for @everyone."

            return f"Make `#{channel.name}` {mode}", True, set_visibility

        if "member" in text and any(word in text for word in ("list", "show", "see", "count")):
            async def members():
                humans = sum(not m.bot for m in guild.members)
                bots = sum(m.bot for m in guild.members)
                return f"Members: `{guild.member_count or 0}` total, `{humans}` humans, `{bots}` bots."

            return "Read member statistics (no changes)", False, members

        if "role" in text and any(word in text for word in ("list", "show", "see")):
            async def roles():
                names = ", ".join(role.name for role in guild.roles[-25:]) or "none"
                return f"Roles: {names}"

            return "Read the server role list (no changes)", False, roles

        if "log" in text or "audit" in text:
            async def audit():
                lines = []
                async for entry in guild.audit_logs(limit=10):
                    lines.append(f"{entry.action.name}: {entry.user} — {entry.target}")
                return "\n".join(lines)[:1800] or "No recent audit entries."

            return "Read the 10 most recent audit-log entries (no changes)", False, audit

        match = re.search(r"(?:create|make|add)\s+(?:a\s+)?role(?:\s+called|\s+named)?\s+([\w -]{2,50})", prompt, re.IGNORECASE)
        if match:
            role_name = match.group(1).strip()[:80]

            async def create_role():
                role = await guild.create_role(name=role_name, reason=f"Slash task by {ctx.author}")
                return f"Created {role.mention}."

            return f"Create the role `{role_name}`", True, create_role

        if "lockdown" in text or "lock down" in text:
            async def lockdown():
                changed = 0
                for channel in guild.text_channels:
                    overwrite = channel.overwrites_for(guild.default_role)
                    overwrite.send_messages = False
                    try:
                        await channel.set_permissions(guild.default_role, overwrite=overwrite, reason=f"Slash task by {ctx.author}")
                        changed += 1
                    except discord.HTTPException:
                        continue
                return f"Locked `{changed}` text channels."

            return "Lock all text channels for @everyone", True, lockdown

        return None

    @commands.hybrid_command(name="task", description="Plan a safe staff task from plain language")
    @commands.has_permissions(manage_guild=True)
    async def task(self, ctx: commands.Context, *, prompt: str):
        if not ctx.guild:
            await ctx.send(embed=E.error("Server only", "Tasks need a server context."), ephemeral=True)
            return
        planned = self._plan(ctx, prompt)
        if not planned:
            await ctx.send(embed=E.error("Task not supported", "Try: `list members`, `list roles`, `check audit logs`, `create role called Helpers`, or `lockdown`."), ephemeral=True)
            return
        description, mutating, execute = planned
        if not mutating:
            await ctx.send(embed=E.info("Task result", await execute()))
            return
        await ctx.send(embed=E.warning("Confirm staff task", f"{description}.\n\nThis will change server state. Press **Run task** to continue."), view=TaskConfirm(ctx.author.id, execute))


async def setup(bot: commands.Bot):
    await bot.add_cog(Tasks(bot))
