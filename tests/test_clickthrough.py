"""Click-through validation script — exercises all interactive paths.

This is designed to be run with pytest-qt or manually against a running AION instance.
"""

import time

import pytest


@pytest.mark.skip(reason="Requires interactive Qt display")
class TestClickThrough:
    def test_main_window_opens(self, qapp):
        from aion.main_window import AionMainWindow
        window = AionMainWindow()
        window.show()
        assert window.isVisible()
        window.close()

    def test_add_remove_tabs(self, qapp):
        from aion.main_window import AionMainWindow
        from PyQt6.QtWidgets import QLabel
        window = AionMainWindow()
        window.show()
        idx1 = window.add_panel("Tab 1", QLabel("Content 1"))
        idx2 = window.add_panel("Tab 2", QLabel("Content 2"))
        assert window.tab_widget.count() == 2
        window.tab_widget.setCurrentIndex(1)
        assert window.tab_widget.currentIndex() == 1
        window.remove_panel(idx1)
        assert window.tab_widget.count() == 1
        window.close()

    def test_command_palette_opens(self, qapp):
        from aion.main_window import AionMainWindow
        window = AionMainWindow()
        window.show()
        window._show_command_palette()
        assert window._command_palette is not None
        assert window._command_palette.isVisible()
        window._command_palette.reject()
        window.close()

    def test_theme_switch(self, qapp):
        from aion.main_window import AionMainWindow
        from aion.theme import Theme
        window = AionMainWindow()
        window.show()
        new_theme = Theme({"theme_name": "test", "colors": {"background": "#ff0000"},
                           "typography": {}, "spacing": {}, "animation": {}})
        window.theme = new_theme
        assert window.theme.name == "test"
        window.close()

    def test_hex_grid_toggle(self, qapp):
        from aion.main_window import AionMainWindow
        window = AionMainWindow()
        window.show()
        window._toggle_hex_grid()
        assert window._hex_overlay.isVisible()
        window._toggle_hex_grid()
        assert not window._hex_overlay.isVisible()
        window.close()

    def test_detachable_panel(self, qapp):
        from aion.main_window import AionMainWindow
        from aion.detachable_panels import PanelManager
        from PyQt6.QtWidgets import QLabel
        window = AionMainWindow()
        window.show()
        mgr = PanelManager(window)
        mgr.add_panel("test", "Test", QLabel("hello"))
        assert mgr.float_panel("test") is True
        assert mgr.get_panel("test").isFloating()
        assert mgr.dock_panel("test") is True
        mgr.remove_panel("test")
        window.close()

    def test_status_bar(self, qapp):
        from aion.main_window import AionMainWindow
        window = AionMainWindow()
        window.show()
        window.set_status("Test message")
        assert "Test message" in window.statusBar().currentMessage()
        window.close()

    def test_save_load_profile(self, qapp, tmp_path):
        from aion.main_window import AionMainWindow
        from aion.workspace_profile import WorkspaceProfileManager
        window = AionMainWindow()
        mgr = WorkspaceProfileManager(tmp_path)
        mgr.save("clicktest", window)
        assert "clicktest" in mgr.list_profiles()
        assert mgr.load("clicktest", window) is True
        window.close()
