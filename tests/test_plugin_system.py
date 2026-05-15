import tempfile
from pathlib import Path

from aion.plugin_system import (
    PluginRegistry, PluginManifest, RestrictedScope,
    CAPABILITY_FILESYSTEM_READ, SandboxError,
)


SAMPLE_PLUGIN = """
# @name: test_plugin
# @version: 1.0.0
# @description: A test plugin
# @hook: on_startup
# @capability: filesystem.read

def on_startup():
    print("Plugin started!")
"""


class TestPluginSystem:
    def test_restricted_scope(self):
        scope = RestrictedScope(["filesystem.read"])
        assert scope.check("filesystem.read") is True
        assert scope.check("network") is False
        scope.require("filesystem.read")  # should not raise
        import pytest
        with pytest.raises(SandboxError):
            scope.require("network")

    def test_manifest_creation(self):
        m = PluginManifest(name="p", version="1.0", hooks=["on_startup"], capabilities=["filesystem.read"])
        assert m.name == "p"
        assert m.hooks == ["on_startup"]

    def test_discover_loads_plugin(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_path = Path(tmpdir) / "my_plugin.py"
            plugin_path.write_text(SAMPLE_PLUGIN)
            registry = PluginRegistry(plugin_dir=tmpdir)
            discovered = registry.discover()
            assert "my_plugin" in discovered
            plugin = registry.get_plugin("test_plugin")
            assert plugin is not None
            assert plugin.manifest.name == "test_plugin"
            assert plugin.manifest.version == "1.0.0"

    def test_call_hook(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_path = Path(tmpdir) / "hook_plugin.py"
            plugin_path.write_text("""# @name: hooker
# @hook: on_tick
results = []
def on_tick():
    results.append(1)
""")
            registry = PluginRegistry(plugin_dir=tmpdir)
            registry.discover()
            results = registry.call_all("on_tick")
            assert "hooker" in results

    def test_unload_plugin(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_path = Path(tmpdir) / "unload_me.py"
            plugin_path.write_text("# @name: unloader\n# @hook: on_shutdown\ndef on_shutdown():\n    pass\n")
            registry = PluginRegistry(plugin_dir=tmpdir)
            registry.discover()
            assert registry.unload("unloader") is True
            assert registry.get_plugin("unloader") is None
            assert registry.unload("nope") is False

    def test_unload_all(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "p1.py").write_text("# @name: p1\n")
            (Path(tmpdir) / "p2.py").write_text("# @name: p2\n")
            registry = PluginRegistry(plugin_dir=tmpdir)
            registry.discover()
            assert len(registry.plugins) == 2
            registry.unload_all()
            assert len(registry.plugins) == 0
