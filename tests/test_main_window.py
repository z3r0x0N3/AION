from aion.main_window import AionMainWindow
from aion.theme import default_theme


class TestAionMainWindow:
    def test_create_window(self, qapp):
        window = AionMainWindow()
        assert window.windowTitle() == "AION"
        assert window.width() == 1400
        assert window.height() == 900

    def test_theme_property(self, qapp):
        window = AionMainWindow()
        assert window.theme.name == "aion-cyber-dark"
        new_theme = default_theme()
        window.theme = new_theme
        assert window.theme is new_theme

    def test_add_remove_panel(self, qapp):
        from PyQt6.QtWidgets import QLabel
        window = AionMainWindow()
        default_count = window.tab_widget.count()
        label = QLabel("test")
        idx = window.add_panel("Test", label)
        assert idx >= 0
        assert window.tab_widget.count() == default_count + 1
        window.remove_panel(idx)
        assert window.tab_widget.count() == default_count

    def test_set_status(self, qapp):
        window = AionMainWindow()
        window.set_status("hello")
        assert "hello" in window.statusBar().currentMessage()

    def test_action_registry_defaults(self, qapp):
        window = AionMainWindow()
        reg = window.action_registry
        assert reg.get_binding("command_palette") is not None
        assert reg.get_binding("toggle_hex_grid") is not None
