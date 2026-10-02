"""Unit tests for pure service logic (no Discord connection needed)."""

from services.moderation_service import burst_hit, case_label, should_block_invite
from services.economy_service import can_claim


def test_invite_block():
    assert should_block_invite("join discord.gg/abc", False) is True
    assert should_block_invite("join discord.gg/abc", True) is False
    assert should_block_invite("hello", False) is False


def test_burst():
    assert burst_hit([0, 1, 2, 3], 4, limit=5, window=8) is True
    assert burst_hit([0], 100, limit=5, window=8) is False


def test_case_label():
    assert case_label(3) == "CASE-000003"


def test_claim_cd():
    assert can_claim(0, 90000, 86400) is True
    assert can_claim(89999, 90000, 86400) is False
