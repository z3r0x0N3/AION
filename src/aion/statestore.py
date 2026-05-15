from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from collections.abc import MutableMapping
from typing import Any


class StateStore(MutableMapping):
    def __init__(self, db_path: str = ":memory:", max_size: int = 1_000_000) -> None:
        self._db_path = db_path
        self._max_size = max_size
        self._lock = threading.RLock()
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self._db_path, check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
            self._init_schema(self._local.conn)
        return self._local.conn

    def _init_db(self) -> None:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema(conn)
        conn.close()

    def _init_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS kv_store (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                ttl REAL
            );
            CREATE INDEX IF NOT EXISTS idx_kv_updated ON kv_store(updated_at);
        """)

    def __getitem__(self, key: str) -> Any:
        with self._lock:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT value, ttl FROM kv_store WHERE key = ?", (key,)
            ).fetchone()
            if row is None:
                raise KeyError(key)
            if row["ttl"] is not None and time.monotonic() > row["ttl"]:
                conn.execute("DELETE FROM kv_store WHERE key = ?", (key,))
                conn.commit()
                raise KeyError(key)
            return json.loads(row["value"])

    def __setitem__(self, key: str, value: Any) -> None:
        with self._lock:
            conn = self._get_conn()
            now = time.monotonic()
            self._ensure_capacity(conn)
            conn.execute(
                """INSERT INTO kv_store (key, value, version, created_at, updated_at)
                   VALUES (?, ?, 1, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET
                       value = excluded.value,
                       version = kv_store.version + 1,
                       updated_at = excluded.updated_at""",
                (key, json.dumps(value), now, now),
            )
            conn.commit()

    def __delitem__(self, key: str) -> None:
        with self._lock:
            conn = self._get_conn()
            cursor = conn.execute(
                "DELETE FROM kv_store WHERE key = ?", (key,)
            )
            conn.commit()
            if cursor.rowcount == 0:
                raise KeyError(key)

    def __len__(self) -> int:
        with self._lock:
            conn = self._get_conn()
            row = conn.execute("SELECT COUNT(*) AS cnt FROM kv_store").fetchone()
            return row["cnt"] if row else 0

    def __iter__(self):
        with self._lock:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT key FROM kv_store ORDER BY key"
            ).fetchall()
            for row in rows:
                yield row["key"]

    def __contains__(self, key: object) -> bool:
        try:
            self.__getitem__(str(key))
            return True
        except KeyError:
            return False

    def set_with_ttl(self, key: str, value: Any, ttl_seconds: float) -> None:
        with self._lock:
            conn = self._get_conn()
            now = time.monotonic()
            self._ensure_capacity(conn)
            conn.execute(
                """INSERT INTO kv_store (key, value, version, created_at, updated_at, ttl)
                   VALUES (?, ?, 1, ?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET
                       value = excluded.value,
                       version = kv_store.version + 1,
                       updated_at = excluded.updated_at,
                       ttl = excluded.ttl""",
                (key, json.dumps(value), now, now, now + ttl_seconds),
            )
            conn.commit()

    def get_version(self, key: str) -> int:
        with self._lock:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT version FROM kv_store WHERE key = ?", (key,)
            ).fetchone()
            if row is None:
                raise KeyError(key)
            return row["version"]

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        with self._lock:
            conn = self._get_conn()
            placeholders = ",".join("?" for _ in keys)
            rows = conn.execute(
                f"SELECT key, value FROM kv_store WHERE key IN ({placeholders})",
                keys,
            ).fetchall()
            result: dict[str, Any] = {}
            for row in rows:
                try:
                    result[row["key"]] = json.loads(row["value"])
                except (json.JSONDecodeError, TypeError):
                    result[row["key"]] = row["value"]
            return result

    def atomic_update(
        self, key: str, update_func: callable[[Any], Any]
    ) -> Any:
        with self._lock:
            current = self.__getitem__(key)
            new_value = update_func(current)
            self.__setitem__(key, new_value)
            return new_value

    def clear(self) -> None:
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM kv_store")
            conn.commit()

    def _ensure_capacity(self, conn: sqlite3.Connection) -> None:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM kv_store").fetchone()
        if row and row["cnt"] >= self._max_size:
            conn.execute(
                "DELETE FROM kv_store WHERE key IN ("
                "SELECT key FROM kv_store ORDER BY updated_at ASC "
                "LIMIT MAX(1, (SELECT COUNT(*) FROM kv_store) - ?)"
                ")",
                (int(self._max_size * 0.9),),
            )
            conn.commit()

    def close(self) -> None:
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None
