from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from aion.eventbus import Event

MatcherFunc = Callable[[Event], bool]
ActionFunc = Callable[[Event], None]


@dataclass
class NotificationRule:
    name: str
    matchers: list[MatcherFunc] = field(default_factory=list)
    actions: list[ActionFunc] = field(default_factory=list)
    enabled: bool = True
    _matcher_configs: list[dict[str, Any]] = field(default_factory=list)
    _action_configs: list[dict[str, Any]] = field(default_factory=list)


class NotificationRuleEngine:
    def __init__(self) -> None:
        self._rules: list[NotificationRule] = []
        self._listeners: list[Callable[[Event], None]] = []

    def add_rule(
        self,
        name: str,
        matchers: list[dict[str, Any]] | None = None,
        actions: list[dict[str, Any]] | None = None,
    ) -> NotificationRule:
        rule = NotificationRule(name=name)
        for m in (matchers or []):
            matcher = self._build_matcher(m)
            if matcher:
                rule.matchers.append(matcher)
                rule._matcher_configs.append(m)
        for a in (actions or []):
            action = self._build_action(a)
            if action:
                rule.actions.append(action)
                rule._action_configs.append(a)
        self._rules.append(rule)
        return rule

    def remove_rule(self, name: str) -> bool:
        for i, r in enumerate(self._rules):
            if r.name == name:
                self._rules.pop(i)
                return True
        return False

    def evaluate(self, event: Event) -> list[NotificationRule]:
        matched: list[NotificationRule] = []
        for rule in self._rules:
            if not rule.enabled:
                continue
            if all(m(event) for m in rule.matchers):
                matched.append(rule)
                for action in rule.actions:
                    try:
                        action(event)
                    except Exception:
                        import traceback
                        traceback.print_exc()
        return matched

    def _build_matcher(self, config: dict[str, Any]) -> MatcherFunc | None:
        match_type = config.get("type")
        value = config.get("value")

        if match_type == "event_type":
            return lambda e, v=value: e.topic == v
        elif match_type == "event_type_prefix":
            return lambda e, v=value: e.topic.startswith(v)
        elif match_type == "severity":
            from aion.eventbus import Priority
            prio_map = {"critical": Priority.CRITICAL, "high": Priority.HIGH,
                        "normal": Priority.NORMAL, "low": Priority.LOW}
            target = prio_map.get(value)
            return lambda e, t=target: e.priority == t.value if t else False
        elif match_type == "regex_payload":
            pattern = re.compile(value)
            return lambda e, p=pattern: any(
                isinstance(v, str) and p.search(v) for v in e.payload.values()
            )
        return None

    def _build_action(self, config: dict[str, Any]) -> ActionFunc | None:
        action_type = config.get("type")
        if action_type == "log":
            return lambda e: print(f"[NOTIFICATION] {e.topic}: {e.payload}")
        elif action_type == "callback":
            cb = config.get("callback")
            if callable(cb):
                return lambda e, c=cb: c(e)
        return None

    def enable_rule(self, name: str) -> bool:
        for r in self._rules:
            if r.name == name:
                r.enabled = True
                return True
        return False

    def disable_rule(self, name: str) -> bool:
        for r in self._rules:
            if r.name == name:
                r.enabled = False
                return True
        return False

    @property
    def rules(self) -> list[NotificationRule]:
        return list(self._rules)

    def clear(self) -> None:
        self._rules.clear()
