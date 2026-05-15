import tempfile
import time
from pathlib import Path

import numpy as np
import pytest

from aion.filesystem_cognition import (
    FilesystemEncoder,
    FilesystemCognitiveEngine,
    compute_recency_score,
    compute_size_weight,
    FileMetadataStore,
    FileMetadata,
)


class TestFilesystemEncoder:
    def test_encode_file(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"hello world\n" * 100)
            path = f.name
        try:
            vec = FilesystemEncoder.encode(path)
            assert vec.shape == (32,)
            assert abs(np.linalg.norm(vec) - 1.0) < 1e-6
        finally:
            Path(path).unlink()

    def test_encode_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vec = FilesystemEncoder.encode(tmpdir)
            assert vec.shape == (32,)
            assert abs(np.linalg.norm(vec) - 1.0) < 1e-6

    def test_encode_nonexistent(self):
        vec = FilesystemEncoder.encode("/nonexistent_path_xyz")
        assert np.allclose(vec, np.zeros(32))


class TestScoring:
    def test_recency_score_returns_float(self):
        score = compute_recency_score(time.time(), time.time())
        assert 0 <= score <= 1

    def test_recency_older_is_lower(self):
        import time
        new = compute_recency_score(time.time(), time.time())
        old = compute_recency_score(time.time() - 86400 * 30, time.time() - 86400 * 30)
        assert new > old

    def test_size_weight_ideal(self):
        w = compute_size_weight(64 * 1024)
        assert w > 0.8

    def test_size_weight_tiny(self):
        w = compute_size_weight(10)
        assert w < 0.5

    def test_size_weight_huge(self):
        w = compute_size_weight(10 * 1024 * 1024)
        assert w < 1.0


class TestFileMetadataStore:
    def test_upsert_and_get(self):
        import time
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "meta.db"
            store = FileMetadataStore(db)
            meta = FileMetadata(
                path="/tmp/test.txt", node_id="abc", size=1024,
                mtime=time.time(), atime=time.time(), entropy=0.5,
                extension=".txt", depth=2, executable=False,
                last_indexed=time.time(), recency_score=0.8, size_weight=0.9,
            )
            store.upsert(meta)
            retrieved = store.get("/tmp/test.txt")
            assert retrieved is not None
            assert retrieved.size == 1024
            assert retrieved.recency_score == 0.8

    def test_delete(self):
        import time
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "meta.db"
            store = FileMetadataStore(db)
            meta = FileMetadata(
                path="/x", node_id="n1", size=1,
                mtime=time.time(), atime=time.time(), entropy=0,
                extension="", depth=1, executable=False, last_indexed=time.time(),
            )
            store.upsert(meta)
            assert store.delete("/x") is True
            assert store.delete("/x") is False

    def test_get_by_node(self):
        import time
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "meta.db"
            store = FileMetadataStore(db)
            store.upsert(FileMetadata(
                path="/a.py", node_id="node1", size=100,
                mtime=time.time(), atime=time.time(), entropy=0.3,
                extension=".py", depth=1, executable=False, last_indexed=time.time(),
            ))
            meta = store.get_by_node("node1")
            assert meta is not None
            assert meta.path == "/a.py"

    def test_top_by_recency(self):
        import time
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "meta.db"
            store = FileMetadataStore(db)
            now = time.time()
            store.upsert(FileMetadata(path="/new", node_id="n1", size=1,
                mtime=now, atime=now, entropy=0, extension="", depth=0,
                executable=False, last_indexed=now, recency_score=0.9, size_weight=0.5))
            store.upsert(FileMetadata(path="/old", node_id="n2", size=1,
                mtime=now - 86400 * 30, atime=now - 86400 * 30, entropy=0,
                extension="", depth=0, executable=False, last_indexed=now,
                recency_score=0.1, size_weight=0.5))
            top = store.top_by_recency(10)
            assert len(top) == 2
            assert top[0].path == "/new"


class TestFilesystemCognitiveEngine:
    def test_index_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "file1.txt").write_text("hello")
            Path(tmpdir, "file2.py").write_text("print('hi')")
            Path(tmpdir, "subdir").mkdir()
            Path(tmpdir, "subdir", "nested.py").write_text("x=1")
            engine = FilesystemCognitiveEngine(tmpdir, db_path=Path(tmpdir, "test.db"))
            count = engine.index()
            assert count >= 3
            assert engine.path_count() >= 3

    def test_index_single_file(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            f.write(b"# title")
            path = f.name
        try:
            engine = FilesystemCognitiveEngine(Path(path).parent, db_path="/tmp/_aion_test.db")
            count = engine.index(path)
            assert count == 1
        finally:
            Path(path).unlink()
            Path("/tmp/_aion_test.db").unlink(missing_ok=True)
            Path("/tmp/_aion_test.db-wal").unlink(missing_ok=True)

    def test_find_similar(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(5):
                Path(tmpdir, f"file{i}.txt").write_text(f"content {i}")
            Path(tmpdir, "target.txt").write_text("content 3")
            engine = FilesystemCognitiveEngine(tmpdir, db_path=Path(tmpdir, "t.db"))
            engine.index()
            similar = engine.find_similar(Path(tmpdir, "target.txt"), k=3)
            assert len(similar) <= 3
            for nid, dist, path, recency in similar:
                assert isinstance(path, str)

    def test_node_for_path(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"import os")
            path = f.name
        try:
            engine = FilesystemCognitiveEngine(Path(path).parent, db_path="/tmp/_aion_test2.db")
            engine.index(path)
            node = engine.node_for_path(path)
            assert node is not None
            assert engine.path_for_node(node.id) == path
        finally:
            Path(path).unlink()
            Path("/tmp/_aion_test2.db").unlink(missing_ok=True)
            Path("/tmp/_aion_test2.db-wal").unlink(missing_ok=True)

    def test_handle_file_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = FilesystemCognitiveEngine(tmpdir, db_path=Path(tmpdir, "e.db"))
            test_file = Path(tmpdir, "newfile.txt")
            test_file.write_text("new content")
            engine.handle_event("created", str(test_file))
            assert engine.path_count() == 1
            test_file.write_text("modified content")
            engine.handle_event("modified", str(test_file))
            assert engine.path_count() == 1
            test_file.unlink()
            engine.handle_event("deleted", str(test_file))
            assert engine.path_count() == 0

    def test_top_recent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(5):
                Path(tmpdir, f"{i}.txt").write_text(f"data {i}")
            engine = FilesystemCognitiveEngine(tmpdir, db_path=Path(tmpdir, "r.db"))
            engine.index()
            recent = engine.top_recent(3)
            assert len(recent) <= 5

    def test_metadata_store_persists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir, "p.db")
            engine = FilesystemCognitiveEngine(tmpdir, db_path=db_path)
            Path(tmpdir, "persist.txt").write_text("hello")
            engine.index()
            assert engine.metadata_store.count() >= 1

    def test_salience_includes_recency_and_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "recent.py").write_text("x=1")
            engine = FilesystemCognitiveEngine(tmpdir, db_path=Path(tmpdir, "s.db"))
            engine.index()
            node = engine.node_for_path(str(Path(tmpdir, "recent.py")))
            assert node is not None
            assert node.salience > 0.3

    def test_query_by_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "a.py").write_text("print(1)")
            Path(tmpdir, "b.txt").write_text("hello")
            engine = FilesystemCognitiveEngine(tmpdir, db_path=Path(tmpdir, "q.db"))
            engine.index()
            py_files = engine.query_files(extension=".py")
            assert len(py_files) >= 1
            assert py_files[0].extension == ".py"
