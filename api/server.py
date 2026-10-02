"""Small dashboard API with explicit token auth and real local data."""

from __future__ import annotations

try:
    from fastapi import FastAPI, Header
    from fastapi.responses import JSONResponse
except ImportError:  # api is optional, bot runs without it
    FastAPI = None  # type: ignore

import config
from core import db
import hmac
import re


def ok(data):
    return {"success": True, "data": data}


def err(code: str, msg: str, status: int = 400):
    from fastapi.responses import JSONResponse

    return JSONResponse({"success": False, "error": {"code": code, "message": msg}}, status_code=status)


def build():
    app = FastAPI(title="Slash Dashboard API")

    @app.get("/health")
    async def health():
        return ok({"bot": "slash", "database": "configured", "prefix": config.PREFIX})

    def authorized(authorization: str) -> bool:
        if not config.API_TOKEN or not authorization.startswith("Bearer "):
            return False
        return hmac.compare_digest(authorization[7:].strip(), config.API_TOKEN)

    @app.get("/guilds/{gid}/config")
    async def guild_config(gid: str, authorization: str = Header(default="")):
        if not re.fullmatch(r"[0-9]{15,21}", gid):
            return err("INVALID_GUILD", "guild id is invalid", 422)
        if not authorized(authorization):
            return err("NO_AUTH", "valid API token required", 401)
        await db.init()
        rows = await db.q("SELECT key,val FROM kv WHERE guild_id=?", (gid,), many=True)
        values = {row["key"]: row["val"] for row in (rows or [])}
        return ok({"guild": gid, "settings": values})

    return app


app = build() if FastAPI else None
