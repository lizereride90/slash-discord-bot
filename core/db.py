"""SQLite storage for Slash. Zero-config local file, optional
postgres later via DATABASE_URL. Keeps tables small and indexed."""

from __future__ import annotations

import aiosqlite
import os
import time

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS warns(
  guild_id TEXT, user_id TEXT, reason TEXT, mod TEXT, ts INTEGER);
CREATE INDEX IF NOT EXISTS ix_warns_gu ON warns(guild_id, user_id);
CREATE TABLE IF NOT EXISTS cases(
  id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id TEXT, target TEXT,
  mod TEXT, action TEXT, reason TEXT, ts INTEGER, expires INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS economy(
  guild_id TEXT, user_id TEXT, wallet INTEGER DEFAULT 0, bank INTEGER DEFAULT 0,
  last_daily INTEGER DEFAULT 0, last_weekly INTEGER DEFAULT 0,
  PRIMARY KEY(guild_id, user_id));
CREATE TABLE IF NOT EXISTS xp(
  guild_id TEXT, user_id TEXT, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 0,
  PRIMARY KEY(guild_id, user_id));
CREATE TABLE IF NOT EXISTS reminders(
  id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id TEXT, user_id TEXT,
  channel_id TEXT, text TEXT, due INTEGER);
CREATE TABLE IF NOT EXISTS custom_cmds(
  guild_id TEXT, name TEXT, text TEXT, PRIMARY KEY(guild_id, name));
CREATE TABLE IF NOT EXISTS kv(
  guild_id TEXT, key TEXT, val TEXT, PRIMARY KEY(guild_id, key));
"""


async def init() -> None:
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def q(sql: str, args: tuple = (), one: bool = False, many: bool = False):
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(sql, args)
        if one:
            r = await cur.fetchone()
            await cur.close()
            return dict(r) if r else None
        if many:
            rows = await cur.fetchall()
            await cur.close()
            return [dict(r) for r in rows]
        await cur.close()
        return None


async def w(sql: str, args: tuple = ()):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(sql, args)
        await db.commit()


# small wrappers the cogs actually use

async def add_warn(gid: int, uid: int, reason: str, mod: str) -> int:
    await w(
        "INSERT INTO warns(guild_id,user_id,reason,mod,ts) VALUES(?,?,?,?,?)",
        (str(gid), str(uid), reason[:500], str(mod)[:100], int(time.time())),
    )
    r = await q(
        "SELECT COUNT(*) c FROM warns WHERE guild_id=? AND user_id=?",
        (str(gid), str(uid)),
        one=True,
    )
    return int(r["c"]) if r else 1


async def get_warns(gid: int, uid: int):
    return await q(
        "SELECT rowid,* FROM warns WHERE guild_id=? AND user_id=? ORDER BY ts DESC LIMIT 25",
        (str(gid), str(uid)),
        many=True,
    )


async def clear_warns(gid: int, uid: int):
    await w("DELETE FROM warns WHERE guild_id=? AND user_id=?", (str(gid), str(uid)))


async def new_case(gid: int, target: str, mod: str, action: str, reason: str, expires: int = 0) -> str:
    async with aiosqlite.connect(config.DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO cases(guild_id,target,mod,action,reason,ts,expires) VALUES(?,?,?,?,?,?,?)",
            (str(gid), target[:100], str(mod)[:100], action[:30], reason[:800], int(time.time()), expires),
        )
        await db.commit()
        cid = cur.lastrowid
    return f"CASE-{int(cid or 0):06d}"


async def econ_get(gid: int, uid: int):
    r = await q("SELECT * FROM economy WHERE guild_id=? AND user_id=?", (str(gid), str(uid)), one=True)
    if not r:
        await w("INSERT OR IGNORE INTO economy(guild_id,user_id) VALUES(?,?)", (str(gid), str(uid)))
        return {"wallet": 0, "bank": 0, "last_daily": 0, "last_weekly": 0}
    return r


async def econ_add(gid: int, uid: int, wallet: int = 0, bank: int = 0):
    await w(
        "INSERT INTO economy(guild_id,user_id,wallet,bank) VALUES(?,?,?,?) "
        "ON CONFLICT(guild_id,user_id) DO UPDATE SET wallet=wallet+?, bank=bank+?",
        (str(gid), str(uid), wallet, bank, wallet, bank),
    )


async def econ_set_cool(gid: int, uid: int, field: str):
    await w(f"UPDATE economy SET {field}=? WHERE guild_id=? AND user_id=?", (int(time.time()), str(gid), str(uid)))


async def xp_add(gid: int, uid: int, amount: int) -> tuple[int, int]:
    cur = await q("SELECT * FROM xp WHERE guild_id=? AND user_id=?", (str(gid), str(uid)), one=True)
    xp = int(cur["xp"] + amount) if cur else amount
    lvl = int((xp / 100) ** 0.5)
    await w(
        "INSERT INTO xp(guild_id,user_id,xp,level) VALUES(?,?,?,?) "
        "ON CONFLICT(guild_id,user_id) DO UPDATE SET xp=?, level=?",
        (str(gid), str(uid), xp, lvl, xp, lvl),
    )
    return xp, lvl
