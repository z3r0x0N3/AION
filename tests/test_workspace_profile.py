import tempfile
from pathlib import Path

from PyQt6.QtWidgets import QMainWindow

from aion.workspace_profile import WorkspaceProfileManager


class TestWorkspaceProfile:
    def test_save_and_list(self, qapp):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = WorkspaceProfileManager(tmpdir)
            window = QMainWindow()
            mgr.save("test_profile", window)
            profiles = mgr.list_profiles()
            assert "test_profile" in profiles

    def test_load_nonexistent(self, qapp):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = WorkspaceProfileManager(tmpdir)
            window = QMainWindow()
            assert mgr.load("nope", window) is False

    def test_delete(self, qapp):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = WorkspaceProfileManager(tmpdir)
            window = QMainWindow()
            mgr.save("to_delete", window)
            assert mgr.delete("to_delete") is True
            assert mgr.delete("nope") is False
            assert "to_delete" not in mgr.list_profiles()

    def test_profile_path(self, qapp):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = WorkspaceProfileManager(tmpdir)
            window = QMainWindow()
            mgr.save("p1", window)
            path = mgr.profile_path("p1")
            assert path is not None
            assert path.exists()
            assert mgr.profile_path("nope") is None
