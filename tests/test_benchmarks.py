"""Performance regression benchmarks for AION cognitive engine.

Run with: pytest tests/test_benchmarks.py --benchmark-only
"""

import time

import pytest


class TestCognitiveBenchmarks:
    def test_semantic_manifold_throughput(self, benchmark):
        from aion.semantic_manifold import SemanticManifold
        import numpy as np

        manifold = SemanticManifold(vector_dim=128, max_nodes=10_000)
        for _ in range(1000):
            manifold.create_node()
        manifold.rebuild_tree_if_needed()

        vec = np.random.randn(128).astype(np.float32)
        vec /= np.linalg.norm(vec)

        def query():
            manifold.nearest_neighbors(vec, k=8)

        benchmark.pedantic(query, rounds=50, iterations=10)

    def test_mutation_throughput(self, benchmark):
        from aion.semantic_manifold import SemanticManifold
        from aion.mutation_engine import MutationEngine

        manifold = SemanticManifold(vector_dim=32, max_nodes=1000)
        for _ in range(100):
            manifold.create_node()

        engine = MutationEngine(manifold, max_mutations_per_tick=50)

        def mutate():
            engine.tick()

        benchmark.pedantic(mutate, rounds=20, iterations=5)

    def test_salience_computation(self, benchmark):
        from aion.semantic_manifold import SemanticManifold
        from aion.salience_engine import SalienceEngine

        manifold = SemanticManifold(vector_dim=32, max_nodes=1000)
        for _ in range(200):
            manifold.create_node()
        manifold.rebuild_tree_if_needed()

        engine = SalienceEngine(manifold)

        benchmark(engine.compute_salience_map)

    def test_constraint_collapse_latency(self, benchmark):
        from aion.semantic_manifold import SemanticManifold
        from aion.constraint_engine import ConstraintCollapseEngine

        manifold = SemanticManifold(vector_dim=16, max_nodes=100)
        node = manifold.create_node()
        engine = ConstraintCollapseEngine(manifold)
        engine.add_hard_constraint("normalize")

        benchmark(engine.collapse, node.id)

    def test_predictive_simulation(self, benchmark):
        from aion.semantic_manifold import SemanticManifold
        from aion.predictive_simulator import RecursivePredictiveSimulator

        manifold = SemanticManifold(vector_dim=16, max_nodes=100)
        for _ in range(20):
            manifold.create_node()
        manifold.rebuild_tree_if_needed()
        node = manifold.get_random_nodes(1)[0]
        sim = RecursivePredictiveSimulator(manifold, beam_width=8, horizon=3)

        benchmark(sim.simulate, node.id)

    def test_state_store_read_write(self, benchmark):
        from aion.statestore import StateStore

        store = StateStore()
        for i in range(100):
            store[f"key_{i}"] = {"data": i * 10}

        def read_all():
            for i in range(100):
                _ = store.get_many([f"key_{i}"])

        benchmark.pedantic(read_all, rounds=30, iterations=5)

    def test_eventbus_throughput(self, benchmark):
        from aion.eventbus import EventBus, Priority

        bus = EventBus()
        results = []
        bus.subscribe("perf", lambda e: results.append(1))

        def emit_and_process():
            for _ in range(100):
                bus.emit("perf", {}, priority=Priority.NORMAL)
            bus.process_all()

        benchmark.pedantic(emit_and_process, rounds=30, iterations=5)

    def test_serialization(self, benchmark):
        from aion.semantic_manifold import SemanticManifold

        manifold = SemanticManifold(vector_dim=64, max_nodes=1000)
        for _ in range(500):
            manifold.create_node()

        def serialize():
            return manifold.serialize()

        result = benchmark(serialize)
        # verify round-trip
        from aion.semantic_manifold import SemanticManifold as SM
        restored = SM.deserialize(result)
        assert restored.size == 500
