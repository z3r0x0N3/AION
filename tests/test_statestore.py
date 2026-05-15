import threading
import time

import pytest

from aion.statestore import StateStore


class TestStateStore:
    def test_set_and_get(self):
        store = StateStore()
        store["foo"] = {"bar": 42}
        assert store["foo"] == {"bar": 42}

    def test_key_error(self):
        store = StateStore()
        with pytest.raises(KeyError):
            _ = store["nonexistent"]

    def test_delete(self):
        store = StateStore()
        store["x"] = 1
        assert "x" in store
        del store["x"]
        assert "x" not in store

    def test_len_and_iter(self):
        store = StateStore()
        store["a"] = 1
        store["b"] = 2
        store["c"] = 3
        assert len(store) == 3
        assert sorted(store) == ["a", "b", "c"]

    def test_contains(self):
        store = StateStore()
        store["key"] = "val"
        assert "key" in store
        assert "nope" not in store

    def test_set_with_ttl(self):
        store = StateStore()
        store.set_with_ttl("ephemeral", "gone", ttl_seconds=0.1)
        assert "ephemeral" in store
        time.sleep(0.15)
        assert "ephemeral" not in store

    def test_get_version(self):
        store = StateStore()
        store["v"] = 1
        v1 = store.get_version("v")
        store["v"] = 2
        v2 = store.get_version("v")
        assert v2 == v1 + 1

    def test_get_many(self):
        store = StateStore()
        store["a"] = 1
        store["b"] = 2
        assert store.get_many(["a", "b", "c"]) == {"a": 1, "b": 2}

    def test_atomic_update(self):
        store = StateStore()
        store["counter"] = 0
        store.atomic_update("counter", lambda x: x + 1)
        store.atomic_update("counter", lambda x: x + 1)
        assert store["counter"] == 2

    def test_clear(self):
        store = StateStore()
        store["a"] = 1
        store["b"] = 2
        store.clear()
        assert len(store) == 0

    def test_concurrent_read_write(self):
        store = StateStore()
        errors = []

        def writer():
            for i in range(100):
                try:
                    store[f"key_{i}"] = i
                except Exception as e:
                    errors.append(e)

        def reader():
            for i in range(100):
                try:
                    _ = store.get_many([f"key_{i}"])
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=writer) for _ in range(2)] + [
            threading.Thread(target=reader) for _ in range(2)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0

    def test_capacity_eviction(self):
        store = StateStore(max_size=5)
        for i in range(10):
            store[f"k{i}"] = i
        assert len(store) <= 5

    def test_close(self):
        store = StateStore()
        store["a"] = 1
        store.close()
        # should be able to reopen
        store2 = StateStore()
        assert "a" not in store2
