"""Find commands that need a real implementation review.

This is intentionally strict: numbered/generated names cannot be called
production quality merely because they register successfully.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


BAD_NAME = re.compile(r"^(?:num|text|srv|mod|fun)\d+$")


def main() -> int:
    catalog = json.loads(Path("commands/catalog.json").read_text())
    flagged = [row for row in catalog if BAD_NAME.fullmatch(row["name"])]
    print(f"catalog actions: {len(catalog)}")
    print(f"flagged generated-style names: {len(flagged)}")
    for row in flagged[:20]:
        print(f"- {row['name']}: {row.get('category', 'unknown')}")
    if flagged:
        print("QUALITY FAIL: generated-style commands require replacement or removal")
        return 1
    print("QUALITY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
