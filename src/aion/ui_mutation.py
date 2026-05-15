from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable

UI_MUTATION_QUEUE_MAX = 1000


@dataclass
class UIMutation:
    target: str
    method: str
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)
    source: str | None = None


class UIMutationScheduler:
    def __init__(self, max_size: int = UI_MUTATION_QUEUE_MAX) -> None:
        self._queue: deque[UIMutation] = deque()
        self._lock = threading.Lock()
        self._max_size = max_size
        self._dropped_count = 0

    def schedule(self, mutation: UIMutation) -> bool:
        with self._lock:
            if len(self._queue) >= self._max_size:
                self._dropped_count += 1
                return False
            self._queue.append(mutation)
            return True

    def schedule_call(
        self,
        target: str,
        method: str,
        *args: Any,
        source: str | None = None,
        **kwargs: Any,
    ) -> bool:
        return self.schedule(
            UIMutation(
                target=target,
                method=method,
                args=args,
                kwargs=kwargs,
                source=source,
            )
        )

    def drain(self, max_items: int = 0) -> list[UIMutation]:
        with self._lock:
            if max_items:
                items = [self._queue.popleft() for _ in range(min(max_items, len(self._queue)))]
            else:
                items = list(self._queue)
                self._queue.clear()
        return items

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._queue)

    @property
    def dropped(self) -> int:
        with self._lock:
            return self._dropped_count

    def clear(self) -> None:
        with self._lock:
            self._queue.clear()
            self._dropped_count = 0
