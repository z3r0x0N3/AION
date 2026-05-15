import threading
import time

import pytest

from aion.eventbus import EventBus, Priority


class TestEventBus:
    def test_emit_and_subscribe(self):
        bus = EventBus()
        results = []

        def handler(e):
            results.append(e.payload["msg"])

        bus.subscribe("test.topic", handler)
        bus.emit("test.topic", {"msg": "hello"}, priority=Priority.HIGH)
        bus.process_next()
        assert results == ["hello"]

    def test_prefix_subscription(self):
        bus = EventBus()
        results = []

        def handler(e):
            results.append(e.topic)

        bus.subscribe_prefix("test.", handler)
        bus.emit("test.alpha", {"n": 1})
        bus.emit("test.beta", {"n": 2})
        bus.emit("other.gamma", {"n": 3})
        bus.process_all()
        assert results == ["test.alpha", "test.beta"]

    def test_priority_ordering(self):
        bus = EventBus()
        results = []

        def handler(e):
            results.append(e.payload["priority"])

        bus.subscribe("test", handler)
        bus.emit("test", {"priority": "low"}, priority=Priority.LOW)
        bus.emit("test", {"priority": "critical"}, priority=Priority.CRITICAL)
        bus.emit("test", {"priority": "normal"}, priority=Priority.NORMAL)
        bus.process_all()
        assert results == ["critical", "normal", "low"]

    def test_queue_overflow(self):
        bus = EventBus(max_size=3)
        bus.emit("t", {}, Priority.NORMAL)
        bus.emit("t", {}, Priority.NORMAL)
        bus.emit("t", {}, Priority.NORMAL)
        with pytest.raises(RuntimeError, match="queue full"):
            bus.emit("t", {}, Priority.NORMAL)

    def test_concurrent_emits(self):
        bus = EventBus()
        results = []
        lock = threading.Lock()

        def handler(e):
            with lock:
                results.append(e)

        bus.subscribe("test", handler)

        def emitter(start: int, count: int):
            for i in range(start, start + count):
                bus.emit("test", {"i": i})
                time.sleep(0.0001)

        threads = [threading.Thread(target=emitter, args=(i * 250, 250)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        bus.process_all()
        assert len(results) == 1000

    def test_unsubscribe(self):
        bus = EventBus()
        results = []

        def handler(e):
            results.append(1)

        bus.subscribe("test", handler)
        bus.emit("test", {})
        bus.process_next()
        assert len(results) == 1
        bus.unsubscribe("test", handler)
        bus.emit("test", {})
        bus.process_next()
        assert len(results) == 1

    def test_clear(self):
        bus = EventBus()
        bus.emit("a", {})
        bus.emit("b", {})
        assert bus.queue_size == 2
        bus.clear()
        assert bus.queue_size == 0

    def test_handler_exception_isolation(self):
        bus = EventBus()
        results = []

        def bad_handler(e):
            raise ValueError("oops")

        def good_handler(e):
            results.append("ok")

        bus.subscribe("test", bad_handler)
        bus.subscribe("test", good_handler)
        bus.emit("test", {})
        bus.process_next()
        assert results == ["ok"]

    def test_wait_for_event(self):
        bus = EventBus()

        def delayed_emit():
            time.sleep(0.05)
            bus.emit("wakeup", {"data": 42})

        t = threading.Thread(target=delayed_emit)
        t.start()
        event = bus.wait_for_event("wakeup", timeout=1.0)
        t.join()
        assert event is not None
        assert event.payload["data"] == 42
