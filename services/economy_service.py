"""Economy rules: payouts, costs, cooldown windows."""

from __future__ import annotations

DAILY_MIN, DAILY_MAX = 100, 250
WEEKLY_MIN, WEEKLY_MAX = 400, 800
WORK_MIN, WORK_MAX = 20, 80
DAILY_CD = 86400
WEEKLY_CD = 604800


def can_claim(last: int, now: int, cd: int) -> bool:
    return (now - int(last or 0)) >= cd
