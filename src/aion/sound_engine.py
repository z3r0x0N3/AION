from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QSoundEffect

SOUND_EVENTS = [
    "tab_switch",
    "button_click",
    "error",
    "warning",
    "success",
    "notification",
    "command_execute",
    "panel_open",
    "panel_close",
    "theme_change",
    "startup",
    "shutdown",
    "crash",
    "constraint_collapse",
    "mutation_spawn",
    "mutation_merge",
    "salience_shift",
    "drift_detected",
    "checkpoint_created",
    "profile_saved",
]

DEFAULT_SOUND_DIR = Path.home() / ".aion" / "sounds" / "default"


class SoundEngine:
    def __init__(self, sound_dir: str | Path | None = None) -> None:
        self._sound_dir = Path(sound_dir) if sound_dir else DEFAULT_SOUND_DIR
        self._sounds: dict[str, QSoundEffect] = {}
        self._muted = False
        self._volume: float = 0.5
        self._load_sounds()

    def _load_sounds(self) -> None:
        self._sound_dir.mkdir(parents=True, exist_ok=True)
        for event in SOUND_EVENTS:
            wav_path = self._sound_dir / f"{event}.wav"
            if wav_path.exists():
                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(str(wav_path)))
                effect.setVolume(self._volume)
                self._sounds[event] = effect

    def play(self, event: str) -> None:
        if self._muted:
            return
        effect = self._sounds.get(event)
        if effect is not None:
            effect.play()

    def set_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(1.0, volume))
        for effect in self._sounds.values():
            effect.setVolume(self._volume)

    def mute(self) -> None:
        self._muted = True

    def unmute(self) -> None:
        self._muted = False

    @property
    def muted(self) -> bool:
        return self._muted

    @property
    def volume(self) -> float:
        return self._volume

    @property
    def available_events(self) -> list[str]:
        return list(self._sounds.keys())

    def reload(self) -> None:
        self._sounds.clear()
        self._load_sounds()
