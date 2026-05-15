from __future__ import annotations

import importlib.util
import os
import sys
import threading
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

HookCallback = Callable[..., None]


@dataclass
class PluginManifest:
    name: str
    version: str
    description: str = ""
    author: str = ""
    hooks: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)


CAPABILITY_DENY_ALL: list[str] = []
CAPABILITY_FILESYSTEM_READ = "filesystem.read"
CAPABILITY_FILESYSTEM_WRITE = "filesystem.write"
CAPABILITY_NETWORK = "network"
CAPABILITY_SUBPROCESS = "subprocess"
CAPABILITY_EVENT_BUS = "event_bus"
CAPABILITY_STATE_STORE = "state_store"

PLUGIN_DIR = Path.home() / ".aion" / "plugins"


class SandboxError(Exception):
    pass


class RestrictedScope:
    def __init__(self, capabilities: list[str]) -> None:
        self._capabilities = set(capabilities)

    def check(self, cap: str) -> bool:
        return cap in self._capabilities

    def require(self, cap: str) -> None:
        if not self.check(cap):
            raise SandboxError(f"Capability '{cap}' not granted")


class Plugin:
    def __init__(self, manifest: PluginManifest, module: object, scope: RestrictedScope) -> None:
        self.manifest = manifest
        self._module = module
        self.scope = scope
        self._hooks: dict[str, list[HookCallback]] = {}

    def register_hook(self, hook_name: str, callback: HookCallback) -> None:
        if hook_name not in self.manifest.hooks:
            raise ValueError(f"Hook '{hook_name}' not declared in manifest")
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)

    def call_hook(self, hook_name: str, *args: Any, **kwargs: Any) -> list[Any]:
        results: list[Any] = []
        for cb in self._hooks.get(hook_name, []):
            try:
                result = cb(*args, **kwargs)
                results.append(result)
            except Exception:
                traceback.print_exc()
        return results

    @property
    def name(self) -> str:
        return self.manifest.name


class PluginRegistry:
    def __init__(self, plugin_dir: str | Path | None = None) -> None:
        self._dir = Path(plugin_dir) if plugin_dir else PLUGIN_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._plugins: dict[str, Plugin] = {}
        self._lock = threading.RLock()

    def discover(self) -> list[str]:
        discovered: list[str] = []
        for path in self._dir.glob("*.py"):
            name = path.stem
            if name not in self._plugins:
                try:
                    self._load_plugin(path)
                    discovered.append(name)
                except Exception:
                    traceback.print_exc()
        return discovered

    def _load_plugin(self, path: Path) -> Plugin:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            raise SandboxError(f"Could not load plugin: {path}")

        module = importlib.util.module_from_spec(spec)
        manifest = self._extract_manifest(module, path)

        scope = RestrictedScope(manifest.capabilities)
        loaded_module = self._exec_in_sandbox(spec, module, scope)

        plugin = Plugin(manifest, loaded_module, scope)
        self._plugins[manifest.name] = plugin

        self._register_plugin_hooks(plugin)
        return plugin

    def _extract_manifest(self, module: object, path: Path) -> PluginManifest:
        manifest = PluginManifest(
            name=path.stem,
            version="0.1.0",
            hooks=[],
            capabilities=[],
        )
        source = path.read_text()
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith("# @name:"):
                manifest.name = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("# @version:"):
                manifest.version = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("# @description:"):
                manifest.description = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("# @hook:"):
                manifest.hooks.append(stripped.split(":", 1)[1].strip())
            elif stripped.startswith("# @capability:"):
                manifest.capabilities.append(stripped.split(":", 1)[1].strip())
        return manifest

    def _exec_in_sandbox(self, spec: object, module: object, scope: RestrictedScope) -> object:
        safe_builtins = {
            "print": print,
            "len": len,
            "range": range,
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "True": True,
            "False": False,
            "None": None,
            "isinstance": isinstance,
            "hasattr": hasattr,
            "getattr": getattr,
            "type": type,
            "ValueError": ValueError,
            "KeyError": KeyError,
            "RuntimeError": RuntimeError,
            "Exception": Exception,
            "max": max,
            "min": min,
            "sum": sum,
            "abs": abs,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "reversed": reversed,
            "open": self._sandboxed_open if scope.check(CAPABILITY_FILESYSTEM_READ) else _deny,
        }
        old_builtins = sys.modules.get("builtins").__dict__.copy() if hasattr(sys.modules.get("builtins"), "__dict__") else {}
        try:
            if spec.loader:
                spec.loader.exec_module(module)
        except Exception as e:
            raise SandboxError(f"Plugin execution failed: {e}") from e
        return module

    def _sandboxed_open(self, file: str, mode: str = "r"):
        if "w" in mode or "a" in mode or "+" in mode:
            scope = RestrictedScope([])
            scope.require(CAPABILITY_FILESYSTEM_WRITE)
        return open(file, mode)

    def _register_plugin_hooks(self, plugin: Plugin) -> None:
        for attr_name in dir(plugin._module):
            if attr_name.startswith("on_"):
                hook_name = attr_name
                callback = getattr(plugin._module, attr_name)
                if callable(callback):
                    if hook_name not in plugin.manifest.hooks:
                        plugin.manifest.hooks.append(hook_name)
                    plugin.register_hook(hook_name, callback)

    def get_plugin(self, name: str) -> Plugin | None:
        return self._plugins.get(name)

    @property
    def plugins(self) -> dict[str, Plugin]:
        return dict(self._plugins)

    def call_all(self, hook_name: str, *args: Any, **kwargs: Any) -> dict[str, list[Any]]:
        results: dict[str, list[Any]] = {}
        for name, plugin in self._plugins.items():
            results[name] = plugin.call_hook(hook_name, *args, **kwargs)
        return results

    def unload(self, name: str) -> bool:
        with self._lock:
            if name not in self._plugins:
                return False
            del self._plugins[name]
            return True

    def unload_all(self) -> None:
        with self._lock:
            self._plugins.clear()


def _deny(*args: Any, **kwargs: Any) -> None:
    raise SandboxError("Operation denied: capability not granted")
