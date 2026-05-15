import numpy as np
import pytest

from aion.semantic_manifold import SemanticManifold, SemanticNode
from aion.constraint_engine import ConstraintCollapseEngine


@pytest.fixture
def manifold():
    m = SemanticManifold(vector_dim=8, max_nodes=100)
    m.create_node(salience=0.5)
    m.create_node(salience=0.3)
    return m


class TestConstraintCollapseEngine:
    def test_collapse_with_hard_constraint(self, manifold):
        engine = ConstraintCollapseEngine(manifold)
        node = manifold.get_random_nodes(1)[0]
        original_vec = node.vector.copy()

        engine.add_hard_constraint(
            "normalize",
            transform=lambda n: SemanticNode(
                id=n.id,
                vector=n.vector / (np.linalg.norm(n.vector) + 1e-8),
                salience=n.salience,
                confidence=n.confidence,
                entropy=n.entropy,
                created=n.created,
                last_mutated=n.last_mutated,
                dependencies=n.dependencies,
                predictions=n.predictions,
            ),
        )

        result = engine.collapse(node.id)
        assert result is not None
        assert "normalize" in result.hard_satisfied

    def test_collapse_with_soft_constraint(self, manifold):
        engine = ConstraintCollapseEngine(manifold)
        node = manifold.get_random_nodes(1)[0]

        engine.add_soft_constraint(
            "high_salience",
            weight=2.0,
            preference=lambda n: n.salience,
        )

        result = engine.collapse(node.id)
        assert result is not None
        assert "high_salience" in result.soft_scores
        assert result.soft_scores["high_salience"] > 0

    def test_collapse_nonexistent(self, manifold):
        engine = ConstraintCollapseEngine(manifold)
        result = engine.collapse("nonexistent")
        assert result is None

    def test_collapse_all(self, manifold):
        engine = ConstraintCollapseEngine(manifold)
        results = engine.collapse_all()
        assert len(results) == 2

    def test_coherence(self, manifold):
        engine = ConstraintCollapseEngine(manifold)
        node = manifold.get_random_nodes(1)[0]

        engine.add_hard_constraint("c1")
        engine.add_hard_constraint("c2")

        result = engine.collapse(node.id)
        assert result is not None
        assert 0 <= result.coherence <= 1.0

    def test_remove_constraint(self, manifold):
        engine = ConstraintCollapseEngine(manifold)
        engine.add_hard_constraint("test_con")
        assert engine.remove_constraint("test_con") is True
        assert engine.remove_constraint("nonexistent") is False

    def test_clear_constraints(self, manifold):
        engine = ConstraintCollapseEngine(manifold)
        engine.add_hard_constraint("c1")
        engine.add_soft_constraint("c2")
        engine.clear_constraints()
        assert len(engine._hard_constraints) == 0
        assert len(engine._soft_constraints) == 0

    def test_latency_tracking(self, manifold):
        engine = ConstraintCollapseEngine(manifold)
        node = manifold.get_random_nodes(1)[0]
        engine.collapse(node.id)
        assert engine.collapse_count > 0
        assert engine.average_latency > 0
