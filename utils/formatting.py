"""Shared text formatting."""

from __future__ import annotations


def chop(s: str, n: int = 1500) -> str:
    s = str(s or "")
    return s if len(s) <= n else s[: n - 3] + "..."


def coins(n: int) -> str:
    return f"{int(n):,}"
