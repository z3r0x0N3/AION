from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

from aion.semantic_manifold import SemanticManifold, SemanticNode


@dataclass
class HardConstraint:
    name: str
    weight: float = 1.0
    applies_to: str | None = None
    condition: Callable[[SemanticNode], bool] | None = None
    transform: Callable[[SemanticNode], SemanticNode] | None = None


@dataclass
class SoftConstraint:
    name: str
    weight: float = 1.0
    applies_to: str | None = None
    preference: Callable[[SemanticNode], float] | None = None


@dataclass
class CollapseResult:
    node_id: str
    original_vector: np.ndarray
    constrained_vector: np.ndarray
    hard_satisfied: list[str]
    soft_scores: dict[str, float]
    coherence: float


class ConstraintCollapseEngine:
    def __init__(self, manifold: SemanticManifold) -> None:
        self.manifold = manifold
        self._hard_constraints: list[HardConstraint] = []
        self._soft_constraints: list[SoftConstraint] = []
        self._lock = threading.RLock()
        self._collapse_count = 0
        self._total_latency = 0.0

    def add_hard_constraint(
        self,
        name: str,
        condition: Callable[[SemanticNode], bool] | None = None,
        transform: Callable[[SemanticNode], SemanticNode] | None = None,
        applies_to: str | None = None,
    ) -> None:
        with self._lock:
            self._hard_constraints.append(HardConstraint(
                name=name, weight=1.0, condition=condition,
                transform=transform, applies_to=applies_to,
            ))

    def add_soft_constraint(
        self,
        name: str,
        weight: float = 1.0,
        preference: Callable[[SemanticNode], float] | None = None,
        applies_to: str | None = None,
    ) -> None:
        with self._lock:
            self._soft_constraints.append(SoftConstraint(
                name=name, weight=weight, preference=preference,
                applies_to=applies_to,
            ))

    def collapse(self, node_id: str) -> CollapseResult | None:
        import time

        node = self.manifold.get(node_id)
        if node is None:
            return None

        start = time.monotonic()
        original_vector = node.vector.copy()
        current_vector = node.vector.copy()
        hard_satisfied: list[str] = []
        soft_scores: dict[str, float] = {}

        with self._lock:
            for constraint in self._hard_constraints:
                if constraint.applies_to and constraint.applies_to != node_id:
                    continue
                if constraint.condition and not constraint.condition(node):
                    hard_satisfied.append(constraint.name)
                    continue
                if constraint.transform:
                    node = constraint.transform(node)
                    current_vector = node.vector
                hard_satisfied.append(constraint.name)

            for constraint in self._soft_constraints:
                if constraint.applies_to and constraint.applies_to != node_id:
                    continue
                if constraint.preference:
                    score = constraint.preference(node) * constraint.weight
                    soft_scores[constraint.name] = score

            node.vector = current_vector
            node.confidence = min(
                1.0,
                node.confidence * (1.0 + len(hard_satisfied) * 0.05),
            )
            self.manifold.update_node(node)

        coherence = self._compute_coherence(current_vector, hard_satisfied)

        latency = time.monotonic() - start
        self._collapse_count += 1
        self._total_latency += latency

        return CollapseResult(
            node_id=node_id,
            original_vector=original_vector,
            constrained_vector=current_vector,
            hard_satisfied=hard_satisfied,
            soft_scores=soft_scores,
            coherence=coherence,
        )

    def collapse_all(self) -> list[CollapseResult]:
        results: list[CollapseResult] = []
        for nid in list(self.manifold.nodes.keys()):
            result = self.collapse(nid)
            if result:
                results.append(result)
        return results

    def _compute_coherence(
        self, vector: np.ndarray, satisfied: list[str]
    ) -> float:
        total = len(self._hard_constraints) + len(self._soft_constraints)
        if total == 0:
            return 1.0
        return len(satisfied) / total

    @property
    def average_latency(self) -> float:
        if self._collapse_count == 0:
            return 0.0
        return self._total_latency / self._collapse_count

    @property
    def collapse_count(self) -> int:
        return self._collapse_count

    def remove_constraint(self, name: str) -> bool:
        with self._lock:
            for clist in [self._hard_constraints, self._soft_constraints]:
                for i, c in enumerate(clist):
                    if c.name == name:
                        clist.pop(i)
                        return True
            return False

    def clear_constraints(self) -> None:
        with self._lock:
            self._hard_constraints.clear()
            self._soft_constraints.clear()
