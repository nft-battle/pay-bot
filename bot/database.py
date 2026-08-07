from datetime import datetime
from pathlib import Path

import aiosqlite

from .config import DATABASE_URL, DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT DEFAULT '',
    amount REAL DEFAULT 0,
    asset TEXT DEFAULT 'USDT',
    status TEXT DEFAULT 'pending',
    invoice_id INTEGER,
    pay_url TEXT DEFAULT '',
    comment TEXT DEFAULT '',
    created_at TEXT DEFAULT '',
    paid_at TEXT DEFAULT ''
)
"""

PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS payments (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username TEXT DEFAULT '',
    amount REAL DEFAULT 0,
    asset TEXT DEFAULT 'USDT',
    status TEXT DEFAULT 'pending',
    invoice_id BIGINT,
    pay_url TEXT DEFAULT '',
    comment TEXT DEFAULT '',
    created_at TEXT DEFAULT '',
    paid_at TEXT DEFAULT ''
)
"""


def _now() -> str:
    return datetime.now().strftime("%d.%m.%Y %H:%M")


class _Adapter:
    async def init(self) -> None: ...
    async def execute(self, sql: str, params: tuple = ()) -> None: ...
    async def fetchall(self, sql: str, params: tuple = ()) -> list[dict]: ...
    async def fetchone(self, sql: str, params: tuple = ()) -> dict | None: ...
    async def insert(self, sql: str, params: tuple = ()) -> int: ...
    async def close(self) -> None: ...


class _SqliteAdapter(_Adapter):
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    async def _connect(self):
        db = await aiosqlite.connect(self.path)
        db.row_factory = aiosqlite.Row
        return db

    async def init(self) -> None:
        db = await self._connect()
        try:
            await db.execute(SCHEMA)
            await db.commit()
        finally:
            await db.close()

    async def _run(self, sql: str, params: tuple = (), *, want_id: bool = False):
        db = await self._connect()
        try:
            cur = await db.execute(sql, params)
            if sql.strip().upper().startswith("SELECT"):
                rows = [dict(r) for r in await cur.fetchall()]
                return rows
            await db.commit()
            return cur.lastrowid if want_id else None
        finally:
            await db.close()

    async def execute(self, sql, params=()):
        await self._run(sql, params)

    async def fetchall(self, sql, params=()):
        return await self._run(sql, params) or []

    async def fetchone(self, sql, params=()):
        rows = await self._run(sql, params)
        return rows[0] if rows else None

    async def insert(self, sql, params=()):
        return await self._run(sql, params, want_id=True)

    async def close(self) -> None:
        pass


class _PgAdapter(_Adapter):
    def __init__(self, url: str):
        import asyncpg

        self.url = url
        self.asyncpg = asyncpg
        self._pool = None

    def _sql(self, sql: str) -> str:
        out, i = [], 0
        for ch in sql:
            if ch == "?":
                i += 1
                out.append(f"${i}")
            else:
                out.append(ch)
        return "".join(out)

    async def _pool_get(self):
        if self._pool is None:
            self._pool = await self.asyncpg.create_pool(
                dsn=self.url,
                min_size=1,
                max_size=5,
                statement_cache_size=0,
            )
        return self._pool

    async def init(self) -> None:
        pool = await self._pool_get()
        async with pool.acquire() as con:
            await con.execute(PG_SCHEMA)

    async def execute(self, sql, params=()):
        pool = await self._pool_get()
        async with pool.acquire() as con:
            await con.execute(self._sql(sql), *params)

    async def fetchall(self, sql, params=()):
        pool = await self._pool_get()
        async with pool.acquire() as con:
            rows = await con.fetch(self._sql(sql), *params)
        return [dict(r) for r in rows]

    async def fetchone(self, sql, params=()):
        rows = await self.fetchall(sql, params)
        return rows[0] if rows else None

    async def insert(self, sql, params=()):
        sql = self._sql(sql)
        if sql.strip().upper().startswith("INSERT") and "returning" not in sql.lower():
            sql += " RETURNING id"
        pool = await self._pool_get()
        async with pool.acquire() as con:
            return await con.fetchval(sql, *params)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None


class Database:
    def __init__(self, url: str | None = None, path: str = DB_PATH):
        self._url = url or DATABASE_URL
        self.adapter: _Adapter = (
            _PgAdapter(self._url) if self._url else _SqliteAdapter(path)
        )

    @property
    def is_pg(self) -> bool:
        return isinstance(self.adapter, _PgAdapter)

    async def init(self) -> None:
        await self.adapter.init()

    async def close(self) -> None:
        await self.adapter.close()

    async def create_payment(
        self, user_id: int, username: str, amount: float, asset: str
    ) -> int:
        return await self.adapter.insert(
            "INSERT INTO payments(user_id, username, amount, asset, created_at) "
            "VALUES(?,?,?,?,?)",
            (user_id, username or "", amount, asset, _now()),
        )

    async def get_payment(self, payment_id: int) -> dict | None:
        return await self.adapter.fetchone(
            "SELECT * FROM payments WHERE id=?", (payment_id,)
        )

    async def list_payments(self, status: str | None = None, limit: int = 100) -> list[dict]:
        if status:
            return await self.adapter.fetchall(
                "SELECT * FROM payments WHERE status=? ORDER BY id DESC LIMIT ?",
                (status, limit),
            )
        return await self.adapter.fetchall(
            "SELECT * FROM payments ORDER BY id DESC LIMIT ?", (limit,)
        )

    async def list_payments_by_user(self, user_id: int, limit: int = 20) -> list[dict]:
        return await self.adapter.fetchall(
            "SELECT * FROM payments WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )

    async def set_invoice(self, payment_id: int, invoice_id: int, pay_url: str, comment: str = "") -> None:
        await self.adapter.execute(
            "UPDATE payments SET invoice_id=?, pay_url=?, comment=? WHERE id=?",
            (invoice_id, pay_url, comment, payment_id),
        )

    async def set_status(self, payment_id: int, status: str, paid_at: str | None = None) -> None:
        if paid_at:
            await self.adapter.execute(
                "UPDATE payments SET status=?, paid_at=? WHERE id=?",
                (status, paid_at, payment_id),
            )
        else:
            await self.adapter.execute(
                "UPDATE payments SET status=? WHERE id=?", (status, payment_id)
            )

    async def mark_paid(self, payment_id: int) -> None:
        await self.adapter.execute(
            "UPDATE payments SET status='paid', paid_at=? WHERE id=?",
            (_now(), payment_id),
        )

    async def count_by_status(self) -> dict[str, int]:
        rows = await self.adapter.fetchall(
            "SELECT status, COUNT(*) AS cnt FROM payments GROUP BY status"
        )
        return {r["status"]: r["cnt"] for r in rows}

    async def total_amount_paid(self) -> float:
        row = await self.adapter.fetchone(
            "SELECT COALESCE(SUM(amount),0) AS s FROM payments WHERE status IN ('paid','confirmed')"
        )
        return float(row["s"]) if row else 0.0

    async def users_count(self) -> int:
        row = await self.adapter.fetchone(
            "SELECT COUNT(DISTINCT user_id) AS c FROM payments"
        )
        return int(row["c"]) if row else 0


db = Database()