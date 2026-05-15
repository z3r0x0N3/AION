from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QWidget


ActionCallback = Callable[[], None]


@dataclass
class ActionBinding:
    name: str
    default_shortcut: str
    description: str
    current_shortcut: str | None = None
    category: str = "general"


class ActionRegistry:
    def __init__(self) -> None:
        self._actions: dict[str, ActionBinding] = {}
        self._callbacks: dict[str, ActionCallback] = {}
        self._widget_actions: dict[str, QAction] = {}

    def register(
        self,
        name: str,
        default_shortcut: str,
        callback: ActionCallback,
        description: str = "",
        category: str = "general",
    ) -> ActionBinding:
        binding = ActionBinding(
            name=name,
            default_shortcut=default_shortcut,
            description=description or name,
            current_shortcut=default_shortcut,
            category=category,
        )
        self._actions[name] = binding
        self._callbacks[name] = callback
        return binding

    def bind_to_widget(self, name: str, widget: QWidget) -> QAction | None:
        binding = self._actions.get(name)
        if binding is None:
            return None
        shortcut = binding.current_shortcut or binding.default_shortcut
        if not shortcut:
            return None
        action = QAction(widget)
        action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(self._callbacks.get(name, lambda: None))
        widget.addAction(action)
        self._widget_actions[name] = action
        return action

    def rebind(self, name: str, new_shortcut: str) -> bool:
        binding = self._actions.get(name)
        if binding is None:
            return False
        conflict = self.find_conflict(name, new_shortcut)
        if conflict:
            return False
        binding.current_shortcut = new_shortcut
        action = self._widget_actions.get(name)
        if action:
            action.setShortcut(QKeySequence(new_shortcut))
        return True

    def find_conflict(self, name: str, shortcut: str) -> str | None:
        for n, b in self._actions.items():
            if n == name:
                continue
            curr = b.current_shortcut or b.default_shortcut
            if curr and curr == shortcut:
                return n
        return None

    def execute(self, name: str) -> bool:
        cb = self._callbacks.get(name)
        if cb is None:
            return False
        cb()
        return True

    def get_binding(self, name: str) -> ActionBinding | None:
        return self._actions.get(name)

    @property
    def all_bindings(self) -> dict[str, ActionBinding]:
        return dict(self._actions)

    def export_bindings(self, path: str | Path) -> None:
        data = {
            name: {
                "name": b.name,
                "default_shortcut": b.default_shortcut,
                "current_shortcut": b.current_shortcut,
                "description": b.description,
                "category": b.category,
            }
            for name, b in self._actions.items()
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def import_bindings(self, path: str | Path) -> int:
        with open(path) as f:
            data = json.load(f)
        count = 0
        for name, info in data.items():
            if name in self._actions:
                self._actions[name].current_shortcut = info.get("current_shortcut")
                count += 1
        return count

    def category(self, cat: str) -> list[ActionBinding]:
        return [b for b in self._actions.values() if b.category == cat]
