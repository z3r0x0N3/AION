from __future__ import annotations

import os
import sys
import threading
import time
import traceback
from pathlib import Path


CRASH_LOG_DIR = Path.home() / ".aion"
CRASH_LOG_PATH = CRASH_LOG_DIR / "crash.log"
MAX_LOG_SIZE = 5 * 1024 * 1024

_suppress_dialog = False


def suppress_dialog(suppress: bool = True) -> None:
    global _suppress_dialog
    _suppress_dialog = suppress


def _ensure_log_dir() -> None:
    CRASH_LOG_DIR.mkdir(parents=True, exist_ok=True)


def _rotate_if_needed() -> None:
    if CRASH_LOG_PATH.exists() and CRASH_LOG_PATH.stat().st_size > MAX_LOG_SIZE:
        rotated = CRASH_LOG_PATH.with_suffix(".log.old")
        CRASH_LOG_PATH.rename(rotated)


def _write_crash_log(exc_type: type, exc_value: BaseException, tb: object) -> None:
    _ensure_log_dir()
    _rotate_if_needed()
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(CRASH_LOG_PATH, "a") as f:
        f.write(f"=== CRASH at {timestamp} ===\n")
        f.write(f"Type: {exc_type.__name__}\n")
        f.write(f"Value: {exc_value}\n")
        traceback.print_exception(exc_type, exc_value, tb, file=f)
        f.write("\n")


def _show_crash_dialog(exc_type: type, exc_value: BaseException) -> None:
    if _suppress_dialog:
        return
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox

        app = QApplication.instance()
        if app is None:
            raise ImportError("No QApplication")

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("AION — Fatal Error")
        msg.setText(f"An unrecoverable error occurred:\n{exc_type.__name__}: {exc_value}")
        msg.setInformativeText(
            f"Crash details written to:\n{CRASH_LOG_PATH}"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Close)
        msg.exec()
    except ImportError:
        print(
            f"FATAL: {exc_type.__name__}: {exc_value}",
            file=sys.stderr,
        )


_original_excepthook: object = sys.excepthook
_original_threading_excepthook: object = threading.excepthook


def _aion_excepthook(
    exc_type: type, exc_value: BaseException, tb: object
) -> None:
    _write_crash_log(exc_type, exc_value, tb)
    _show_crash_dialog(exc_type, exc_value)
    if callable(_original_excepthook):
        _original_excepthook(exc_type, exc_value, tb)


def _aion_threading_excepthook(args: threading.ExceptHookArgs) -> None:
    exc_type = args.exc_type or RuntimeError
    exc_value = args.exc_value or Exception("Unknown thread exception")
    tb = args.exc_traceback
    _write_crash_log(exc_type, exc_value, tb)
    _show_crash_dialog(exc_type, exc_value)
    if callable(_original_threading_excepthook):
        _original_threading_excepthook(args)


def install_crash_hooks() -> None:
    global _original_excepthook, _original_threading_excepthook  # noqa: PLW0603
    _original_excepthook = sys.excepthook
    sys.excepthook = _aion_excepthook
    _original_threading_excepthook = threading.excepthook
    threading.excepthook = _aion_threading_excepthook


def uninstall_crash_hooks() -> None:
    sys.excepthook = _original_excepthook  # type: ignore[assignment]
    threading.excepthook = _original_threading_excepthook  # type: ignore[assignment]
