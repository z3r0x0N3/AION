import tempfile
from pathlib import Path

from aion.action_registry import ActionRegistry


class TestActionRegistry:
    def test_register_and_execute(self):
        reg = ActionRegistry()
        results = []
        reg.register("test_action", "Ctrl+T", lambda: results.append(1), "Test action")
        assert reg.execute("test_action") is True
        assert results == [1]

    def test_execute_nonexistent(self):
        reg = ActionRegistry()
        assert reg.execute("nope") is False

    def test_rebind(self):
        reg = ActionRegistry()
        reg.register("a", "Ctrl+A", lambda: None)
        reg.register("b", "Ctrl+B", lambda: None)
        assert reg.rebind("a", "Ctrl+C") is True
        assert reg.get_binding("a").current_shortcut == "Ctrl+C"

    def test_conflict_detection(self):
        reg = ActionRegistry()
        reg.register("a", "Ctrl+A", lambda: None)
        reg.register("b", "Ctrl+B", lambda: None)
        conflict = reg.find_conflict("c", "Ctrl+A")
        assert conflict == "a"
        assert reg.find_conflict("a", "Ctrl+Z") is None

    def test_rebind_conflict_returns_false(self):
        reg = ActionRegistry()
        reg.register("a", "Ctrl+A", lambda: None)
        reg.register("b", "Ctrl+B", lambda: None)
        assert reg.rebind("b", "Ctrl+A") is False

    def test_get_binding(self):
        reg = ActionRegistry()
        reg.register("x", "Ctrl+X", lambda: None, description="X", category="edit")
        b = reg.get_binding("x")
        assert b.name == "x"
        assert b.default_shortcut == "Ctrl+X"
        assert b.description == "X"
        assert b.category == "edit"

    def test_all_bindings(self):
        reg = ActionRegistry()
        reg.register("a", "Ctrl+A", lambda: None)
        reg.register("b", "Ctrl+B", lambda: None)
        assert len(reg.all_bindings) == 2

    def test_category_filter(self):
        reg = ActionRegistry()
        reg.register("a", "Ctrl+A", lambda: None, category="nav")
        reg.register("b", "Ctrl+B", lambda: None, category="edit")
        assert len(reg.category("nav")) == 1
        assert len(reg.category("edit")) == 1

    def test_export_import(self):
        reg = ActionRegistry()
        reg.register("a", "Ctrl+A", lambda: None)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        try:
            reg.export_bindings(path)
            reg2 = ActionRegistry()
            reg2.register("a", "Ctrl+A", lambda: None)
            reg2.rebind("a", "Ctrl+Z")
            count = reg2.import_bindings(path)
            assert count == 1
            assert reg2.get_binding("a").current_shortcut == "Ctrl+A"
        finally:
            Path(path).unlink()
