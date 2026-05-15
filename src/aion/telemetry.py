from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TelemetrySample:
    timestamp: float
    frame_time_ms: float
    event_loop_lag_ms: float
    memory_mb: float
    mutation_count: int
    node_count: int


class PerformanceTelemetry:
    def __init__(self, log_dir: str | Path | None = None) -> None:
        self._log_dir = Path(log_dir) if log_dir else Path.home() / ".aion" / "telemetry"
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._samples: list[TelemetrySample] = []
        self._max_samples = 100_000
        self._start_time = time.monotonic()

    def sample(
        self,
        frame_time_ms: float = 0.0,
        event_loop_lag_ms: float = 0.0,
        memory_mb: float = 0.0,
        mutation_count: int = 0,
        node_count: int = 0,
    ) -> TelemetrySample:
        sample = TelemetrySample(
            timestamp=time.monotonic() - self._start_time,
            frame_time_ms=frame_time_ms,
            event_loop_lag_ms=event_loop_lag_ms,
            memory_mb=memory_mb,
            mutation_count=mutation_count,
            node_count=node_count,
        )
        self._samples.append(sample)
        if len(self._samples) > self._max_samples:
            self._samples.pop(0)
        return sample

    def save(self, name: str = "telemetry") -> Path:
        path = self._log_dir / f"{name}_{int(time.time())}.json"
        data = {
            "start_time": self._start_time,
            "duration": time.monotonic() - self._start_time,
            "samples": [
                {
                    "t": s.timestamp,
                    "ft": s.frame_time_ms,
                    "lag": s.event_loop_lag_ms,
                    "mem": s.memory_mb,
                    "mut": s.mutation_count,
                    "nodes": s.node_count,
                }
                for s in self._samples
            ],
            "summary": self.summary(),
        }
        path.write_text(json.dumps(data, indent=2))
        return path

    def summary(self) -> dict[str, float]:
        if not self._samples:
            return {}
        ft = [s.frame_time_ms for s in self._samples if s.frame_time_ms > 0]
        lag = [s.event_loop_lag_ms for s in self._samples]
        mem = [s.memory_mb for s in self._samples if s.memory_mb > 0]
        return {
            "frame_time_p50": _percentile(ft, 50) if ft else 0,
            "frame_time_p95": _percentile(ft, 95) if ft else 0,
            "frame_time_p99": _percentile(ft, 99) if ft else 0,
            "event_lag_p50": _percentile(lag, 50) if lag else 0,
            "event_lag_p95": _percentile(lag, 95) if lag else 0,
            "event_lag_p99": _percentile(lag, 99) if lag else 0,
            "memory_p50": _percentile(mem, 50) if mem else 0,
            "memory_growth_mb": (mem[-1] - mem[0]) if len(mem) >= 2 else 0,
            "memory_growth_rate_mb_per_hr": _growth_rate(mem) if len(mem) >= 10 else 0,
            "duration_seconds": self._samples[-1].timestamp if self._samples else 0,
            "sample_count": len(self._samples),
        }

    def clear(self) -> None:
        self._samples.clear()
        self._start_time = time.monotonic()


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = max(0, min(len(sorted_vals) - 1, int(len(sorted_vals) * p / 100)))
    return sorted_vals[idx]


def _growth_rate(values: list[float]) -> float:
    if len(values) < 10:
        return 0.0
    first = values[0]
    last = values[-1]
    delta = last - first
    return delta  # per-sample average (caller normalizes to time)
