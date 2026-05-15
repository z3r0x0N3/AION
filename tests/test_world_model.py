import time

import pytest

from aion.semantic_manifold import SemanticManifold
from aion.world_model import WorldModel


@pytest.fixture
def manifold():
    m = SemanticManifold(vector_dim=8, max_nodes=100)
    for _ in range(10):
        m.create_node()
    return m


class TestWorldModel:
    def _make_checkpoint(self, manifold, tmp_path):
        from aion.mutation_engine import MutationEngine
        me = MutationEngine(manifold, spawn_rate=1.0, merge_rate=0, perturb_rate=0, prune_rate=0)
        manifold._mutation_engine = me
        wm = WorldModel(manifold, checkpoint_dir=str(tmp_path), checkpoint_interval=1)
        for _ in range(5):
            me.tick()
        return wm.checkpoint()

    def test_checkpoint_creates_file(self, manifold, tmp_path):
        path = self._make_checkpoint(manifold, tmp_path)
        assert path is not None
        assert path.exists()

    def test_restore_latest(self, manifold, tmp_path):
        self._make_checkpoint(manifold, tmp_path)
        original_size = manifold.size
        wm2 = WorldModel(SemanticManifold(vector_dim=8), checkpoint_dir=str(tmp_path))
        restored = wm2.restore_latest()
        assert restored is not None
        assert restored.size == original_size

    def test_drift_detection(self, manifold):
        wm = WorldModel(manifold, drift_threshold=0.5)
        drift1 = wm.detect_drift()
        assert drift1 == 0.0  # first call sets baseline

        # alter the manifold
        node = manifold.get_random_nodes(1)[0]
        import numpy as np
        node.vector = np.random.randn(8).astype(np.float32)
        node.vector /= np.linalg.norm(node.vector)
        manifold.update_node(node)

        drift2 = wm.detect_drift()
        assert drift2 >= 0.0

    def test_critical_drift(self, manifold):
        wm = WorldModel(manifold, drift_threshold=0.01)
        wm.detect_drift()  # baseline

        # drastically alter manifold
        for nid in list(manifold.nodes.keys())[:5]:
            node = manifold.get(nid)
            if node:
                import numpy as np
                node.vector = np.random.randn(8).astype(np.float32)
                node.vector /= np.linalg.norm(node.vector)
                manifold.update_node(node)

        wm.detect_drift()
        assert wm.has_critical_drift()

    def test_rollback(self, manifold, tmp_path):
        self._make_checkpoint(manifold, tmp_path)
        original_ids = set(manifold.nodes.keys())
        manifold.prune_low_salience(0.5)
        after_ids = set(manifold.nodes.keys())
        assert after_ids != original_ids

        wm2 = WorldModel(manifold, checkpoint_dir=str(tmp_path))
        wm2.rollback()
        assert set(wm2.manifold.nodes.keys()) == original_ids

    def test_drift_rate(self, manifold):
        wm = WorldModel(manifold)
        wm.detect_drift()
        wm.detect_drift()
        rate = wm.get_drift_rate(window=10)
        assert rate >= 0.0
