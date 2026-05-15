from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, Callable

from aion.eventbus import Event, EventBus

TriggerCallback = Callable[[dict[str, Any]], None]


class TimerTrigger:
    def __init__(self, event_bus: EventBus) -> None:
        self._bus = event_bus
        self._timers: dict[str, threading.Thread] = {}
        self._running: dict[str, bool] = {}

    def start_interval(self, name: str, interval_seconds: float, topic: str, payload: dict[str, Any] | None = None) -> None:
        if name in self._timers:
            return
        self._running[name] = True

        def _run():
            from aion.eventbus import Priority
            while self._running.get(name, False):
                self._bus.emit(topic, payload or {}, priority=Priority.LOW)
                time.sleep(interval_seconds)

        t = threading.Thread(target=_run, daemon=True, name=f"timer-{name}")
        self._timers[name] = t
        t.start()

    def start_once(self, name: str, delay_seconds: float, topic: str, payload: dict[str, Any] | None = None) -> None:
        from aion.eventbus import Priority
        if name in self._timers:
            return
        self._running[name] = True

        def _run():
            time.sleep(delay_seconds)
            if self._running.get(name, False):
                self._bus.emit(topic, payload or {}, priority=Priority.NORMAL)
            self.stop(name)

        t = threading.Thread(target=_run, daemon=True, name=f"timer-{name}")
        self._timers[name] = t
        t.start()

    def stop(self, name: str) -> None:
        self._running[name] = False
        self._timers.pop(name, None)

    def stop_all(self) -> None:
        for name in list(self._running.keys()):
            self.stop(name)


class FileWatchTrigger:
    def __init__(self, event_bus: EventBus, poll_interval: float = 0.2) -> None:
        self._bus = event_bus
        self._poll_interval = poll_interval
        self._watches: dict[str, dict] = {}
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()

    def watch(self, path: str | Path, topic: str, interval: float = 1.0) -> None:
        path = str(path)
        with self._lock:
            self._watches[path] = {
                "topic": topic,
                "interval": interval,
                "last_mtime": Path(path).stat().st_mtime if Path(path).exists() else 0,
                "last_size": Path(path).stat().st_size if Path(path).exists() else 0,
            }
        self._ensure_running()

    def unwatch(self, path: str | Path) -> None:
        with self._lock:
            self._watches.pop(str(path), None)

    def _ensure_running(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="filewatch")
        self._thread.start()

    def _run(self) -> None:
        from aion.eventbus import Priority
        while self._running:
            with self._lock:
                for path, info in list(self._watches.items()):
                    p = Path(path)
                    if not p.exists():
                        continue
                    mtime = p.stat().st_mtime
                    size = p.stat().st_size
                    if mtime != info["last_mtime"] or size != info["last_size"]:
                        info["last_mtime"] = mtime
                        info["last_size"] = size
                        self._bus.emit(info["topic"], {"path": path, "mtime": mtime, "size": size}, priority=Priority.NORMAL)
            time.sleep(self._poll_interval)

    def stop(self) -> None:
        self._running = False


class WebhookTrigger:
    def __init__(self, event_bus: EventBus) -> None:
        self._bus = event_bus
        self._routes: dict[str, str] = {}

    def register(self, topic: str, source_pattern: str) -> None:
        self._routes[source_pattern] = topic

    def receive(self, source: str, payload: dict[str, Any]) -> None:
        topic = self._routes.get(source)
        if topic:
            self._bus.emit(topic, payload)


class AutomationEngine:
    def __init__(self, event_bus: EventBus) -> None:
        self._bus = event_bus
        self.timer = TimerTrigger(event_bus)
        self.file_watch = FileWatchTrigger(event_bus)
        self.webhook = WebhookTrigger(event_bus)

    def start_all(self) -> None:
        pass

    def stop_all(self) -> None:
        self.timer.stop_all()
        self.file_watch.stop()
