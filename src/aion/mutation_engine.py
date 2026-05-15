from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

from aion.semantic_manifold import SemanticManifold, SemanticNode


class MutationOp(Enum):
    SPAWN = "SPAWN"
    MERGE = "MERGE"
    PERTURB = "PERTURB"
    PRUNE = "PRUNE"


@dataclass
class MutationRecord:
    id: str
    source_id: str
    target_ids: list[str]
    operation: MutationOp
    delta_vector: np.ndarray | None
    confidence: float
    timestamp: float = field(default_factory=time.monotonic)


class MutationEngine:
    def __init__(
        self,
        manifold: SemanticManifold,
        mutation_interval: float = 0.01,
        max_mutations_per_tick: int = 100,
        spawn_rate: float = 0.4,
        merge_rate: float = 0.2,
        perturb_rate: float = 0.3,
        prune_rate: float = 0.1,
    ) -> None:
        self.manifold = manifold
        self.mutation_interval = mutation_interval
        self.max_mutations_per_tick = max_mutations_per_tick
        self.spawn_rate = spawn_rate
        self.merge_rate = merge_rate
        self.perturb_rate = perturb_rate
        self.prune_rate = prune_rate

        self._lock = threading.RLock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._history: list[MutationRecord] = []
        self._max_history = 100_000
        self._mutation_count = 0

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="mutation-engine"
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    @property
    def mutation_count(self) -> int:
        with self._lock:
            return self._mutation_count

    @property
    def mutations_per_second(self) -> float:
        with self._lock:
            if not self._history:
                return 0.0
            recent = [
                m
                for m in self._history
                if m.timestamp > time.monotonic() - 1.0
            ]
            return len(recent)

    def _run(self) -> None:
        while self._running:
            self.manifold.rebuild_tree_if_needed()
            self.tick()
            time.sleep(self.mutation_interval)

    def tick(self) -> int:
        if self.manifold.size < 2:
            return 0

        count = 0
        for _ in range(self.max_mutations_per_tick):
            op = self._select_operation()
            if op == MutationOp.SPAWN:
                success = self._do_spawn()
            elif op == MutationOp.MERGE:
                success = self._do_merge()
            elif op == MutationOp.PERTURB:
                success = self._do_perturb()
            elif op == MutationOp.PRUNE:
                success = self._do_prune()
            else:
                success = False

            if success:
                count += 1
        return count

    def _select_operation(self) -> MutationOp:
        rates = np.array([
            self.spawn_rate, self.merge_rate,
            self.perturb_rate, self.prune_rate,
        ], dtype=np.float32)
        total = rates.sum()
        if total <= 0:
            return MutationOp.SPAWN
        probs = rates / total
        r = np.random.random()
        cumulative = 0.0
        for op, prob in zip(
            [MutationOp.SPAWN, MutationOp.MERGE, MutationOp.PERTURB, MutationOp.PRUNE],
            probs,
        ):
            cumulative += prob
            if r < cumulative:
                return op
        return MutationOp.SPAWN

    def spawn(self, source: SemanticNode) -> SemanticNode | None:
        return self._spawn_from(source)

    def merge(
        self, nodes: list[SemanticNode]
    ) -> SemanticNode | None:
        return self._merge_nodes(nodes)

    def perturb(self, source: SemanticNode) -> SemanticNode | None:
        return self._perturb_node(source)

    def _do_spawn(self) -> bool:
        source = self._pick_source()
        if source is None:
            return False
        return self._spawn_from(source) is not None

    def _spawn_from(self, source: SemanticNode) -> SemanticNode | None:
        try:
            noise = np.random.randn(self.manifold.vector_dim).astype(np.float32) * 0.1
            child_vector = source.vector + noise
            child_vector /= np.linalg.norm(child_vector) + 1e-8

            child = self.manifold.create_node(
                vector=child_vector,
                salience=source.salience * 0.9,
                confidence=source.confidence * 0.8,
                entropy=source.entropy + 0.1,
                dependencies={source.id},
            )
            source.dependencies.add(child.id)
            self.manifold.update_node(source)

            self._record_mutation(
                source_id=source.id,
                target_ids=[child.id],
                operation=MutationOp.SPAWN,
                delta_vector=noise,
                confidence=source.confidence * 0.8,
            )
            return child
        except (RuntimeError, ValueError):
            return None

    def _do_merge(self) -> bool:
        candidates = self.manifold.get_random_nodes(2)
        if len(candidates) < 2:
            return False
        return self._merge_nodes(candidates) is not None

    def _merge_nodes(
        self, nodes: list[SemanticNode]
    ) -> SemanticNode | None:
        if len(nodes) < 2:
            return None
        try:
            vectors = [n.vector for n in nodes]
            weights = [n.confidence for n in nodes]
            w = np.array(weights, dtype=np.float32)
            w /= w.sum() + 1e-8

            merged_vector = np.zeros(self.manifold.vector_dim, dtype=np.float32)
            for vec, weight in zip(vectors, w):
                merged_vector += vec * weight
            merged_vector /= np.linalg.norm(merged_vector) + 1e-8

            avg_salience = sum(n.salience for n in nodes) / len(nodes)
            avg_confidence = sum(n.confidence for n in nodes) / len(nodes)
            avg_entropy = sum(n.entropy for n in nodes) / len(nodes)

            merged = self.manifold.create_node(
                vector=merged_vector,
                salience=avg_salience,
                confidence=min(1.0, avg_confidence * 1.1),
                entropy=avg_entropy * 0.8,
                dependencies={n.id for n in nodes},
            )

            for n in nodes:
                n.dependencies.add(merged.id)
                self.manifold.update_node(n)

            for n in nodes:
                self.manifold.remove_node(n.id)

            self._record_mutation(
                source_id=nodes[0].id,
                target_ids=[merged.id],
                operation=MutationOp.MERGE,
                delta_vector=merged_vector - nodes[0].vector,
                confidence=avg_confidence,
            )
            return merged
        except (RuntimeError, ValueError):
            return None

    def _do_perturb(self) -> bool:
        source = self._pick_source()
        if source is None:
            return False
        return self._perturb_node(source) is not None

    def _perturb_node(self, source: SemanticNode) -> SemanticNode | None:
        try:
            noise_scale = max(0.01, 1.0 - source.confidence)
            noise = (
                np.random.randn(self.manifold.vector_dim).astype(np.float32)
                * noise_scale
            )
            new_vector = source.vector + noise
            new_vector /= np.linalg.norm(new_vector) + 1e-8

            source.vector = new_vector
            source.salience *= 1.05
            source.entropy = max(0.0, source.entropy + np.random.randn() * 0.05)
            self.manifold.update_node(source)

            self._record_mutation(
                source_id=source.id,
                target_ids=[source.id],
                operation=MutationOp.PERTURB,
                delta_vector=noise,
                confidence=source.confidence,
            )
            return source
        except (RuntimeError, ValueError):
            return None

    def _do_prune(self) -> bool:
        if self.manifold.size < 10:
            return False
        threshold = self._estimate_salience_threshold()
        if threshold <= 0:
            return False
        removed = self.manifold.prune_low_salience(threshold)
        if removed > 0:
            self._record_mutation(
                source_id="pruner",
                target_ids=[],
                operation=MutationOp.PRUNE,
                delta_vector=None,
                confidence=0.5,
            )
            return True
        return False

    def _estimate_salience_threshold(self) -> float:
        nodes = list(self.manifold._nodes.values())
        if not nodes:
            return -1.0
        saliences = sorted(n.salience for n in nodes)
        if len(saliences) < 2:
            return -1.0
        idx = min(len(saliences) - 1, max(1, int(len(saliences) * 0.05)))
        return saliences[idx] * 1.0001  # slightly above cutoff to include equal values

    def _pick_source(self) -> SemanticNode | None:
        nodes = self.manifold.get_random_nodes(1)
        return nodes[0] if nodes else None

    def _record_mutation(
        self,
        source_id: str,
        target_ids: list[str],
        operation: MutationOp,
        delta_vector: np.ndarray | None,
        confidence: float,
    ) -> None:
        with self._lock:
            record = MutationRecord(
                id=str(uuid.uuid4()),
                source_id=source_id,
                target_ids=target_ids,
                operation=operation,
                delta_vector=delta_vector,
                confidence=confidence,
            )
            self._history.append(record)
            self._mutation_count += 1
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]
