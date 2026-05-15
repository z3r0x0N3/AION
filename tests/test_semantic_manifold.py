import numpy as np
import pytest

from aion.semantic_manifold import SemanticManifold, SemanticNode, Prediction


class TestSemanticManifold:
    def test_create_node(self):
        m = SemanticManifold(vector_dim=64, max_nodes=100)
        node = m.create_node()
        assert node.id is not None
        assert node.vector.shape == (64,)
        assert abs(np.linalg.norm(node.vector) - 1.0) < 1e-6
        assert node.salience == 0.1
        assert m.size == 1

    def test_create_node_with_vector(self):
        m = SemanticManifold(vector_dim=8)
        vec = np.ones(8, dtype=np.float32)
        vec /= np.linalg.norm(vec)
        node = m.create_node(vector=vec, salience=0.5)
        assert np.allclose(node.vector, vec)
        assert node.salience == 0.5

    def test_get_node(self):
        m = SemanticManifold(vector_dim=8)
        node = m.create_node()
        assert m.get(node.id) is node
        assert m.get("nonexistent") is None

    def test_update_node(self):
        m = SemanticManifold(vector_dim=8)
        node = m.create_node()
        node.salience = 0.9
        m.update_node(node)
        retrieved = m.get(node.id)
        assert retrieved is not None
        assert retrieved.salience == 0.9

    def test_remove_node(self):
        m = SemanticManifold(vector_dim=8)
        n1 = m.create_node()
        n2 = m.create_node()
        assert m.size == 2
        m.remove_node(n1.id)
        assert m.size == 1
        assert m.get(n1.id) is None

    def test_nearest_neighbors(self):
        m = SemanticManifold(vector_dim=8, max_nodes=100)
        nodes = [m.create_node() for _ in range(20)]
        m.rebuild_tree_if_needed()
        neighbors = m.nearest_neighbors(nodes[0].vector, k=3)
        assert len(neighbors) == 3
        assert neighbors[0][0] == nodes[0].id  # self is closest

    def test_similarity(self):
        m = SemanticManifold(vector_dim=8)
        n1 = m.create_node()
        n2 = m.create_node()
        sim = m.similarity(n1, n2)
        assert -1.0 <= sim <= 1.0

    def test_capacity_limit(self):
        m = SemanticManifold(vector_dim=4, max_nodes=3)
        m.create_node()
        m.create_node()
        m.create_node()
        with pytest.raises(RuntimeError, match="capacity"):
            m.create_node()

    def test_prune_low_salience(self):
        m = SemanticManifold(vector_dim=4, max_nodes=100)
        for i in range(10):
            s = i / 10.0
            m.create_node(salience=s)
        removed = m.prune_low_salience(0.3)
        assert removed >= 3
        for nid in list(m.nodes):
            assert m.get(nid) is None or m.get(nid).salience >= 0.3

    def test_serialize_deserialize(self):
        m = SemanticManifold(vector_dim=8, max_nodes=100)
        n1 = m.create_node(salience=0.5)
        n2 = m.create_node(salience=0.3, confidence=0.9)
        n1.dependencies.add(n2.id)
        n1.predictions.append(Prediction(target_id=n2.id, probability=0.75))
        m.update_node(n1)

        data = m.serialize()
        m2 = SemanticManifold.deserialize(data)

        assert m2.size == 2
        assert m2.vector_dim == 8
        r1 = m2.get(n1.id)
        r2 = m2.get(n2.id)
        assert r1 is not None
        assert r2 is not None
        assert r1.salience == 0.5
        assert r2.confidence == 0.9
        assert n1.id in r2.dependencies or n2.id in r1.dependencies

    def test_get_random_nodes(self):
        m = SemanticManifold(vector_dim=4, max_nodes=100)
        for _ in range(10):
            m.create_node()
        sampled = m.get_random_nodes(3)
        assert len(sampled) == 3

    def test_dimension_mismatch(self):
        m = SemanticManifold(vector_dim=64)
        bad_vec = np.ones(32, dtype=np.float32)
        with pytest.raises(ValueError, match="Expected dim"):
            m.create_node(vector=bad_vec)
