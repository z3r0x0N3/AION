from aion.eventbus import EventBus, Event, Priority
from aion.notification_engine import NotificationRuleEngine


class TestNotificationEngine:
    def test_add_rule(self):
        engine = NotificationRuleEngine()
        rule = engine.add_rule("test_rule")
        assert rule.name == "test_rule"
        assert rule.enabled is True

    def test_remove_rule(self):
        engine = NotificationRuleEngine()
        engine.add_rule("r1")
        engine.add_rule("r2")
        assert engine.remove_rule("r1") is True
        assert len(engine.rules) == 1

    def test_evaluate_event_type_matcher(self):
        engine = NotificationRuleEngine()
        bus = EventBus()
        results = []

        engine.add_rule("alert", matchers=[
            {"type": "event_type", "value": "system.error"},
        ], actions=[
            {"type": "log"},
        ])

        event = Event(priority=Priority.NORMAL.value, timestamp=0.0, topic="system.error", payload={"msg": "fail"}, event_id="1")
        matched = engine.evaluate(event)
        assert len(matched) == 1

    def test_evaluate_unmatched(self):
        engine = NotificationRuleEngine()
        engine.add_rule("alert", matchers=[
            {"type": "event_type", "value": "system.error"},
        ])

        event = Event(priority=Priority.NORMAL.value, timestamp=0.0, topic="system.ok", payload={}, event_id="2")
        matched = engine.evaluate(event)
        assert len(matched) == 0

    def test_disabled_rule(self):
        engine = NotificationRuleEngine()
        engine.add_rule("r", matchers=[{"type": "event_type", "value": "x"}])
        engine.disable_rule("r")

        event = Event(priority=0, timestamp=0.0, topic="x", payload={}, event_id="3")
        matched = engine.evaluate(event)
        assert len(matched) == 0

    def test_enable_disable(self):
        engine = NotificationRuleEngine()
        engine.add_rule("r")
        assert engine.disable_rule("r") is True
        assert engine.enable_rule("r") is True
        assert engine.enable_rule("nope") is False
        assert engine.disable_rule("nope") is False

    def test_regex_matcher(self):
        engine = NotificationRuleEngine()
        engine.add_rule("regex", matchers=[
            {"type": "regex_payload", "value": "error|fail"},
        ])

        event = Event(priority=0, timestamp=0.0, topic="x", payload={"msg": "critical error"}, event_id="4")
        matched = engine.evaluate(event)
        assert len(matched) == 1

        event2 = Event(priority=0, timestamp=0.0, topic="x", payload={"msg": "everything ok"}, event_id="5")
        assert len(engine.evaluate(event2)) == 0

    def test_clear(self):
        engine = NotificationRuleEngine()
        engine.add_rule("r")
        engine.clear()
        assert len(engine.rules) == 0

    def test_prefix_matcher(self):
        engine = NotificationRuleEngine()
        engine.add_rule("r", matchers=[{"type": "event_type_prefix", "value": "system."}])

        event = Event(priority=0, timestamp=0.0, topic="system.error.disk", payload={}, event_id="6")
        assert len(engine.evaluate(event)) == 1

        event2 = Event(priority=0, timestamp=0.0, topic="app.event", payload={}, event_id="7")
        assert len(engine.evaluate(event2)) == 0
