"""Structured logging for Slash. Thin wrapper so cogs do `log.info(...)`."""

from __future__ import annotations

import logging
import os

_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def get(name: str = "slash") -> logging.Logger:
    lg = logging.getLogger(name)
    if not lg.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s", "%H:%M:%S"))
        lg.addHandler(h)
    lg.setLevel(getattr(logging, _LEVEL, logging.INFO))
    return lg


log = get()
