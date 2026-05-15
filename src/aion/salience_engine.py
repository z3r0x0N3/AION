from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

import numpy as np

from aion.semantic_manifold import SemanticManifold


@dataclass
class SalienceMap:
    node_scores: dict[str, float] = field(default_factory=dict)
    gradient: dict[str, float] = field(default_factory=dict)
    budget_remaining: float = 1.0


class SalienceEngine:
    def __init__(
        self,
        manifold: SemanticManifold,
        novelty_weight: float = 0.25,
        divergence_weight: float = 0.25,
        density_weight: float = 0.15,
        risk_weight: float = 0.2,
        utility_weight: float = 0.15,
        top_fraction: float = 0.05,
    ) -> None:
        self.manifold = manifold
        self.novelty_weight = novelty_weight
        self.divergence_weight = divergence_weight
        self.density_weight = density_weight
        self.risk_weight = risk_weight
        self.utility_weight = utility_weight
        self.top_fraction = top_fraction

        self._lock = threading.RLock()
        self._history: dict[str, list[float]] = {}
        self._max_history_len = 100

    def compute_salience_map(self) -> SalienceMap:
        self.manifold.rebuild_tree_if_needed()
        nodes = self.manifold.nodes
        if not nodes:
            return SalienceMap()

        scores: dict[str, float] = {}
        gradients: dict[str, float] = {}

        for nid, node in nodes.items():
            novelty = self._score_novelty(node)
            divergence = self._score_divergence(node)
            density = self._score_density(node)
            risk = self._score_risk(node)
            utility = self._score_utility(node)

            score = (
                self.novelty_weight * novelty
                + self.divergence_weight * divergence
                + self.density_weight * density
                + self.risk_weight * risk
                + self.utility_weight * utility
            )
            scores[nid] = score

            gradient = self._compute_gradient(node, scores)
            gradients[nid] = gradient

        total = sum(scores.values()) or 1.0
        normalized = {k: v / total for k, v in scores.items()}

        top_n = max(1, int(len(nodes) * self.top_fraction))
        top_ids = sorted(normalized, key=normalized.get, reverse=True)[:top_n]
        budget = sum(normalized[nid] for nid in top_ids)

        for nid, node in nodes.items():
            node.salience = normalized.get(nid, 0.0)
            self.manifold.update_node(node)

        return SalienceMap(
            node_scores=normalized,
            gradient=gradients,
            budget_remaining=budget,
        )

    def get_top_nodes(self, count: int) -> list[str]:
        salience_map = self.compute_salience_map()
        sorted_ids = sorted(
            salience_map.node_scores,
            key=salience_map.node_scores.get,
            reverse=True,
        )
        return sorted_ids[:count]

    def _score_novelty(self, node) -> float:
        neighbors = self.manifold.nearest_neighbors(
            node.vector, k=min(8, max(2, self.manifold.size))
        )
        if not neighbors:
            return 1.0
        avg_dist = sum(d for _, d in neighbors) / len(neighbors)
        return float(np.tanh(avg_dist))

    def _score_divergence(self, node) -> float:
        if not node.predictions:
            return 0.0
        errors = []
        for pred in node.predictions:
            target = self.manifold.get(pred.target_id)
            if target is None or pred.delta_vector is None:
                continue
            actual_delta = target.vector - node.vector
            error = float(
                np.linalg.norm(actual_delta - pred.delta_vector)
            )
            errors.append(error * pred.probability)
        return float(np.tanh(sum(errors) / (len(errors) + 1e-8)))

    def _score_density(self, node) -> float:
        neighbors = self.manifold.nearest_neighbors(
            node.vector, k=min(8, max(2, self.manifold.size))
        )
        if not neighbors:
            return 0.0
        avg_sim = sum(
            self.manifold.similarity(
                node, self.manifold.get(nid)
            )
            for nid, _ in neighbors
            if self.manifold.get(nid) is not None
        ) / len(neighbors)
        return float(1.0 - np.tanh(avg_sim * 3.0))

    def _score_risk(self, node) -> float:
        risk = node.entropy / (node.confidence + 1e-8)
        return float(np.tanh(risk))

    def _score_utility(self, node) -> float:
        with self._lock:
            history = self._history.get(node.id, [])
            if not history:
                return 0.5
            recent = history[-min(10, len(history)):]
            avg = sum(recent) / len(recent)
            return float(np.tanh(avg))

    def record_outcome(self, node_id: str, score: float) -> None:
        with self._lock:
            if node_id not in self._history:
                self._history[node_id] = []
            self._history[node_id].append(score)
            if len(self._history[node_id]) > self._max_history_len:
                self._history[node_id] = self._history[node_id][
                    -self._max_history_len:
                ]

    def _compute_gradient(self, node, scores: dict[str, float]) -> float:
        neighbors = self.manifold.nearest_neighbors(
            node.vector, k=min(8, max(2, self.manifold.size))
        )
        if not neighbors:
            return 0.0

        my_score = scores.get(node.id, 0.0)
        neighbor_scores = [
            scores.get(nid, 0.0)
            for nid, _ in neighbors
            if nid in scores
        ]
        if not neighbor_scores:
            return 0.0
        avg_neighbor = sum(neighbor_scores) / len(neighbor_scores)
        return my_score - avg_neighbor

    def allocate_budget(self, salience_map: SalienceMap) -> dict[str, float]:
        total_score = sum(salience_map.node_scores.values()) or 1.0
        return {
            nid: score / total_score
            for nid, score in salience_map.node_scores.items()
        }
