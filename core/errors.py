"""User-safe errors with internal IDs. Never leak tracebacks to chat."""

from __future__ import annotations

import os
import time


def eid() -> str:
    return f"ERR-{os.getpid():04X}{int(time.time())%65536:04X}"
