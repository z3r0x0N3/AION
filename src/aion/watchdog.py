from __future__ import annotations

import threading
import time
import traceback


class EventLoopWatchdog:
    def __init__(
        self,
        tick_interval: float = 0.5,
        stall_threshold: float = 5.0,
        dump_threshold: float = 12.0,
    ) -> None:
        self._tick_interval = tick_interval
        self._stall_threshold = stall_threshold
        self._dump_threshold = dump_threshold
        self._last_tick: float = time.monotonic()
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._stall_callbacks: list[callable] = []
        self._tick_count = 0
        self._adaptive_interval = tick_interval
        self._pressure = 0.0

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._last_tick = time.monotonic()
        self._thread = threading.Thread(target=self._run, daemon=True, name="watchdog")
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def tick(self) -> None:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_tick
            self._last_tick = now
            self._tick_count += 1

            if elapsed > self._dump_threshold:
                self._dump_stacks(elapsed)
                for cb in self._stall_callbacks:
                    try:
                        cb(elapsed)
                    except Exception:
                        traceback.print_exc()
            elif elapsed > self._stall_threshold:
                for cb in self._stall_callbacks:
                    try:
                        cb(elapsed)
                    except Exception:
                        traceback.print_exc()

            self._pressure = max(0.0, self._pressure - 0.1)
            if self._pressure > 0.5:
                base = self._adaptive_interval
                self._adaptive_interval = min(base * 2.0, base * (1.0 + self._pressure))
            else:
                self._adaptive_interval = max(
                    self._tick_interval, self._adaptive_interval * 0.95
                )

    def on_stall(self, callback: callable) -> None:
        self._stall_callbacks.append(callback)

    def _run(self) -> None:
        while self._running:
            self.tick()
            time.sleep(self._adaptive_interval)

    def _dump_stacks(self, elapsed: float) -> None:
        import sys

        now = time.monotonic()
        lines = [
            f"=== WATCHDOG: Event-loop stalled for {elapsed:.1f}s at {now} ===",
        ]
        for thread_id, frame in sys._current_frames().items():
            lines.append(f"\n--- Thread {thread_id} ---")
            for fname, lineno, func, code in traceback.extract_stack(frame):
                lines.append(f"  {fname}:{lineno} {func}")
        msg = "\n".join(lines)
        print(msg, file=sys.stderr)

    @property
    def stall_detected(self) -> bool:
        with self._lock:
            return (time.monotonic() - self._last_tick) > self._stall_threshold

    @property
    def uptime(self) -> float:
        with self._lock:
            return self._tick_count * self._adaptive_interval

    def reset(self) -> None:
        with self._lock:
            self._last_tick = time.monotonic()
            self._pressure = 0.0
            self._adaptive_interval = self._tick_interval
