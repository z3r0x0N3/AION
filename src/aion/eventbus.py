from __future__ import annotations

import heapq
import threading
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable

Handler = Callable[..., None]


class Priority(IntEnum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass(order=True)
class Event:
    priority: int
    timestamp: float = field(compare=False)
    topic: str = field(compare=False)
    payload: dict[str, Any] = field(compare=False)
    event_id: str = field(compare=False)


class EventBus:
    _MAX_QUEUE_SIZE = 10_000

    def __init__(self, max_size: int | None = None) -> None:
        self._lock = threading.RLock()
        self._subscribers: dict[str, list[Handler]] = defaultdict(list)
        self._prefix_subscribers: dict[str, list[Handler]] = defaultdict(list)
        self._queue: list[Event] = []
        self._max_size = max_size or self._MAX_QUEUE_SIZE
        self._processing = False

    def subscribe(self, topic: str, handler: Handler) -> str:
        sub_id = str(uuid.uuid4())
        with self._lock:
            self._subscribers[topic].append(handler)
        return sub_id

    def subscribe_prefix(self, prefix: str, handler: Handler) -> str:
        sub_id = str(uuid.uuid4())
        with self._lock:
            self._prefix_subscribers[prefix].append(handler)
        return sub_id

    def unsubscribe(self, topic: str, handler: Handler) -> bool:
        with self._lock:
            try:
                self._subscribers[topic].remove(handler)
                return True
            except ValueError:
                pass
            try:
                self._prefix_subscribers[topic].remove(handler)
                return True
            except ValueError:
                return False

    def emit(
        self,
        topic: str,
        payload: dict[str, Any] | None = None,
        priority: Priority = Priority.NORMAL,
    ) -> str:
        import time

        event = Event(
            priority=priority.value,
            timestamp=time.monotonic(),
            topic=topic,
            payload=payload or {},
            event_id=str(uuid.uuid4()),
        )
        with self._lock:
            if len(self._queue) >= self._max_size:
                raise RuntimeError(
                    f"EventBus queue full ({self._max_size} events). "
                    f"Dropping event: {topic}"
                )
            heapq.heappush(self._queue, event)
        return event.event_id

    def process_next(self) -> Event | None:
        with self._lock:
            if not self._queue:
                return None
            event = heapq.heappop(self._queue)

        self._dispatch(event)
        return event

    def process_all(self, max_events: int = 0) -> int:
        count = 0
        while True:
            if max_events and count >= max_events:
                break
            with self._lock:
                if not self._queue:
                    break
                event = heapq.heappop(self._queue)
            self._dispatch(event)
            count += 1
        return count

    def _dispatch(self, event: Event) -> None:
        exact_handlers = list(self._subscribers.get(event.topic, []))
        prefix_handlers: list[Handler] = []
        for prefix, handlers in self._prefix_subscribers.items():
            if event.topic.startswith(prefix):
                prefix_handlers.extend(handlers)

        for handler in exact_handlers + prefix_handlers:
            try:
                handler(event)
            except Exception:
                import traceback

                traceback.print_exc()

    @property
    def queue_size(self) -> int:
        with self._lock:
            return len(self._queue)

    def clear(self) -> None:
        with self._lock:
            self._queue.clear()

    def wait_for_event(self, topic: str, timeout: float = 5.0) -> Event | None:
        import time

        deadline = time.monotonic() + timeout
        result: list[Event] = []

        def waiter(e: Event) -> None:
            result.append(e)

        sub_id = self.subscribe(topic, waiter)
        try:
            while time.monotonic() < deadline:
                self.process_next()
                if result:
                    return result[0]
                time.sleep(0.001)
            return None
        finally:
            self.unsubscribe(topic, waiter)
