from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QLabel

from aion.detachable_panels import PanelManager, DetachablePanel


class TestDetachablePanels:
    def test_add_panel(self, qapp):
        window = QMainWindow()
        mgr = PanelManager(window)
        panel = mgr.add_panel("test", "Test Panel", QLabel("hello"))
        assert mgr.panel_count() == 1
        assert mgr.get_panel("test") is panel

    def test_remove_panel(self, qapp):
        window = QMainWindow()
        mgr = PanelManager(window)
        mgr.add_panel("p1", "P1", QLabel("a"))
        mgr.add_panel("p2", "P2", QLabel("b"))
        assert mgr.remove_panel("p1") is True
        assert mgr.panel_count() == 1
        assert mgr.remove_panel("nope") is False

    def test_float_and_dock(self, qapp):
        window = QMainWindow()
        mgr = PanelManager(window)
        mgr.add_panel("p", "P", QLabel("x"))
        assert mgr.float_panel("p") is True
        assert mgr.get_panel("p").isFloating()
        assert mgr.dock_panel("p") is True
        assert not mgr.get_panel("p").isFloating()

    def test_panel_names(self, qapp):
        window = QMainWindow()
        mgr = PanelManager(window)
        mgr.add_panel("a", "A", QLabel("1"))
        mgr.add_panel("b", "B", QLabel("2"))
        names = mgr.panel_names
        assert "a" in names
        assert "b" in names

    def test_get_nonexistent(self, qapp):
        window = QMainWindow()
        mgr = PanelManager(window)
        assert mgr.get_panel("nope") is None
