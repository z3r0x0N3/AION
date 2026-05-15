import os
import sys
import threading

import pytest

from aion.crash_hooks import (
    install_crash_hooks,
    uninstall_crash_hooks,
    suppress_dialog,
    CRASH_LOG_PATH,
)


class TestCrashHooks:
    def test_install_and_uninstall(self):
        suppress_dialog(True)
        old_excepthook = sys.excepthook
        old_threadhook = threading.excepthook
        install_crash_hooks()
        assert sys.excepthook is not old_excepthook
        assert threading.excepthook is not old_threadhook
        uninstall_crash_hooks()
        assert sys.excepthook is old_excepthook
        assert threading.excepthook is old_threadhook
        suppress_dialog(False)

    def test_crash_log_written(self):
        if CRASH_LOG_PATH.exists():
            CRASH_LOG_PATH.unlink()
        suppress_dialog(True)
        install_crash_hooks()
        try:
            raise ValueError("test_crash")
        except ValueError:
            sys.excepthook(*sys.exc_info())
        uninstall_crash_hooks()
        suppress_dialog(False)
        assert CRASH_LOG_PATH.exists()
        content = CRASH_LOG_PATH.read_text()
        assert "ValueError" in content
        assert "test_crash" in content

    def test_crash_log_rotation(self):
        CRASH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CRASH_LOG_PATH.write_text("x" * (6 * 1024 * 1024))
        old_size = CRASH_LOG_PATH.stat().st_size
        suppress_dialog(True)
        install_crash_hooks()
        try:
            raise RuntimeError("rotation_test")
        except RuntimeError:
            sys.excepthook(*sys.exc_info())
        uninstall_crash_hooks()
        suppress_dialog(False)
        assert CRASH_LOG_PATH.exists()
        rotated = CRASH_LOG_PATH.with_suffix(".log.old")
        assert rotated.exists()
        assert rotated.stat().st_size == old_size
        rotated.unlink()
