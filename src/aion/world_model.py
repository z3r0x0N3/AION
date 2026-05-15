from __future__ import annotations

import hashlib
import os
import pickle
import threading
import time
from pathlib import Path

import numpy as np

from aion.semantic_manifold import SemanticManifold


class WorldModel:
    def __init__(
        self,
        manifold: SemanticManifold,
        checkpoint_dir: str | Path | None = None,
        checkpoint_interval: int = 1000,
        drift_threshold: float = 0.05,
    ) -> None:
        self.manifold = manifold
        self.checkpoint_dir = (
            Path(checkpoint_dir) if checkpoint_dir else Path.home() / ".aion" / "checkpoints"
        )
        self.checkpoint_interval = checkpoint_interval
        self.drift_threshold = drift_threshold

        self._lock = threading.RLock()
        self._last_checkpoint_mutation = 0
        self._last_hash: str | None = None
        self._drift_score: float = 0.0
        self._total_drift: float = 0.0
        self._drift_samples: list[float] = []
        self._max_drift_samples = 1000

        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    @property
    def drift_score(self) -> float:
        with self._lock:
            return self._drift_score

    @property
    def total_drift(self) -> float:
        with self._lock:
            return self._total_drift

    def checkpoint(self) -> Path | None:
        from aion.mutation_engine import MutationEngine

        mutation_count = 0
        if hasattr(self.manifold, "_mutation_engine"):
            mutation_count = self.manifold._mutation_engine.mutation_count

        if mutation_count - self._last_checkpoint_mutation < self.checkpoint_interval:
            return None

        self._last_checkpoint_mutation = mutation_count

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"checkpoint_{timestamp}_{mutation_count}.aion"
        path = self.checkpoint_dir / filename

        data = self.manifold.serialize()
        path.write_bytes(data)

        self._cleanup_old_checkpoints()

        return path

    def restore_latest(self) -> SemanticManifold | None:
        checkpoints = sorted(self.checkpoint_dir.glob("*.aion"))
        if not checkpoints:
            return None

        latest = checkpoints[-1]
        return self.restore(latest)

    def restore(self, path: Path) -> SemanticManifold | None:
        if not path.exists():
            return None
        try:
            data = path.read_bytes()
            manifold = SemanticManifold.deserialize(data)
            self.manifold = manifold
            self._last_hash = self._compute_hash(manifold)
            return manifold
        except (pickle.UnpicklingError, EOFError, KeyError, ValueError):
            return None

    def detect_drift(self) -> float:
        current_hash = self._compute_hash(self.manifold)
        if self._last_hash is None:
            self._last_hash = current_hash
            return 0.0

        if current_hash == self._last_hash:
            drift = 0.0
        else:
            diff_bits = sum(
                a != b for a, b in zip(
                    bin(int(current_hash, 16)),
                    bin(int(self._last_hash, 16)),
                )
            )
            drift = diff_bits / 256.0

        with self._lock:
            self._drift_score = drift
            self._total_drift += drift
            self._drift_samples.append(drift)
            if len(self._drift_samples) > self._max_drift_samples:
                self._drift_samples = self._drift_samples[
                    -self._max_drift_samples:
                ]

        self._last_hash = current_hash
        return drift

    def has_critical_drift(self) -> bool:
        return self._drift_score > self.drift_threshold

    def rollback(self) -> bool:
        manifold = self.restore_latest()
        return manifold is not None

    def _compute_hash(self, manifold: SemanticManifold) -> str:
        node_ids = sorted(manifold.nodes.keys())
        hasher = hashlib.sha256()
        for nid in node_ids:
            node = manifold.get(nid)
            if node is None:
                continue
            hasher.update(nid.encode())
            hasher.update(node.vector.tobytes())
        return hasher.hexdigest()

    def _cleanup_old_checkpoints(self, keep: int = 5) -> None:
        checkpoints = sorted(self.checkpoint_dir.glob("*.aion"))
        while len(checkpoints) > keep:
            oldest = checkpoints.pop(0)
            oldest.unlink(missing_ok=True)

    def get_drift_rate(self, window: int = 60) -> float:
        with self._lock:
            if len(self._drift_samples) < 2:
                return 0.0
            recent = self._drift_samples[-window:]
            return sum(recent) / len(recent) if recent else 0.0
