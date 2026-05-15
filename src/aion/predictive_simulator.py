from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from aion.semantic_manifold import SemanticManifold, SemanticNode, Prediction


@dataclass
class SimulationBranch:
    nodes: list[SemanticNode]
    probability: float
    score: float = 0.0


@dataclass
class SimulationResult:
    root_id: str
    branches: list[SimulationBranch]
    best_branch: SimulationBranch | None
    horizon: int


class RecursivePredictiveSimulator:
    def __init__(
        self,
        manifold: SemanticManifold,
        beam_width: int = 8,
        horizon: int = 3,
        exploration_noise: float = 0.05,
        discount: float = 0.9,
    ) -> None:
        self.manifold = manifold
        self.beam_width = beam_width
        self.horizon = horizon
        self.exploration_noise = exploration_noise
        self.discount = discount

        self._lock = threading.RLock()
        self._simulation_count = 0
        self._total_latency = 0.0

    def simulate(self, node_id: str) -> SimulationResult | None:
        import time

        root = self.manifold.get(node_id)
        if root is None:
            return None

        start = time.monotonic()

        beam: list[SimulationBranch] = [
            SimulationBranch(nodes=[root], probability=1.0, score=0.0)
        ]

        for step in range(self.horizon):
            new_beam: list[SimulationBranch] = []
            for branch in beam:
                current = branch.nodes[-1]
                children = self._expand(current, self.beam_width)
                for child_vec, prob in children:
                    child = self._make_prediction_node(
                        current, child_vec, prob, step
                    )
                    new_branch = SimulationBranch(
                        nodes=branch.nodes + [child],
                        probability=branch.probability * prob,
                        score=branch.score
                        + self._score_node(child) * (self.discount**step),
                    )
                    new_beam.append(new_branch)

            new_beam.sort(key=lambda b: b.score, reverse=True)
            beam = new_beam[: self.beam_width]

        best_branch = max(beam, key=lambda b: b.score) if beam else None

        latency = time.monotonic() - start
        self._simulation_count += 1
        self._total_latency += latency

        return SimulationResult(
            root_id=node_id,
            branches=beam,
            best_branch=best_branch,
            horizon=self.horizon,
        )

    def _expand(
        self, node: SemanticNode, count: int
    ) -> list[tuple[np.ndarray, float]]:
        candidates: list[tuple[np.ndarray, float]] = []

        neighbors = self.manifold.nearest_neighbors(
            node.vector, k=min(count, max(2, self.manifold.size))
        )

        for nid, dist in neighbors:
            neighbor = self.manifold.get(nid)
            if neighbor is None:
                continue
            direction = neighbor.vector - node.vector
            prob = float(np.exp(-dist))
            candidates.append((direction, prob))

        for _ in range(count - len(candidates)):
            noise = np.random.randn(self.manifold.vector_dim).astype(np.float32)
            noise *= self.exploration_noise
            noise /= np.linalg.norm(noise) + 1e-8
            prob = 0.1
            candidates.append((noise, prob))

        total_prob = sum(p for _, p in candidates) or 1.0
        candidates = [
            (vec, p / total_prob) for vec, p in candidates
        ]

        return candidates[:count]

    def _make_prediction_node(
        self,
        parent: SemanticNode,
        delta: np.ndarray,
        probability: float,
        step: int,
    ) -> SemanticNode:
        predicted_vector = parent.vector + delta
        predicted_vector /= np.linalg.norm(predicted_vector) + 1e-8

        predicted_entropy = parent.entropy + step * 0.05

        node = SemanticNode(
            id=f"pred_{parent.id}_{step}_{uuid4().hex[:8]}",
            vector=predicted_vector,
            salience=parent.salience * (1.0 - step * 0.1),
            confidence=parent.confidence * probability,
            entropy=min(1.0, predicted_entropy),
            dependencies={parent.id},
        )
        return node

    def update_predictions(self, node_id: str) -> None:
        node = self.manifold.get(node_id)
        if node is None:
            return

        result = self.simulate(node_id)
        if result is None or result.best_branch is None:
            return

        predictions: list[Prediction] = []
        for branch in result.branches[:3]:
            if len(branch.nodes) < 2:
                continue
            target = branch.nodes[1]
            delta = target.vector - node.vector
            predictions.append(
                Prediction(
                    target_id=target.id,
                    probability=branch.probability,
                    delta_vector=delta,
                )
            )

        node.predictions = predictions
        self.manifold.update_node(node)

    def _score_node(self, node: SemanticNode) -> float:
        info_gain = node.entropy * (1.0 - node.confidence)
        salience_bonus = node.salience
        return float(info_gain + salience_bonus)

    @property
    def simulation_count(self) -> int:
        return self._simulation_count

    @property
    def average_latency(self) -> float:
        if self._simulation_count == 0:
            return 0.0
        return self._total_latency / self._simulation_count


def uuid4() -> Any:
    import uuid

    return uuid.uuid4()
