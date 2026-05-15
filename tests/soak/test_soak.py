"""Long-session soak test for AION runtime stability.

Usage:
    pytest tests/soak/test_soak.py --soak-minutes=5
"""

import time

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--soak-minutes",
        action="store",
        default=0,
        type=int,
        help="Run soak test for N minutes (0 = skip)",
    )


@pytest.mark.soak
class TestSoak:
    @pytest.fixture
    def soak_duration(self, request):
        minutes = request.config.getoption("--soak-minutes")
        if minutes <= 0:
            pytest.skip("Soak test skipped (use --soak-minutes=N)")
        return minutes * 60

    def test_cognitive_engine_soak(self, soak_duration):
        from aion.semantic_manifold import SemanticManifold
        from aion.mutation_engine import MutationEngine
        from aion.salience_engine import SalienceEngine
        from aion.constraint_engine import ConstraintCollapseEngine
        from aion.world_model import WorldModel
        import tempfile

        manifold = SemanticManifold(vector_dim=32, max_nodes=10_000)
        for _ in range(100):
            manifold.create_node()

        mutation_engine = MutationEngine(manifold, mutation_interval=0.001)
        salience_engine = SalienceEngine(manifold)
        constraint_engine = ConstraintCollapseEngine(manifold)
        mutation_engine.start()

        with tempfile.TemporaryDirectory() as tmpdir:
            world = WorldModel(manifold, checkpoint_dir=tmpdir, checkpoint_interval=500)

            start = time.monotonic()
            last_mem_sample = start
            memory_samples = []
            crash = None

            try:
                while time.monotonic() - start < soak_duration:
                    salience_engine.compute_salience_map()

                    nodes = manifold.get_random_nodes(min(3, manifold.size))
                    for n in nodes:
                        constraint_engine.collapse(n.id)

                    world.detect_drift()

                    if time.monotonic() - last_mem_sample >= 60:
                        import psutil
                        proc = psutil.Process()
                        mem_mb = proc.memory_info().rss / 1024 / 1024
                        memory_samples.append(mem_mb)
                        last_mem_sample = time.monotonic()

                    mutation_engine.tick()
                    time.sleep(0.01)

            except Exception as e:
                crash = e
            finally:
                mutation_engine.stop()

            world.checkpoint()

            if crash:
                pytest.fail(f"Crash during soak: {crash}")

            if len(memory_samples) >= 2:
                growth = memory_samples[-1] - memory_samples[0]
                elapsed = time.monotonic() - start
                growth_per_hr = (growth / elapsed) * 3600 if elapsed > 0 else 0
                print(f"Soak results: {manifold.size} nodes, "
                      f"{mutation_engine.mutation_count} mutations, "
                      f"memory growth: {growth_per_hr:.1f} MB/hr")

    def test_eventbus_soak(self, soak_duration):
        from aion.eventbus import EventBus, Priority
        import threading

        bus = EventBus(max_size=100_000)
        received = []
        lock = threading.Lock()

        def handler(e):
            with lock:
                received.append(1)

        bus.subscribe("soak", handler)

        def emitter():
            end = time.monotonic() + soak_duration
            while time.monotonic() < end:
                try:
                    bus.emit("soak", {"t": time.monotonic()}, priority=Priority.NORMAL)
                except RuntimeError:
                    pass
                time.sleep(0.0005)

        threads = [threading.Thread(target=emitter, daemon=True) for _ in range(4)]
        for t in threads:
            t.start()

        start = time.monotonic()
        while time.monotonic() - start < soak_duration:
            bus.process_all(max_events=1000)
            time.sleep(0.001)

        for t in threads:
            t.join(timeout=1)

        bus.process_all()
        print(f"EventBus soak: {len(received)} events processed")
