"""Moderation business logic separate from Discord I/O, so it's testable."""

from __future__ import annotations


def should_block_invite(content: str, is_staff: bool) -> bool:
    if is_staff:
        return False
    t = content.lower()
    return "discord.gg/" in t or "discord.com/invite/" in t


def burst_hit(stamps: list[float], now: float, limit: int = 5, window: float = 8.0) -> bool:
    fresh = [s for s in stamps if now - s < window]
    fresh.append(now)
    return len(fresh) >= limit


def case_label(cid: int) -> str:
    return f"CASE-{int(cid):06d}"
