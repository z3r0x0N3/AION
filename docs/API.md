# AION API Reference

## EventBus

```python
from aion.eventbus import EventBus, Priority

bus = EventBus(max_size=10000)
bus.subscribe("topic", handler)
bus.subscribe_prefix("prefix.", handler)
bus.emit("topic", {"key": "value"}, priority=Priority.HIGH)
bus.process_next()
bus.process_all(max_events=100)
bus.wait_for_event("topic", timeout=5.0)
```

## StateStore

```python
from aion.statestore import StateStore

store = StateStore(db_path=":memory:")
store["key"] = {"data": 42}
value = store["key"]
del store["key"]
store.set_with_ttl("ephemeral", "val", ttl_seconds=10)
version = store.get_version("key")
store.atomic_update("counter", lambda x: x + 1)
store.get_many(["a", "b"])
```

## SemanticManifold

```python
from aion.semantic_manifold import SemanticManifold

m = SemanticManifold(vector_dim=128, max_nodes=1_000_000, topology_k=8)
node = m.create_node(vector=my_vector, salience=0.5)
node = m.get(node_id)
m.update_node(node)
m.remove_node(node_id)
neighbors = m.nearest_neighbors(vector, k=8)
m.prune_low_salience(threshold=0.01)
data = m.serialize()
m2 = SemanticManifold.deserialize(data)
```

## MutationEngine

```python
from aion.mutation_engine import MutationEngine

engine = MutationEngine(manifold)
engine.start()  # background thread
child = engine.spawn(source_node)
merged = engine.merge([node_a, node_b])
perturbed = engine.perturb(node)
count = engine.tick()  # synchronous mutation batch
engine.stop()
```

## SalienceEngine

```python
from aion.salience_engine import SalienceEngine

engine = SalienceEngine(manifold)
smap = engine.compute_salience_map()
top = engine.get_top_nodes(count=10)
engine.record_outcome(node_id, score=0.8)
```

## ConstraintCollapseEngine

```python
from aion.constraint_engine import ConstraintCollapseEngine

engine = ConstraintCollapseEngine(manifold)
engine.add_hard_constraint("name", condition=fn, transform=fn)
engine.add_soft_constraint("name", weight=2.0, preference=fn)
result = engine.collapse(node_id)
results = engine.collapse_all()
```

## RecursivePredictiveSimulator

```python
from aion.predictive_simulator import RecursivePredictiveSimulator

sim = RecursivePredictiveSimulator(manifold, beam_width=8, horizon=3)
result = sim.simulate(node_id)
sim.update_predictions(node_id)
```

## WorldModel

```python
from aion.world_model import WorldModel

wm = WorldModel(manifold, checkpoint_dir="~/.aion/checkpoints")
path = wm.checkpoint()
wm.restore_latest()
drift = wm.detect_drift()
if wm.has_critical_drift():
    wm.rollback()
```

## Theme System

```python
from aion.theme import Theme, load_theme, apply_theme, default_theme

theme = default_theme()
theme = load_theme("path/to/theme.json")
color = theme.color("accent_primary")
palette = theme.to_palette()
stylesheet = theme.to_stylesheet()
apply_theme(theme)
```

## Plugin System

```python
from aion.plugin_system import PluginRegistry

registry = PluginRegistry(plugin_dir="~/.aion/plugins")
discovered = registry.discover()
plugin = registry.get_plugin("my_plugin")
results = registry.call_all("on_startup")
```

## Export Pipeline

```python
from aion.export_pipeline import ExportPipeline, ExportOptions

pipe = ExportPipeline()
json_str = pipe.export(manifold, ExportOptions(format="json"))
csv_str = pipe.export(manifold, ExportOptions(format="csv"))
pipe.export_to_file(manifold, "export.html", ExportOptions(format="html"))
```

## Credential Providers

```python
from aion.credential_providers import CredentialManager

mgr = CredentialManager()
mgr.set("api_key", "secret", "file")
value = mgr.get("api_key", "file")
mgr.set_active("keyring")
```

## Thread Safety & Subprocess

```python
from aion.safe_subprocess import safe_subprocess_run, run_in_background

result = safe_subprocess_run(["ls"], timeout=30.0)
thread = run_in_background(["long_task"], callback=my_callback, timeout=60)
```

## Telemetry

```python
from aion.telemetry import PerformanceTelemetry

tel = PerformanceTelemetry()
tel.sample(frame_time_ms=16.7, memory_mb=120.5)
tel.save("benchmark_run")
summary = tel.summary()
```
