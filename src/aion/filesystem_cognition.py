from __future__ import annotations

import hashlib
import os
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from aion.eventbus import EventBus, Priority
from aion.semantic_manifold import SemanticManifold, SemanticNode


VECTOR_DIM = 32
RECENCY_HALFLIFE_DAYS = 7.0
SIZE_IDEAL_KB = 64.0


@dataclass
class FileMetadata:
    path: str
    size: int
    mtime: float
    atime: float
    entropy: float
    extension: str
    depth: int
    executable: bool
    node_id: str | None
    last_indexed: float
    recency_score: float = 0.0
    size_weight: float = 1.0


class FileMetadataStore:
    def __init__(self, db_path: str | Path) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS file_meta (
                path TEXT PRIMARY KEY,
                node_id TEXT,
                size INTEGER NOT NULL DEFAULT 0,
                mtime REAL NOT NULL DEFAULT 0,
                atime REAL NOT NULL DEFAULT 0,
                entropy REAL NOT NULL DEFAULT 0,
                extension TEXT NOT NULL DEFAULT '',
                depth INTEGER NOT NULL DEFAULT 0,
                executable INTEGER NOT NULL DEFAULT 0,
                recency_score REAL NOT NULL DEFAULT 0,
                size_weight REAL NOT NULL DEFAULT 1.0,
                last_indexed REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_file_recency ON file_meta(recency_score DESC);
            CREATE INDEX IF NOT EXISTS idx_file_size ON file_meta(size);
            CREATE INDEX IF NOT EXISTS idx_file_ext ON file_meta(extension);
            CREATE INDEX IF NOT EXISTS idx_file_node ON file_meta(node_id);
        """)
        self._conn.commit()

    def upsert(self, meta: FileMetadata) -> None:
        with self._lock:
            self._conn.execute(
                """INSERT INTO file_meta (path, node_id, size, mtime, atime, entropy,
                   extension, depth, executable, recency_score, size_weight, last_indexed)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(path) DO UPDATE SET
                       node_id = excluded.node_id,
                       size = excluded.size,
                       mtime = excluded.mtime,
                       atime = excluded.atime,
                       entropy = excluded.entropy,
                       extension = excluded.extension,
                       depth = excluded.depth,
                       executable = excluded.executable,
                       recency_score = excluded.recency_score,
                       size_weight = excluded.size_weight,
                       last_indexed = excluded.last_indexed""",
                (meta.path, meta.node_id, meta.size, meta.mtime, meta.atime,
                 meta.entropy, meta.extension, meta.depth, int(meta.executable),
                 meta.recency_score, meta.size_weight, meta.last_indexed),
            )
            self._conn.commit()

    def delete(self, path: str) -> bool:
        with self._lock:
            c = self._conn.execute("DELETE FROM file_meta WHERE path = ?", (path,))
            self._conn.commit()
            return c.rowcount > 0

    def get(self, path: str) -> FileMetadata | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM file_meta WHERE path = ?", (path,)
            ).fetchone()
            if row is None:
                return None
            return self._row_to_meta(row)

    def get_by_node(self, node_id: str) -> FileMetadata | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM file_meta WHERE node_id = ?", (node_id,)
            ).fetchone()
            if row is None:
                return None
            return self._row_to_meta(row)

    def top_by_recency(self, limit: int = 100) -> list[FileMetadata]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM file_meta ORDER BY recency_score DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [self._row_to_meta(r) for r in rows]

    def top_by_size(self, limit: int = 100) -> list[FileMetadata]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM file_meta ORDER BY size DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [self._row_to_meta(r) for r in rows]

    def query(self, extension: str | None = None, min_size: int = 0, max_size: int = 0) -> list[FileMetadata]:
        with self._lock:
            clauses = []
            params = []
            if extension:
                clauses.append("extension = ?")
                params.append(extension)
            if min_size > 0:
                clauses.append("size >= ?")
                params.append(min_size)
            if max_size > 0:
                clauses.append("size <= ?")
                params.append(max_size)
            where = " AND ".join(clauses) if clauses else "1"
            rows = self._conn.execute(
                f"SELECT * FROM file_meta WHERE {where} ORDER BY recency_score DESC", params
            ).fetchall()
            return [self._row_to_meta(r) for r in rows]

    def count(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) AS cnt FROM file_meta").fetchone()
            return row[0] if row else 0

    def _row_to_meta(self, row: sqlite3.Row) -> FileMetadata:
        return FileMetadata(
            path=row[0], node_id=row[1], size=row[2], mtime=row[3], atime=row[4],
            entropy=row[5], extension=row[6], depth=row[7], executable=bool(row[8]),
            recency_score=row[9], size_weight=row[10], last_indexed=row[11],
        )

    def close(self) -> None:
        self._conn.close()


def compute_recency_score(mtime: float, atime: float) -> float:
    now = time.time()
    days_since_mod = max(0, (now - mtime) / 86400)
    days_since_access = max(0, (now - atime) / 86400)
    mod_score = np.exp(-days_since_mod / RECENCY_HALFLIFE_DAYS)
    access_score = np.exp(-days_since_access / (RECENCY_HALFLIFE_DAYS * 0.5))
    return float(max(mod_score, access_score * 0.6))


def compute_size_weight(size: int) -> float:
    if size <= 0:
        return 0.1
    kb = size / 1024
    ratio = kb / SIZE_IDEAL_KB
    if ratio < 1:
        return float(np.tanh(ratio * 2))
    else:
        return float(np.exp(-(ratio - 1) * 0.1))


class FilesystemEncoder:
    @classmethod
    def encode(cls, path: str | Path) -> np.ndarray:
        p = Path(path)
        if not p.exists():
            return np.zeros(VECTOR_DIM, dtype=np.float32)
        try:
            stat = p.stat()
            vec = np.zeros(VECTOR_DIM, dtype=np.float32)
            vec[0] = np.tanh(stat.st_size / 1_000_000)
            vec[1] = np.sin(stat.st_mtime / 1_000_000)
            vec[2] = 1.0 if p.is_dir() else 0.0
            vec[3] = np.tanh(stat.st_nlink / 10.0)
            ext = p.suffix.lower()
            h = int(hashlib.md5(ext.encode()).hexdigest()[:8], 16) / 2**32
            vec[4] = h
            depth = len(p.relative_to(p.anchor).parts) if p.anchor else len(p.parts)
            vec[5] = np.tanh(depth / 20.0)
            vec[6] = 1.0 if stat.st_mode & 0o111 else 0.0
            vec[7] = np.tanh(stat.st_size / (1024 * 1024 * 100))
            if p.is_file() and stat.st_size > 0:
                try:
                    sample = p.read_bytes()[:4096]
                    vec[8] = cls._shannon_entropy(sample)
                except (OSError, PermissionError):
                    vec[8] = 0.0
            vec[9] = np.tanh((time.time() - stat.st_atime) / 86400)
            rng = np.random.RandomState(int(stat.st_ino))
            vec[10:] = rng.randn(VECTOR_DIM - 10).astype(np.float32) * 0.01
            vec /= np.linalg.norm(vec) + 1e-8
            return vec
        except (OSError, PermissionError):
            return np.random.randn(VECTOR_DIM).astype(np.float32) * 0.01

    @staticmethod
    def _shannon_entropy(data: bytes) -> float:
        if not data:
            return 0.0
        counts = np.zeros(256)
        for b in data:
            counts[b] += 1
        probs = counts / len(data)
        total = sum(p * np.log2(p) for p in probs if p > 0)
        return float(-total) / 8.0


EXCLUDE_DIRS = {
    ".git", ".cache", ".venv", "node_modules", "__pycache__",
    ".aion", ".local", ".config", ".mozilla", ".npm",
    ".gradle", ".cargo", ".rustup", ".sbt", ".ivy2",
    "Library", "AppData", ".var", ".flatpak", ".steam",
    ".Trash", ".thumbnails", ".zoiper",
}


class FilesystemCognitiveEngine:
    def __init__(
        self,
        root_path: str | Path,
        manifold: SemanticManifold | None = None,
        event_bus: EventBus | None = None,
        db_path: str | Path | None = None,
    ) -> None:
        self.root = Path(root_path).resolve()
        self._manifold = manifold or SemanticManifold(
            vector_dim=VECTOR_DIM,
            max_nodes=1_000_000,
        )
        self._bus = event_bus or EventBus()
        self._store = FileMetadataStore(
            db_path or self.root / ".aion_fs" / "file_meta.db"
        )
        self._path_to_node: dict[str, str] = {}
        self._node_to_path: dict[str, str] = {}

    @property
    def manifold(self) -> SemanticManifold:
        return self._manifold

    @property
    def event_bus(self) -> EventBus:
        return self._bus

    @property
    def metadata_store(self) -> FileMetadataStore:
        return self._store

    def index(self, path: str | Path | None = None, max_files: int = 50_000) -> int:
        target = Path(path) if path else self.root
        count = 0
        if target.is_file():
            if self._ingest_path(target):
                count += 1
        else:
            for p in target.rglob("*"):
                if count >= max_files:
                    break
                if any(part.startswith(".") or part in EXCLUDE_DIRS for part in p.parts):
                    continue
                try:
                    if self._ingest_path(p):
                        count += 1
                except (OSError, PermissionError):
                    continue
        self._manifold.rebuild_tree_if_needed()
        return count

    def _ingest_path(self, path: Path) -> bool:
        try:
            path_str = str(path)
            if path_str in self._path_to_node:
                node_id = self._path_to_node[path_str]
                self._update_node(path, node_id)
                return False
            vector = FilesystemEncoder.encode(path)
            meta = self._build_meta(path)
            salience = 0.3 + 0.4 * meta.recency_score + 0.3 * meta.size_weight
            node = self._manifold.create_node(
                vector=vector,
                salience=min(1.0, salience),
                confidence=1.0,
                entropy=meta.entropy,
            )
            self._path_to_node[path_str] = node.id
            self._node_to_path[node.id] = path_str
            meta.node_id = node.id
            self._store.upsert(meta)
            return True
        except (OSError, PermissionError, RuntimeError):
            return False

    def _update_node(self, path: Path, node_id: str) -> None:
        node = self._manifold.get(node_id)
        if node is None:
            return
        new_vector = FilesystemEncoder.encode(path)
        meta = self._build_meta(path)
        node.vector = new_vector
        node.last_mutated = time.monotonic()
        node.entropy = meta.entropy
        node.salience = min(1.0, 0.3 + 0.4 * meta.recency_score + 0.3 * meta.size_weight)
        self._manifold.update_node(node)
        meta.node_id = node_id
        self._store.upsert(meta)

    def _build_meta(self, path: Path) -> FileMetadata:
        try:
            stat = path.stat()
            ext = path.suffix.lower()
            depth = len(path.relative_to(self.root).parts) if path != self.root else 0
            entropy = 0.0
            if path.is_file() and stat.st_size > 0:
                try:
                    entropy = FilesystemEncoder._shannon_entropy(path.read_bytes()[:4096])
                except (OSError, PermissionError):
                    pass
            recency = compute_recency_score(stat.st_mtime, stat.st_atime)
            size_w = compute_size_weight(stat.st_size)
            return FileMetadata(
                path=str(path),
                size=stat.st_size,
                mtime=stat.st_mtime,
                atime=stat.st_atime,
                entropy=entropy,
                extension=ext,
                depth=depth,
                executable=bool(stat.st_mode & 0o111),
                node_id=self._path_to_node.get(str(path)),
                last_indexed=time.time(),
                recency_score=recency,
                size_weight=size_w,
            )
        except (OSError, PermissionError):
            return FileMetadata(
                path=str(path), size=0, mtime=0, atime=0, entropy=0,
                extension="", depth=0, executable=False,
                node_id=None, last_indexed=time.time(),
            )

    def handle_event(self, event_type: str, path: str) -> None:
        p = Path(path)
        if event_type == "created":
            if str(p) not in self._path_to_node:
                self._ingest_path(p)
                self._manifold.rebuild_tree_if_needed()
        elif event_type == "modified":
            node_id = self._path_to_node.get(str(p))
            if node_id:
                self._update_node(p, node_id)
        elif event_type == "deleted":
            node_id = self._path_to_node.pop(str(p), None)
            if node_id:
                self._node_to_path.pop(node_id, None)
                self._manifold.remove_node(node_id)
                self._store.delete(str(p))
        elif event_type == "moved":
            parts = path.split("|", 1)
            src, dst = parts[0], parts[1] if len(parts) > 1 else ""
            node_id = self._path_to_node.pop(str(src), None)
            if node_id and dst:
                self._path_to_node[str(dst)] = node_id
                self._node_to_path[node_id] = str(dst)
                self._store.delete(str(src))
                self._update_node(Path(dst), node_id)

    def find_similar(self, path: str | Path, k: int = 8) -> list[tuple[str, float, str, float]]:
        vector = FilesystemEncoder.encode(path)
        results = self._manifold.nearest_neighbors(vector, k=k)
        out = []
        for nid, dist in results:
            meta = self._store.get_by_node(nid)
            recency = meta.recency_score if meta else 0.0
            out.append((nid, dist, self._node_to_path.get(nid, "?"), recency))
        return out

    def node_for_path(self, path: str | Path) -> SemanticNode | None:
        node_id = self._path_to_node.get(str(path))
        return self._manifold.get(node_id) if node_id else None

    def path_for_node(self, node_id: str) -> str | None:
        return self._node_to_path.get(node_id)

    def path_count(self) -> int:
        return len(self._path_to_node)

    def node_ids_by_salience(self, top_n: int = 10) -> list[tuple[str, float, str]]:
        from aion.salience_engine import SalienceEngine
        se = SalienceEngine(self._manifold)
        smap = se.compute_salience_map()
        sorted_ids = sorted(smap.node_scores, key=smap.node_scores.get, reverse=True)[:top_n]
        return [(nid, smap.node_scores[nid], self._node_to_path.get(nid, "?")) for nid in sorted_ids]

    def top_recent(self, limit: int = 20) -> list[FileMetadata]:
        return self._store.top_by_recency(limit)

    def query_files(self, extension: str | None = None, min_size: int = 0, max_size: int = 0) -> list[FileMetadata]:
        return self._store.query(extension, min_size, max_size)

    def close(self) -> None:
        self._store.close()


class FilesystemWatcher:
    def __init__(self, engine: FilesystemCognitiveEngine) -> None:
        self._engine = engine
        self._observer = None

    def start(self) -> None:
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class _Handler(FileSystemEventHandler):
                def __init__(self, eng):
                    self.eng = eng

                def on_created(self, event):
                    if any(part.startswith(".") or part in EXCLUDE_DIRS for part in Path(event.src_path).parts):
                        return
                    if not event.is_directory:
                        self.eng.handle_event("created", event.src_path)

                def on_modified(self, event):
                    if not event.is_directory:
                        self.eng.handle_event("modified", event.src_path)

                def on_deleted(self, event):
                    if not event.is_directory:
                        self.eng.handle_event("deleted", event.src_path)

                def on_moved(self, event):
                    if not event.is_directory:
                        self.eng.handle_event("moved", f"{event.src_path}|{event.dest_path}")

            self._observer = Observer()
            self._handler = _Handler(self._engine)
            self._observer.schedule(self._handler, str(self._engine.root), recursive=True)
            self._observer.start()
        except ImportError:
            pass

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join()

    def index_and_watch(self, max_files: int = 50_000) -> int:
        count = self._engine.index(max_files=max_files)
        self.start()
        return count
