import time

from aion.eventbus import EventBus
from aion.automation_triggers import AutomationEngine, TimerTrigger, FileWatchTrigger, WebhookTrigger


class TestTimerTrigger:
    def test_start_once(self):
        bus = EventBus()
        tt = TimerTrigger(bus)
        results = []
        bus.subscribe("test.timer", lambda e: results.append(e))
        tt.start_once("t1", 0.05, "test.timer", {"msg": "once"})
        time.sleep(0.15)
        bus.process_all()
        assert len(results) == 1

    def test_stop(self):
        bus = EventBus()
        tt = TimerTrigger(bus)
        tt.start_interval("t2", 0.02, "test.interval")
        time.sleep(0.05)
        tt.stop("t2")
        count_before = bus.queue_size
        time.sleep(0.05)
        assert bus.queue_size == count_before


class TestFileWatchTrigger:
    def test_watch(self, tmp_path):
        bus = EventBus()
        fw = FileWatchTrigger(bus, poll_interval=0.05)
        results = []
        bus.subscribe("file.changed", lambda e: results.append(e))

        test_file = tmp_path / "watchme.txt"
        test_file.write_text("initial")
        fw.watch(str(test_file), "file.changed", interval=0.1)
        time.sleep(0.15)
        test_file.write_text("modified")
        time.sleep(0.3)
        fw.stop()
        bus.process_all()
        assert len(results) >= 1


class TestWebhookTrigger:
    def test_receive(self):
        bus = EventBus()
        wh = WebhookTrigger(bus)
        results = []
        bus.subscribe("webhook.data", lambda e: results.append(e))
        wh.register("webhook.data", "github")
        wh.receive("github", {"event": "push"})
        bus.process_all()
        assert len(results) == 1
        assert results[0].payload["event"] == "push"

    def test_unregistered_source(self):
        bus = EventBus()
        wh = WebhookTrigger(bus)
        results = []
        bus.subscribe("x", lambda e: results.append(e))
        wh.receive("unknown", {})
        assert len(results) == 0


class TestAutomationEngine:
    def test_create(self):
        bus = EventBus()
        engine = AutomationEngine(bus)
        assert engine.timer is not None
        assert engine.file_watch is not None
        assert engine.webhook is not None

    def test_stop_all(self):
        bus = EventBus()
        engine = AutomationEngine(bus)
        engine.timer.start_interval("t", 0.01, "x")
        engine.file_watch.watch("/dev/null", "x", interval=0.5)
        engine.stop_all()
        # should not raise
