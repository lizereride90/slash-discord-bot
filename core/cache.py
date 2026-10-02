"""Tiny TTL cache for guild config / hot settings. No unbounded growth."""

from __future__ import annotations

import time

_MAX = 2000
_store: dict[str, tuple[float, object]] = {}


def get(key: str):
    hit = _store.get(key)
    if not hit:
        return None
    exp, val = hit
    if exp < time.monotonic():
        _store.pop(key, None)
        return None
    return val


def set(key: str, val: object, ttl: float = 60.0) -> None:
    if len(_store) > _MAX:
        # drop oldest quarter — cheap, no lru bookkeeping
        for k in list(_store)[: _MAX // 4]:
            _store.pop(k, None)
    _store[key] = (time.monotonic() + ttl, val)


def bust(prefix: str) -> None:
    for k in [k for k in _store if k.startswith(prefix)]:
        _store.pop(k, None)
