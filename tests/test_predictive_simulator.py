import pytest

from aion.semantic_manifold import SemanticManifold
from aion.predictive_simulator import RecursivePredictiveSimulator


@pytest.fixture
def manifold():
    m = SemanticManifold(vector_dim=8, max_nodes=100)
    for _ in range(20):
        m.create_node()
    m.rebuild_tree_if_needed()
    return m


class TestRecursivePredictiveSimulator:
    def test_simulate_returns_result(self, manifold):
        sim = RecursivePredictiveSimulator(manifold, beam_width=4, horizon=2)
        node = manifold.get_random_nodes(1)[0]
        result = sim.simulate(node.id)
        assert result is not None
        assert result.root_id == node.id
        assert len(result.branches) > 0
        assert result.best_branch is not None

    def test_simulate_nonexistent(self, manifold):
        sim = RecursivePredictiveSimulator(manifold)
        result = sim.simulate("nonexistent")
        assert result is None

    def test_branches_have_correct_horizon(self, manifold):
        sim = RecursivePredictiveSimulator(manifold, beam_width=3, horizon=3)
        node = manifold.get_random_nodes(1)[0]
        result = sim.simulate(node.id)
        assert result is not None
        if result.best_branch:
            # root + 3 horizon steps = 4 nodes
            assert len(result.best_branch.nodes) == 4

    def test_update_predictions(self, manifold):
        sim = RecursivePredictiveSimulator(manifold, beam_width=3, horizon=2)
        node = manifold.get_random_nodes(1)[0]
        sim.update_predictions(node.id)
        updated = manifold.get(node.id)
        assert updated is not None
        assert len(updated.predictions) > 0

    def test_beam_width_limited(self, manifold):
        sim = RecursivePredictiveSimulator(manifold, beam_width=3, horizon=2)
        node = manifold.get_random_nodes(1)[0]
        result = sim.simulate(node.id)
        assert result is not None
        assert len(result.branches) <= 3

    def test_simulation_tracking(self, manifold):
        sim = RecursivePredictiveSimulator(manifold)
        node = manifold.get_random_nodes(1)[0]
        sim.simulate(node.id)
        assert sim.simulation_count == 1
        assert sim.average_latency > 0
