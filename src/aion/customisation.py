from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QComboBox, QFontComboBox, QSlider, QWidget, QVBoxLayout, QLabel, QHBoxLayout


@dataclass
class ComponentOverrides:
    font_family_ui: str | None = None
    font_family_mono: str | None = None
    font_size_ui: int | None = None
    font_size_mono: int | None = None
    background_opacity: float = 1.0
    animation_speed: float = 1.0


class CustomisationManager:
    def __init__(self) -> None:
        self._overrides: dict[str, ComponentOverrides] = {}
        self._global_speed: float = 1.0
        self._listeners: list[callable] = []

    def get_overrides(self, component: str) -> ComponentOverrides:
        if component not in self._overrides:
            self._overrides[component] = ComponentOverrides()
        return self._overrides[component]

    def set_font_family(self, component: str, family: str, mono: bool = False) -> None:
        ov = self.get_overrides(component)
        if mono:
            ov.font_family_mono = family
        else:
            ov.font_family_ui = family
        self._notify(component)

    def set_font_size(self, component: str, size: int, mono: bool = False) -> None:
        ov = self.get_overrides(component)
        if mono:
            ov.font_size_mono = size
        else:
            ov.font_size_ui = size
        self._notify(component)

    def set_opacity(self, component: str, opacity: float) -> None:
        ov = self.get_overrides(component)
        ov.background_opacity = max(0.0, min(1.0, opacity))
        self._notify(component)

    def set_animation_speed(self, component: str, speed: float) -> None:
        ov = self.get_overrides(component)
        ov.animation_speed = max(0.0, min(3.0, speed))
        self._notify(component)

    def set_global_speed(self, speed: float) -> None:
        self._global_speed = max(0.0, min(3.0, speed))

    @property
    def global_speed(self) -> float:
        return self._global_speed

    def on_change(self, callback: callable) -> None:
        self._listeners.append(callback)

    def _notify(self, component: str) -> None:
        for cb in self._listeners:
            try:
                cb(component)
            except Exception:
                pass

    def font_for(self, component: str, default_ui: str = "Inter", default_mono: str = "JetBrains Mono") -> dict[str, QFont]:
        ov = self._overrides.get(component, ComponentOverrides())
        ui_family = ov.font_family_ui or default_ui
        mono_family = ov.font_family_mono or default_mono
        ui_size = ov.font_size_ui or 13
        mono_size = ov.font_size_mono or 13
        return {
            "ui": QFont(ui_family, ui_size),
            "mono": QFont(mono_family, mono_size),
        }

    def animation_duration(self, base_ms: int, component: str = "global") -> int:
        ov = self._overrides.get(component, ComponentOverrides())
        speed = ov.animation_speed if component != "global" else self._global_speed
        if speed <= 0:
            return 0
        return int(base_ms / speed)
