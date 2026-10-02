"""Central config for Slash. Keeps env parsing in one place."""

from __future__ import annotations

import os


def _load_dotenv(path: str = ".env") -> None:
    # tiny loader so we don't depend on python-dotenv for local runs,
    # but if it's installed it also works. human habit: support both.
    base = os.path.join(os.path.dirname(__file__), path)
    if not os.path.exists(base):
        base = path
    if not os.path.exists(base):
        return
    with open(base, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("\"'")
            if k and k not in os.environ:
                os.environ[k] = v


_load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
PREFIX = os.getenv("PREFIX", "!").strip() or "!"
CLIENT_ID = os.getenv("CLIENT_ID", "").strip()
GUILD_ID = os.getenv("GUILD_ID", "").strip()
API_TOKEN = os.getenv("API_TOKEN", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

_owner_raw = os.getenv("OWNER_IDS", "")
OWNER_IDS = set()
for part in _owner_raw.replace(";", ",").split(","):
    part = part.strip()
    if part.isdigit():
        OWNER_IDS.add(int(part))

# brand
BRAND = "Slash"
ACCENT = 0x7C5CFF  # slash violet
SUCCESS = 0x2DC770
ERROR = 0xE5484D
WARNING = 0xF5A524
INFO = 0x3E9BFF
DARK = 0x1A1B22

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "slash.db")
