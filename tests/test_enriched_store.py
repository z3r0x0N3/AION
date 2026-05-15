import tempfile
import time
from pathlib import Path

import pytest

from aion.enriched_store import EnrichedStore


class TestEnrichedStore:
    @pytest.fixture
    def store(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = EnrichedStore(Path(tmpdir) / "test.db")
            yield s
            s.close()

    def test_upsert_and_get_node(self, store):
        store.upsert_node("node1", {"path": "/test.py", "name": "test.py",
            "extension": ".py", "language": "Python", "size": 1024,
            "line_count": 10, "code_lines": 8, "salience": 0.5})
        node = store.get_node("node1")
        assert node is not None
        assert node["path"] == "/test.py"
        assert node["language"] == "Python"

    def test_get_nonexistent(self, store):
        assert store.get_node("nope") is None

    def test_get_by_path(self, store):
        store.upsert_node("n1", {"path": "/a/b.py", "name": "b.py"})
        node = store.get_node("/a/b.py")
        assert node is not None
        assert node["node_id"] == "n1"

    def test_query_by_language(self, store):
        store.upsert_node("n1", {"path": "/a.py", "extension": ".py", "language": "Python", "size": 100})
        store.upsert_node("n2", {"path": "/b.rs", "extension": ".rs", "language": "Rust", "size": 200})
        results = store.query_nodes(language="Python")
        assert len(results) == 1
        assert results[0]["language"] == "Python"

    def test_query_by_extension(self, store):
        store.upsert_node("n1", {"path": "/a.py", "extension": ".py", "language": "Python"})
        store.upsert_node("n2", {"path": "/b.py", "extension": ".py", "language": "Python"})
        results = store.query_nodes(extension=".py")
        assert len(results) == 2

    def test_query_salience_filter(self, store):
        store.upsert_node("n1", {"path": "/a", "salience": 0.9})
        store.upsert_node("n2", {"path": "/b", "salience": 0.1})
        results = store.query_nodes(min_salience=0.5)
        assert len(results) == 1

    def test_telemetry(self, store):
        store.upsert_telemetry({"node_count": 100, "mutation_count": 5000,
            "avg_salience": 0.5, "avg_confidence": 0.8, "avg_entropy": 0.3,
            "drift_score": 0.01, "fs_file_count": 50, "memory_mb": 100, "cpu_percent": 25})
        tel = store.get_telemetry(limit=10)
        assert len(tel) >= 1
        assert tel[0]["node_count"] == 100

    def test_event_log(self, store):
        store.log_event("test.event", "pytest", "test detail")
        events = store.get_events(limit=10)
        assert len(events) >= 1
        assert events[0]["event_type"] == "test.event"

    def test_event_filter(self, store):
        store.log_event("type_a", "src", "a")
        store.log_event("type_b", "src", "b")
        events = store.get_events(event_type="type_a")
        assert len(events) == 1
        assert events[0]["event_type"] == "type_a"

    def test_stats(self, store):
        store.upsert_node("n1", {"path": "/a.py", "extension": ".py", "language": "Python"})
        store.upsert_node("n2", {"path": "/b.rs", "extension": ".rs", "language": "Rust"})
        store.upsert_telemetry({"node_count": 2})
        s = store.stats()
        assert s["total_nodes"] >= 2
        assert s["total_telemetry"] >= 1
        assert len(s["languages"]) >= 2

    def test_delete_node(self, store):
        store.upsert_node("del1", {"path": "/del"})
        assert store.delete_node("del1") is True
        assert store.delete_node("nope") is False
        assert store.get_node("del1") is None
