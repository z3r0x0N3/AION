from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication

CURRENT_THEME: Theme | None = None


class Theme:
    def __init__(self, data: dict[str, Any], path: str | None = None) -> None:
        self._data = data
        self.path = path
        self._name: str = data.get("theme_name", "aion-cyber-dark")
        self._colors: dict[str, str] = data.get("colors", {})
        self._typography: dict[str, Any] = data.get("typography", {})
        self._spacing: dict[str, dict[str, int]] = data.get("spacing", {})
        self._animation: dict[str, Any] = data.get("animation", {})

    @property
    def name(self) -> str:
        return self._name

    def color(self, token: str) -> QColor:
        hex_color = self._colors.get(token, "#ffffff")
        return QColor(hex_color)

    def color_hex(self, token: str) -> str:
        return self._colors.get(token, "#ffffff")

    def font(self, family_key: str = "font_family_ui") -> QFont:
        family = self._typography.get(family_key, "Inter, sans-serif")
        return QFont(family.split(",")[0].strip())

    def font_size(self, size_key: str = "font_size_normal") -> int:
        return self._typography.get(size_key, 13)

    def spacing(self, density: str = "normal") -> dict[str, int]:
        return self._spacing.get(density, self._spacing.get("normal", {"padding": 8, "margin": 4, "gap": 4}))

    def animation_ms(self, key: str = "duration_medium_ms") -> int:
        return self._animation.get(key, 250)

    def to_palette(self) -> QPalette:
        p = QPalette()
        p.setColor(QPalette.ColorRole.Window, self.color("background"))
        p.setColor(QPalette.ColorRole.WindowText, self.color("text_primary"))
        p.setColor(QPalette.ColorRole.Base, self.color("background_secondary"))
        p.setColor(QPalette.ColorRole.AlternateBase, self.color("background_tertiary"))
        p.setColor(QPalette.ColorRole.ToolTipBase, self.color("surface"))
        p.setColor(QPalette.ColorRole.ToolTipText, self.color("text_primary"))
        p.setColor(QPalette.ColorRole.Text, self.color("text_primary"))
        p.setColor(QPalette.ColorRole.Button, self.color("surface"))
        p.setColor(QPalette.ColorRole.ButtonText, self.color("text_primary"))
        p.setColor(QPalette.ColorRole.BrightText, self.color("accent_primary"))
        p.setColor(QPalette.ColorRole.Link, self.color("accent_primary"))
        p.setColor(QPalette.ColorRole.Highlight, self.color("accent_primary"))
        p.setColor(QPalette.ColorRole.HighlightedText, self.color("text_primary"))
        return p

    def to_stylesheet(self) -> str:
        c = self._colors
        return f"""
            QMainWindow {{ background-color: {c.get("background", "#0a0e1a")}; }}
            QWidget {{ color: {c.get("text_primary", "#e2e8f0")}; font-family: {self._typography.get("font_family_ui", "Inter, sans-serif").split(",")[0].strip()}; }}
            QMenuBar {{ background-color: {c.get("background_secondary", "#111827")}; color: {c.get("text_primary", "#e2e8f0")}; }}
            QMenuBar::item:selected {{ background-color: {c.get("surface_hover", "#263548")}; }}
            QMenu {{ background-color: {c.get("surface", "#1e293b")}; border: 1px solid {c.get("border", "#2a3a5c")}; }}
            QMenu::item:selected {{ background-color: {c.get("surface_hover", "#263548")}; }}
            QTabWidget::pane {{ border: 1px solid {c.get("border", "#2a3a5c")}; background-color: {c.get("background_secondary", "#111827")}; }}
            QTabBar::tab {{ background-color: {c.get("background_tertiary", "#1a2235")}; color: {c.get("text_secondary", "#94a3b8")}; padding: 6px 12px; border: 1px solid {c.get("border", "#2a3a5c")}; }}
            QTabBar::tab:selected {{ background-color: {c.get("surface", "#1e293b")}; color: {c.get("accent_primary", "#00f0ff")}; }}
            QStatusBar {{ background-color: {c.get("background_secondary", "#111827")}; color: {c.get("text_secondary", "#94a3b8")}; }}
            QToolTip {{ background-color: {c.get("surface", "#1e293b")}; color: {c.get("text_primary", "#e2e8f0")}; border: 1px solid {c.get("border_focus", "#00f0ff")}; }}
        """


def load_theme(path: str | Path) -> Theme:
    with open(path) as f:
        data = json.load(f)
    theme = Theme(data, path=str(path))
    return theme


def apply_theme(theme: Theme) -> None:
    app = QApplication.instance()
    if app is None:
        return
    app.setPalette(theme.to_palette())
    app.setStyleSheet(theme.to_stylesheet())
    global CURRENT_THEME
    CURRENT_THEME = theme


CYBER_DARK_DEFAULT = {
    "theme_name": "aion-cyber-dark",
    "colors": {
        "background": "#0a0e1a",
        "background_secondary": "#111827",
        "background_tertiary": "#1a2235",
        "surface": "#1e293b",
        "surface_hover": "#263548",
        "border": "#2a3a5c",
        "border_focus": "#00f0ff",
        "text_primary": "#e2e8f0",
        "text_secondary": "#94a3b8",
        "text_accent": "#00f0ff",
        "accent_primary": "#00f0ff",
        "accent_secondary": "#ff00aa",
        "accent_warning": "#ffaa00",
        "accent_error": "#ff3355",
        "accent_success": "#00ff88",
        "glow_accent": "rgba(0, 240, 255, 0.3)",
        "glow_warning": "rgba(255, 170, 0, 0.3)",
        "glow_error": "rgba(255, 51, 85, 0.3)",
    },
    "typography": {
        "font_family_ui": "Inter, SF Pro, sans-serif",
        "font_family_mono": "JetBrains Mono, Fira Code, monospace",
        "font_size_small": 11,
        "font_size_normal": 13,
        "font_size_large": 15,
        "font_size_header": 18,
        "font_size_title": 24,
    },
    "spacing": {
        "compact": {"padding": 4, "margin": 2, "gap": 2},
        "normal": {"padding": 8, "margin": 4, "gap": 4},
        "comfortable": {"padding": 12, "margin": 8, "gap": 8},
    },
    "animation": {
        "duration_short_ms": 150,
        "duration_medium_ms": 250,
        "duration_long_ms": 400,
        "easing": "ease_in_out_quad",
        "global_speed_multiplier": 1.0,
    },
}


def default_theme() -> Theme:
    return Theme(CYBER_DARK_DEFAULT)
