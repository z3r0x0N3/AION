from __future__ import annotations

from enum import Enum

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout


class LayoutDensity(Enum):
    COMPACT = "compact"
    NORMAL = "normal"
    COMFORTABLE = "comfortable"


DENSITY_VALUES = {
    LayoutDensity.COMPACT: {"padding": 2, "margin": 2, "spacing": 2, "indent": 0},
    LayoutDensity.NORMAL: {"padding": 6, "margin": 4, "spacing": 4, "indent": 8},
    LayoutDensity.COMFORTABLE: {"padding": 12, "margin": 8, "spacing": 8, "indent": 16},
}


class DensityManager:
    def __init__(self) -> None:
        self._current = LayoutDensity.NORMAL
        self._listeners: list[callable] = []

    @property
    def current(self) -> LayoutDensity:
        return self._current

    @current.setter
    def current(self, density: LayoutDensity) -> None:
        self._current = density
        self._notify()

    def values(self) -> dict[str, int]:
        return DENSITY_VALUES[self._current]

    def apply_to_widget(self, widget: QWidget) -> None:
        v = self.values()
        if isinstance(widget, QVBoxLayout):
            widget.setSpacing(v["spacing"])
            widget.setContentsMargins(v["margin"], v["margin"], v["margin"], v["margin"])
        else:
            layout = widget.layout()
            if layout is not None:
                layout.setSpacing(v["spacing"])
                layout.setContentsMargins(v["margin"], v["margin"], v["margin"], v["margin"])

    def on_change(self, callback: callable) -> None:
        self._listeners.append(callback)

    def _notify(self) -> None:
        for cb in self._listeners:
            try:
                cb(self._current)
            except Exception:
                pass
