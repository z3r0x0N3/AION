from aion.ui_mutation import UIMutationScheduler, UIMutation


class TestUIMutationScheduler:
    def test_schedule_and_drain(self):
        sched = UIMutationScheduler()
        mut = UIMutation(target="label", method="setText", args=("hello",))
        ok = sched.schedule(mut)
        assert ok
        assert sched.size == 1
        drained = sched.drain()
        assert len(drained) == 1
        assert drained[0].target == "label"
        assert sched.size == 0

    def test_schedule_call(self):
        sched = UIMutationScheduler()
        ok = sched.schedule_call("panel", "show", source="test")
        assert ok
        item = sched.drain(1)[0]
        assert item.target == "panel"
        assert item.method == "show"
        assert item.source == "test"

    def test_overflow(self):
        sched = UIMutationScheduler(max_size=3)
        sched.schedule(UIMutation("a", "m"))
        sched.schedule(UIMutation("b", "m"))
        sched.schedule(UIMutation("c", "m"))
        ok = sched.schedule(UIMutation("d", "m"))
        assert not ok
        assert sched.dropped == 1

    def test_drain_max_items(self):
        sched = UIMutationScheduler()
        for i in range(10):
            sched.schedule(UIMutation(f"t{i}", "m"))
        items = sched.drain(max_items=3)
        assert len(items) == 3
        assert sched.size == 7

    def test_clear(self):
        sched = UIMutationScheduler()
        sched.schedule(UIMutation("x", "m"))
        sched.schedule(UIMutation("y", "m"))
        assert sched.size == 2
        sched.clear()
        assert sched.size == 0
        assert sched.dropped == 0

    def test_empty_drain(self):
        sched = UIMutationScheduler()
        items = sched.drain()
        assert items == []
