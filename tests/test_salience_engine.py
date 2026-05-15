import pytest

from aion.semantic_manifold import SemanticManifold
from aion.salience_engine import SalienceEngine, SalienceMap


@pytest.fixture
def manifold():
    m = SemanticManifold(vector_dim=16, max_nodes=1000)
    for _ in range(20):
        m.create_node()
    return m


class TestSalienceEngine:
    def test_compute_salience_map(self, manifold):
        engine = SalienceEngine(manifold)
        smap = engine.compute_salience_map()
        assert isinstance(smap, SalienceMap)
        assert len(smap.node_scores) == 20
        total = sum(smap.node_scores.values())
        assert abs(total - 1.0) < 1e-6
        assert 0 <= smap.budget_remaining <= 1.0

    def test_get_top_nodes(self, manifold):
        engine = SalienceEngine(manifold, top_fraction=0.25)
        top = engine.get_top_nodes(3)
        assert len(top) == 3
        for nid in top:
            assert nid in manifold.nodes

    def test_record_outcome(self, manifold):
        engine = SalienceEngine(manifold)
        node = manifold.get_random_nodes(1)[0]
        engine.record_outcome(node.id, 0.8)
        engine.record_outcome(node.id, 0.6)
        smap = engine.compute_salience_map()
        assert node.id in smap.node_scores

    def test_allocate_budget(self, manifold):
        engine = SalienceEngine(manifold)
        smap = engine.compute_salience_map()
        budget = engine.allocate_budget(smap)
        assert len(budget) == 20
        total = sum(budget.values())
        assert abs(total - 1.0) < 1e-6

    def test_novelty_score(self, manifold):
        engine = SalienceEngine(manifold)
        node = manifold.get_random_nodes(1)[0]
        score = engine._score_novelty(node)
        assert 0.0 <= score <= 1.0

    def test_risk_score(self, manifold):
        engine = SalienceEngine(manifold)
        node = manifold.get_random_nodes(1)[0]
        score = engine._score_risk(node)
        assert 0.0 <= score <= 1.0

    def test_density_score(self, manifold):
        manifold.rebuild_tree_if_needed()
        engine = SalienceEngine(manifold)
        node = manifold.get_random_nodes(1)[0]
        score = engine._score_density(node)
        assert 0.0 <= score <= 1.0

    def test_empty_manifold(self):
        m = SemanticManifold(vector_dim=8)
        engine = SalienceEngine(m)
        smap = engine.compute_salience_map()
        assert len(smap.node_scores) == 0

    def test_salience_updates_node(self, manifold):
        engine = SalienceEngine(manifold)
        engine.compute_salience_map()
        for node in manifold.nodes.values():
            assert node.salience > 0
