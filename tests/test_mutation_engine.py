import numpy as np
import pytest

from aion.semantic_manifold import SemanticManifold
from aion.mutation_engine import MutationEngine, MutationOp


@pytest.fixture
def manifold():
    m = SemanticManifold(vector_dim=16, max_nodes=1000)
    for _ in range(50):
        m.create_node()
    return m


class TestMutationEngine:
    def test_spawn(self, manifold):
        engine = MutationEngine(manifold)
        source = manifold.get_random_nodes(1)[0]
        child = engine.spawn(source)
        assert child is not None
        assert child.id != source.id
        assert source.id in child.dependencies
        assert manifold.size == 51

    def test_merge(self, manifold):
        engine = MutationEngine(manifold)
        nodes = manifold.get_random_nodes(2)
        merged = engine.merge(nodes)
        assert merged is not None
        assert merged.id not in [n.id for n in nodes]
        assert manifold.size == 49  # 50 - 2 + 1

    def test_perturb(self, manifold):
        engine = MutationEngine(manifold)
        source = manifold.get_random_nodes(1)[0]
        original_vec = source.vector.copy()
        result = engine.perturb(source)
        assert result is not None
        assert result.id == source.id
        assert not np.allclose(result.vector, original_vec)

    def test_tick_increases_count(self, manifold):
        engine = MutationEngine(manifold, max_mutations_per_tick=50, spawn_rate=1.0, merge_rate=0, perturb_rate=0, prune_rate=0)
        count = engine.tick()
        assert count > 0
        assert count <= 50
        assert engine.mutation_count > 0

    def test_mutations_per_second(self, manifold):
        engine = MutationEngine(manifold)
        engine.tick()
        rate = engine.mutations_per_second
        # rate should report recent mutations (within last 1s)
        assert isinstance(rate, (int, float))

    def test_empty_manifold_no_mutations(self):
        m = SemanticManifold(vector_dim=8, max_nodes=100)
        engine = MutationEngine(m)
        count = engine.tick()
        assert count == 0

    def test_prune_removes_low_salience(self, manifold):
        for nid in list(manifold.nodes.keys())[:10]:
            node = manifold.get(nid)
            if node:
                node.salience = 0.001
                manifold.update_node(node)
        engine = MutationEngine(manifold, spawn_rate=0, merge_rate=0, perturb_rate=0, prune_rate=1.0)
        engine.tick()
        assert manifold.size < 50

    def test_start_stop(self, manifold):
        engine = MutationEngine(manifold, mutation_interval=0.01)
        engine.start()
        import time
        time.sleep(0.05)
        assert engine.mutation_count > 0
        engine.stop()
        time.sleep(0.1)  # give thread time to fully stop
        count_after = engine.mutation_count
        # Should not increase after thread has stopped
        time.sleep(0.05)
        assert engine.mutation_count == count_after

    def test_mutation_record_created(self, manifold):
        engine = MutationEngine(manifold)
        source = manifold.get_random_nodes(1)[0]
        engine.spawn(source)
        assert engine.mutation_count == 1
