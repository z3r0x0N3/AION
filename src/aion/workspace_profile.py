from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtWidgets import QMainWindow, QWidget

PROFILE_DIR = Path.home() / ".aion" / "profiles"


def _qbytearray_to_hex(qba: QByteArray) -> str:
    return bytes(qba).hex()


def _hex_to_qbytearray(hex_str: str) -> QByteArray:
    return QByteArray(bytes.fromhex(hex_str))


class WorkspaceProfileManager:
    def __init__(self, profile_dir: str | Path | None = None) -> None:
        self._profile_dir = Path(profile_dir) if profile_dir else PROFILE_DIR
        self._profile_dir.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, window: QMainWindow) -> Path:
        data = {
            "name": name,
            "window_geometry": _qbytearray_to_hex(window.saveGeometry()),
            "window_state": _qbytearray_to_hex(window.saveState()),
            "size": (window.width(), window.height()),
            "position": (window.x(), window.y()),
            "maximized": window.isMaximized(),
        }
        path = self._profile_dir / f"{name}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path

    def load(self, name: str, window: QMainWindow) -> bool:
        path = self._profile_dir / f"{name}.json"
        if not path.exists():
            return False
        try:
            with open(path) as f:
                data = json.load(f)
            geo_hex = data.get("window_geometry", "")
            state_hex = data.get("window_state", "")
            if geo_hex:
                window.restoreGeometry(_hex_to_qbytearray(geo_hex))
            if state_hex:
                window.restoreState(_hex_to_qbytearray(state_hex))
            return True
        except (json.JSONDecodeError, TypeError, ValueError, KeyError):
            return False

    def delete(self, name: str) -> bool:
        path = self._profile_dir / f"{name}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def list_profiles(self) -> list[str]:
        return sorted(p.stem for p in self._profile_dir.glob("*.json"))

    def profile_path(self, name: str) -> Path | None:
        path = self._profile_dir / f"{name}.json"
        return path if path.exists() else None
