"""Production command registration guard."""

import re
from pathlib import Path


def test_command_count():
    files = list(Path("cogs").rglob("*.py"))
    found = []
    for f in files:
        found += re.findall(r"hybrid_command\(name=\"([^\"]+)\"", f.read_text())
    assert len(found) >= 75, f"production surface unexpectedly small: {len(found)} commands"
    assert len(set(found)) == len(found), "duplicate command names"
