from PyQt6.QtWidgets import QLabel, QWidget

from aion.tab_system import CyberTabWidget


class TestCyberTabWidget:
    def test_add_tab(self, qapp):
        tabs = CyberTabWidget()
        idx = tabs.addTab(QLabel("a"), "Tab A")
        assert idx == 0
        assert tabs.count() == 1
        assert tabs.tabText(0) == "Tab A"

    def test_remove_tab(self, qapp):
        tabs = CyberTabWidget()
        tabs.addTab(QLabel("a"), "A")
        tabs.addTab(QLabel("b"), "B")
        assert tabs.count() == 2
        tabs.removeTab(0)
        assert tabs.count() == 1

    def test_current_index(self, qapp):
        tabs = CyberTabWidget()
        tabs.addTab(QLabel("a"), "A")
        tabs.addTab(QLabel("b"), "B")
        tabs.setCurrentIndex(1)
        assert tabs.currentIndex() == 1

    def test_set_tab_text(self, qapp):
        tabs = CyberTabWidget()
        tabs.addTab(QLabel("a"), "Old")
        tabs.setTabText(0, "New")
        assert tabs.tabText(0) == "New"
