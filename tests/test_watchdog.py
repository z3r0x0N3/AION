import time

from aion.watchdog import EventLoopWatchdog


class TestEventLoopWatchdog:
    def test_tick_updates_last_tick(self):
        wd = EventLoopWatchdog(tick_interval=0.05)
        old = wd._last_tick
        time.sleep(0.01)
        wd.tick()
        assert wd._last_tick > old

    def test_stall_callback_invoked(self):
        wd = EventLoopWatchdog(
            tick_interval=0.02, stall_threshold=0.05, dump_threshold=0.2
        )
        stalls = []

        def on_stall(elapsed):
            stalls.append(elapsed)

        wd.on_stall(on_stall)
        wd._last_tick = time.monotonic() - 0.1
        wd.tick()
        assert len(stalls) >= 1
        assert stalls[0] >= 0.05

    def test_stall_detected_property(self):
        wd = EventLoopWatchdog(stall_threshold=0.05)
        wd._last_tick = time.monotonic() - 1.0
        assert wd.stall_detected
        wd.tick()
        assert not wd.stall_detected

    def test_reset(self):
        wd = EventLoopWatchdog(tick_interval=0.5)
        wd._last_tick = time.monotonic() - 100
        wd._pressure = 0.9
        wd._adaptive_interval = 2.0
        wd.reset()
        assert wd._pressure == 0.0
        assert wd._adaptive_interval == 0.5

    def test_adaptive_interval_increases_under_pressure(self):
        wd = EventLoopWatchdog(tick_interval=0.5)
        initial = wd._adaptive_interval
        wd._pressure = 0.8
        wd.tick()
        assert wd._adaptive_interval > initial

    def test_start_stop(self):
        wd = EventLoopWatchdog(tick_interval=0.05)
        wd.start()
        assert wd._running
        time.sleep(0.12)
        wd.stop()
        assert not wd._running
