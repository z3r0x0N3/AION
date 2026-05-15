from aion.action_registry import ActionRegistry
from aion.command_palette import CommandPalette


class TestCommandPalette:
    def test_create_palette(self, qapp):
        reg = ActionRegistry()
        reg.register("test", "Ctrl+T", lambda: None, "Test command")
        palette = CommandPalette(reg)
        assert palette.windowTitle() == "Commands"
        assert palette._list.count() == 1

    def test_filter_hides_items(self, qapp):
        reg = ActionRegistry()
        reg.register("alpha", "Ctrl+A", lambda: None, "Alpha command")
        reg.register("beta", "Ctrl+B", lambda: None, "Beta command")
        palette = CommandPalette(reg)
        assert palette._list.count() == 2
        palette._search.setText("beta")
        palette._filter()
        assert palette._list.item(0).isHidden()
        assert not palette._list.item(1).isHidden()
