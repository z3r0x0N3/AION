from __future__ import annotations

import os
import sqlite3
import threading
import time
from dataclasses import dataclass, field as dataclass_field
from pathlib import Path
from typing import Any

ENRICHED_SCHEMA = """
CREATE TABLE IF NOT EXISTS enriched_nodes (
    node_id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    extension TEXT NOT NULL DEFAULT '',
    is_dir INTEGER NOT NULL DEFAULT 0,
    size INTEGER NOT NULL DEFAULT 0,
    mtime REAL NOT NULL DEFAULT 0,
    atime REAL NOT NULL DEFAULT 0,
    ctime REAL NOT NULL DEFAULT 0,
    permissions TEXT NOT NULL DEFAULT '',
    owner TEXT NOT NULL DEFAULT '',
    "group" TEXT NOT NULL DEFAULT '',
    line_count INTEGER NOT NULL DEFAULT 0,
    code_lines INTEGER NOT NULL DEFAULT 0,
    comment_lines INTEGER NOT NULL DEFAULT 0,
    blank_lines INTEGER NOT NULL DEFAULT 0,
    language TEXT NOT NULL DEFAULT 'Unknown',
    mime_type TEXT NOT NULL DEFAULT '',
    imports TEXT NOT NULL DEFAULT '[]',
    git_commits_30d INTEGER NOT NULL DEFAULT 0,
    git_authors TEXT NOT NULL DEFAULT '[]',
    git_last_commit_msg TEXT NOT NULL DEFAULT '',
    git_branch TEXT NOT NULL DEFAULT '',
    checksum_md5 TEXT NOT NULL DEFAULT '',
    checksum_sip32 TEXT NOT NULL DEFAULT '',
    symlink_target TEXT NOT NULL DEFAULT '',
    hardlinks INTEGER NOT NULL DEFAULT 0,
    inode INTEGER NOT NULL DEFAULT 0,
    device INTEGER NOT NULL DEFAULT 0,
    blocks INTEGER NOT NULL DEFAULT 0,
    blksize INTEGER NOT NULL DEFAULT 0,
    salience REAL NOT NULL DEFAULT 0,
    confidence REAL NOT NULL DEFAULT 0,
    entropy REAL NOT NULL DEFAULT 0,
    recency_score REAL NOT NULL DEFAULT 0,
    size_weight REAL NOT NULL DEFAULT 0,
    last_indexed REAL NOT NULL DEFAULT 0,
    last_seen REAL NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_enriched_path ON enriched_nodes(path);
CREATE INDEX IF NOT EXISTS idx_enriched_lang ON enriched_nodes(language);
CREATE INDEX IF NOT EXISTS idx_enriched_salience ON enriched_nodes(salience DESC);
CREATE INDEX IF NOT EXISTS idx_enriched_recency ON enriched_nodes(recency_score DESC);
CREATE INDEX IF NOT EXISTS idx_enriched_ext ON enriched_nodes(extension);
CREATE INDEX IF NOT EXISTS idx_enriched_git_commits ON enriched_nodes(git_commits_30d DESC);
"""

TELEMETRY_SCHEMA = """
CREATE TABLE IF NOT EXISTS telemetry_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    node_count INTEGER NOT NULL DEFAULT 0,
    mutation_count INTEGER NOT NULL DEFAULT 0,
    avg_salience REAL NOT NULL DEFAULT 0,
    avg_confidence REAL NOT NULL DEFAULT 0,
    avg_entropy REAL NOT NULL DEFAULT 0,
    drift_score REAL NOT NULL DEFAULT 0,
    fs_file_count INTEGER NOT NULL DEFAULT 0,
    memory_mb REAL NOT NULL DEFAULT 0,
    cpu_percent REAL NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_telemetry_ts ON telemetry_log(timestamp);
"""

EVENT_LOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS event_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    event_type TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT '',
    detail TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_event_ts ON event_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_event_type ON event_log(event_type);
"""


class EnrichedStore:
    def __init__(self, db_path: str | Path) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(ENRICHED_SCHEMA)
        self._conn.executescript(TELEMETRY_SCHEMA)
        self._conn.executescript(EVENT_LOG_SCHEMA)
        self._conn.commit()

    def upsert_node(self, node_id: str, data: dict[str, Any]) -> None:
        with self._lock:
            self._conn.execute(
                """INSERT INTO enriched_nodes (
                   node_id, path, name, extension, is_dir, size, mtime, atime, ctime,
                   permissions, owner, "group", line_count, code_lines, comment_lines,
                   blank_lines, language, mime_type, imports, git_commits_30d,
                   git_authors, git_last_commit_msg, git_branch, checksum_md5,
                   checksum_sip32, symlink_target, hardlinks, inode, device, blocks,
                   blksize, salience, confidence, entropy, recency_score, size_weight,
                   last_indexed, last_seen)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(node_id) DO UPDATE SET
                   path=excluded.path, name=excluded.name, extension=excluded.extension,
                   is_dir=excluded.is_dir, size=excluded.size, mtime=excluded.mtime,
                   atime=excluded.atime, ctime=excluded.ctime,
                   permissions=excluded.permissions, owner=excluded.owner,
                   "group"=excluded."group", line_count=excluded.line_count,
                   code_lines=excluded.code_lines, comment_lines=excluded.comment_lines,
                   blank_lines=excluded.blank_lines, language=excluded.language,
                   mime_type=excluded.mime_type, imports=excluded.imports,
                   git_commits_30d=excluded.git_commits_30d,
                   git_authors=excluded.git_authors,
                   git_last_commit_msg=excluded.git_last_commit_msg,
                   git_branch=excluded.git_branch, checksum_md5=excluded.checksum_md5,
                   checksum_sip32=excluded.checksum_sip32,
                   symlink_target=excluded.symlink_target,
                   hardlinks=excluded.hardlinks, inode=excluded.inode,
                   device=excluded.device, blocks=excluded.blocks,
                   blksize=excluded.blksize, salience=excluded.salience,
                   confidence=excluded.confidence, entropy=excluded.entropy,
                   recency_score=excluded.recency_score, size_weight=excluded.size_weight,
                   last_indexed=excluded.last_indexed, last_seen=excluded.last_seen""",
                (
                    node_id, data.get("path", ""), data.get("name", ""),
                    data.get("extension", ""), int(data.get("is_dir", False)),
                    data.get("size", 0), data.get("mtime", 0), data.get("atime", 0),
                    data.get("ctime", 0), data.get("permissions", ""),
                    data.get("owner", ""), data.get("group", ""),
                    data.get("line_count", 0), data.get("code_lines", 0),
                    data.get("comment_lines", 0), data.get("blank_lines", 0),
                    data.get("language", "Unknown"), data.get("mime_type", ""),
                    str(data.get("imports", [])), data.get("git_commits_30d", 0),
                    str(data.get("git_authors", [])),
                    data.get("git_last_commit_msg", ""), data.get("git_branch", ""),
                    data.get("checksum_md5", ""), data.get("checksum_sip32", ""),
                    data.get("symlink_target", ""), data.get("hardlinks", 0),
                    data.get("inode", 0), data.get("device", 0),
                    data.get("blocks", 0), data.get("blksize", 0),
                    data.get("salience", 0), data.get("confidence", 0),
                    data.get("entropy", 0), data.get("recency_score", 0),
                    data.get("size_weight", 0), data.get("last_indexed", 0),
                    time.time(),
                ),
            )
            self._conn.commit()

    def upsert_telemetry(self, data: dict[str, Any]) -> None:
        with self._lock:
            self._conn.execute(
                """INSERT INTO telemetry_log (timestamp, node_count, mutation_count,
                   avg_salience, avg_confidence, avg_entropy, drift_score,
                   fs_file_count, memory_mb, cpu_percent)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    time.time(), data.get("node_count", 0), data.get("mutation_count", 0),
                    data.get("avg_salience", 0), data.get("avg_confidence", 0),
                    data.get("avg_entropy", 0), data.get("drift_score", 0),
                    data.get("fs_file_count", 0), data.get("memory_mb", 0),
                    data.get("cpu_percent", 0),
                ),
            )
            self._conn.commit()

    def log_event(self, event_type: str, source: str = "", detail: str = "") -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO event_log (timestamp, event_type, source, detail) VALUES (?,?,?,?)",
                (time.time(), event_type, source, detail),
            )
            self._conn.commit()

    def _row_as_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        return dict(zip(row.keys(), row)) if row else {}

    def query_nodes(
        self,
        language: str | None = None,
        extension: str | None = None,
        min_salience: float = 0,
        min_recency: float = 0,
        min_size: int = 0,
        max_size: int = 0,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        with self._lock:
            clauses = []
            params: list[Any] = []
            if language:
                clauses.append("language = ?")
                params.append(language)
            if extension:
                clauses.append("extension = ?")
                params.append(extension)
            if min_salience > 0:
                clauses.append("salience >= ?")
                params.append(min_salience)
            if min_recency > 0:
                clauses.append("recency_score >= ?")
                params.append(min_recency)
            if min_size > 0:
                clauses.append("size >= ?")
                params.append(min_size)
            if max_size > 0:
                clauses.append("size <= ?")
                params.append(max_size)
            where = " AND ".join(clauses) if clauses else "1"
            rows = self._conn.execute(
                f"SELECT * FROM enriched_nodes WHERE {where} ORDER BY salience DESC LIMIT ? OFFSET ?",
                (*params, limit, offset),
            ).fetchall()
            return [self._row_as_dict(r) for r in rows]

    def get_node(self, node_id_or_path: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM enriched_nodes WHERE node_id = ? OR path = ?",
                (node_id_or_path, node_id_or_path),
            ).fetchone()
            return self._row_as_dict(row) if row else None

    def get_telemetry(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM telemetry_log ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
            return [self._row_as_dict(r) for r in rows]

    def get_events(self, event_type: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            if event_type:
                rows = self._conn.execute(
                    "SELECT * FROM event_log WHERE event_type = ? ORDER BY timestamp DESC LIMIT ?",
                    (event_type, limit),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM event_log ORDER BY timestamp DESC LIMIT ?", (limit,)
                ).fetchall()
            return [self._row_as_dict(r) for r in rows]

    def stats(self) -> dict[str, Any]:
        with self._lock:
            lang_rows = self._conn.execute(
                "SELECT language, COUNT(*) AS count FROM enriched_nodes GROUP BY language ORDER BY count DESC LIMIT 20"
            ).fetchall()
            ext_rows = self._conn.execute(
                "SELECT extension, COUNT(*) AS count FROM enriched_nodes GROUP BY extension ORDER BY count DESC LIMIT 20"
            ).fetchall()
            return {
                "total_nodes": self._conn.execute("SELECT COUNT(*) FROM enriched_nodes").fetchone()[0],
                "total_telemetry": self._conn.execute("SELECT COUNT(*) FROM telemetry_log").fetchone()[0],
                "total_events": self._conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0],
                "languages": [self._row_as_dict(r) for r in lang_rows],
                "extensions": [self._row_as_dict(r) for r in ext_rows],
            }

    def delete_node(self, node_id: str) -> bool:
        with self._lock:
            c = self._conn.execute("DELETE FROM enriched_nodes WHERE node_id = ?", (node_id,))
            self._conn.commit()
            return c.rowcount > 0

    def close(self) -> None:
        self._conn.close()
