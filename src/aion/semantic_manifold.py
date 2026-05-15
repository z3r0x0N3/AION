from __future__ import annotations

import pickle
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy.spatial import KDTree


@dataclass
class Prediction:
    target_id: str
    probability: float
    delta_vector: np.ndarray | None = None


@dataclass
class SemanticNode:
    id: str
    vector: np.ndarray
    salience: float = 0.1
    confidence: float = 1.0
    entropy: float = 0.0
    created: float = field(default_factory=time.monotonic)
    last_mutated: float = field(default_factory=time.monotonic)
    dependencies: set[str] = field(default_factory=set)
    predictions: list[Prediction] = field(default_factory=list)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SemanticNode):
            return self.id == other.id
        return False


class SemanticManifold:
    def __init__(
        self,
        vector_dim: int = 128,
        max_nodes: int = 1_000_000,
        topology_k: int = 8,
    ) -> None:
        self.vector_dim = vector_dim
        self.max_nodes = max_nodes
        self.topology_k = topology_k

        self._nodes: dict[str, SemanticNode] = {}
        self._vectors: dict[str, np.ndarray] = {}
        self._lock = threading.RLock()
        self._tree: KDTree | None = None
        self._tree_version = 0
        self._tree_lock = threading.RLock()

    def create_node(
        self,
        vector: np.ndarray | None = None,
        **kwargs: Any,
    ) -> SemanticNode:
        if vector is None:
            vector = np.random.randn(self.vector_dim).astype(np.float32)
            vector /= np.linalg.norm(vector) + 1e-8

        vector = vector.astype(np.float32)
        if vector.shape[0] != self.vector_dim:
            raise ValueError(
                f"Expected dim {self.vector_dim}, got {vector.shape[0]}"
            )

        node = SemanticNode(
            id=str(uuid.uuid4()),
            vector=vector,
            **kwargs,
        )

        with self._lock:
            if len(self._nodes) >= self.max_nodes:
                raise RuntimeError(
                    f"Manifold at capacity ({self.max_nodes} nodes)"
                )
            self._nodes[node.id] = node
            self._vectors[node.id] = vector
            self._invalidate_tree()

        return node

    def get(self, node_id: str) -> SemanticNode | None:
        with self._lock:
            return self._nodes.get(node_id)

    def get_vector(self, node_id: str) -> np.ndarray | None:
        with self._lock:
            return self._vectors.get(node_id)

    def update_node(self, node: SemanticNode) -> None:
        with self._lock:
            node.last_mutated = time.monotonic()
            self._nodes[node.id] = node
            self._vectors[node.id] = node.vector
            self._invalidate_tree()

    def remove_node(self, node_id: str) -> bool:
        with self._lock:
            if node_id not in self._nodes:
                return False
            del self._nodes[node_id]
            del self._vectors[node_id]
            self._invalidate_tree()
            for n in self._nodes.values():
                n.dependencies.discard(node_id)
            return True

    def nearest_neighbors(
        self, vector: np.ndarray, k: int = 8
    ) -> list[tuple[str, float]]:
        tree = self._get_tree()
        if tree is None or len(self._nodes) == 0:
            return []

        k = min(k, len(self._nodes))
        distances, indices = tree.query(vector.astype(np.float32), k=k)
        if k == 1:
            distances = [distances]
            indices = [indices]

        node_ids = list(self._nodes.keys())
        return [
            (node_ids[idx], float(dist))
            for idx, dist in zip(indices, distances)
        ]

    def similarity(
        self, node_a: SemanticNode, node_b: SemanticNode
    ) -> float:
        dot = float(np.dot(node_a.vector, node_b.vector))
        norm = float(
            np.linalg.norm(node_a.vector) * np.linalg.norm(node_b.vector)
        )
        return dot / (norm + 1e-8)

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._nodes)

    @property
    def nodes(self) -> dict[str, SemanticNode]:
        with self._lock:
            return dict(self._nodes)

    def get_random_nodes(self, n: int) -> list[SemanticNode]:
        import random

        with self._lock:
            if n >= len(self._nodes):
                return list(self._nodes.values())
            return random.sample(list(self._nodes.values()), n)

    def _get_tree(self) -> KDTree | None:
        with self._tree_lock:
            return self._tree

    def _invalidate_tree(self) -> None:
        with self._tree_lock:
            self._tree_version += 1
            self._tree = None

    def _rebuild_tree(self) -> None:
        with self._lock:
            if len(self._vectors) < 2:
                return
            ids = list(self._vectors.keys())
            mat = np.array([self._vectors[nid] for nid in ids], dtype=np.float32)
            with self._tree_lock:
                self._tree = KDTree(mat)
                self._tree._node_ids = ids

    def rebuild_tree_if_needed(self) -> None:
        with self._lock:
            if self._tree is None and len(self._vectors) >= 2:
                self._rebuild_tree()

    def prune_low_salience(self, threshold: float) -> int:
        with self._lock:
            to_remove = [
                nid
                for nid, node in self._nodes.items()
                if node.salience <= threshold
            ]
            for nid in to_remove:
                del self._nodes[nid]
                del self._vectors[nid]
            self._invalidate_tree()
            return len(to_remove)

    def serialize(self) -> bytes:
        with self._lock:
            data = {
                "vector_dim": self.vector_dim,
                "max_nodes": self.max_nodes,
                "topology_k": self.topology_k,
                "nodes": {
                    nid: {
                        "id": n.id,
                        "vector": n.vector.tobytes(),
                        "vector_shape": n.vector.shape,
                        "vector_dtype": n.vector.dtype.str,
                        "salience": n.salience,
                        "confidence": n.confidence,
                        "entropy": n.entropy,
                        "created": n.created,
                        "last_mutated": n.last_mutated,
                        "dependencies": list(n.dependencies),
                        "predictions": [
                            {
                                "target_id": p.target_id,
                                "probability": p.probability,
                                "delta_vector": (
                                    p.delta_vector.tobytes()
                                    if p.delta_vector is not None
                                    else None
                                ),
                            }
                            for p in n.predictions
                        ],
                    }
                    for nid, n in self._nodes.items()
                },
            }
            return pickle.dumps(data)

    @classmethod
    def deserialize(cls, data: bytes) -> SemanticManifold:
        loaded = pickle.loads(data)
        manifold = cls(
            vector_dim=loaded["vector_dim"],
            max_nodes=loaded["max_nodes"],
            topology_k=loaded["topology_k"],
        )
        for nid, ndata in loaded["nodes"].items():
            vector = np.frombuffer(
                ndata["vector"], dtype=np.dtype(ndata["vector_dtype"])
            ).reshape(ndata["vector_shape"])
            node = SemanticNode(
                id=ndata["id"],
                vector=vector,
                salience=ndata["salience"],
                confidence=ndata["confidence"],
                entropy=ndata["entropy"],
                created=ndata["created"],
                last_mutated=ndata["last_mutated"],
                dependencies=set(ndata["dependencies"]),
                predictions=[
                    Prediction(
                        target_id=p["target_id"],
                        probability=p["probability"],
                        delta_vector=(
                            np.frombuffer(p["delta_vector"], dtype=np.float32)
                            if p["delta_vector"] is not None
                            else None
                        ),
                    )
                    for p in ndata["predictions"]
                ],
            )
            manifold._nodes[nid] = node
            manifold._vectors[nid] = vector
        return manifold
