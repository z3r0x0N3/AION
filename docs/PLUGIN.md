# AION Plugin Authoring Guide

## Plugin Structure

Plugins are Python files placed in `~/.aion/plugins/`. Each plugin must have a manifest header using `# @` annotations:

```python
# @name: my_plugin
# @version: 1.0.0
# @description: Does something useful
# @hook: on_startup
# @hook: on_tick
# @hook: on_shutdown
# @capability: filesystem.read

def on_startup():
    print("Plugin started!")

def on_tick():
    pass

def on_shutdown():
    pass
```

## Available Hooks

| Hook | When Called |
|------|-------------|
| `on_startup` | After plugin load |
| `on_tick` | Every engine tick |
| `on_event` | On matching EventBus event |
| `on_shutdown` | On engine shutdown |
| `on_salience_update` | After salience recomputation |
| `on_mutation` | After mutation event |

## Capabilities

| Capability | Description |
|------------|-------------|
| `filesystem.read` | Read files from disk |
| `filesystem.write` | Write files to disk |
| `network` | Make network requests |
| `subprocess` | Spawn child processes |
| `event_bus` | Access EventBus |
| `state_store` | Access StateStore |

## Sandbox

Plugins run in a restricted environment with only safe builtins available.
Capabilities must be declared in the manifest header to be granted.
Unrequested capabilities are denied at runtime.
