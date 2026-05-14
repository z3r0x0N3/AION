# AION — Probabilistic Infinite-State Cognition Architecture

## Success Criteria, Deliverables & Development Plan

---

# 1. Executive Summary

AION is a bounded cognitive runtime that models an effectively infinite probabilistic state space by dynamically compressing uncertainty into coherent, actionable structure. It is not a brute-force state enumerator. It is a **salience-directed semantic optimization engine** that recursively allocates compute where informational gain is highest.

This document defines the success criteria, concrete deliverables, and a phased development plan for a production-grade AION system with a Cyber-style UX (inspired by GNOSIS), full cosmetic and functional customisability, and a smooth, freeze-free operator experience.

---

# 2. Success Criteria

## 2.1 Core Runtime (Cognitive Engine)

| Criterion | Threshold | Target | Stretch |
|-----------|-----------|--------|--------|
| Semantic state space capacity | 10^6 nodes | 10^9 latent states | Effectively unbounded via compression |
| State mutation throughput | 100 states/s | 1,000 states/s | 10,000 states/s |
| Constraint collapse latency | <500ms | <100ms | <10ms |
| Salience-directed compute allocation | 80% of compute on top-5% salience | 90% on top-3% | 95% on top-1% |
| Recursive prediction horizon | 3 steps | 10 steps | 50 steps |
| Persistent world model drift | <5%/hr | <1%/hr | <0.1%/hr |
| Thread safety (event bus, store, state) | No crashes under concurrent load | Zero data races | Formal verification |

## 2.2 UX — Cyber-Style Interface

| Criterion | Threshold | Target | Stretch |
|-----------|-----------|--------|--------|
| UI freeze events | <1 per 10 min | 0 per hour | 0 per 8-hour session |
| Startup to interactive | <5s | <2s | <800ms |
| Frame rate (idle) | 30 fps | 60 fps | 120 fps |
| Frame rate (under load) | 15 fps | 30 fps | 60 fps |
| Event loop lag (p95) | <100ms | <16ms | <8ms |
| Tab switch latency | <200ms | <50ms | <16ms |

### Visual Design — Cyber-Style Aesthetics

| Element | Specification |
|---------|--------------|
| Color palette | Dark background (#0a0e1a), cyan accent (#00f0ff), magenta accent (#ff00aa), amber for warnings (#ffaa00) |
| Typography | JetBrains Mono (terminal/data), Inter or SF Pro (UI labels), monospace throughout data displays |
| Glow effects | QGraphicsDropShadowEffect with cyan glow on active elements, magenta on alerts |
| Scan lines | Optional CRT scan-line overlay with configurable opacity (0-30%) |
| Terminal aesthetic | QPlainTextEdit with dark background, green/cyan text, optional phosphor decay effect |
| Animations | 150-250ms ease-in-out for panels, 300ms for modal transitions |
| Hex grid | Background decorative hex grid (optional, configurable density and opacity) |
| Particle trails | Optional cursor particle effects for cyber-ambience (toggleable) |

## 2.3 Customisability

### Cosmetic Customisation

| Feature | Implementation |
|---------|---------------|
| Theme system | JSON-based theme files with full colour map (~60 tokens) |
| Accent colour | User-selectable from palette or hex input |
| Font family/size | Per-component font overrides (terminal, UI, labels, monospace) |
| Background opacity | Separate bg/fg opacity sliders per pane |
| Animation speed | Global multiplier (0=off, 0.5x, 1x, 1.5x, 2x) |
| Scan-line/CRT effect | Toggle + intensity slider |
| Hex grid overlay | Toggle + density + opacity + animation speed |
| Sound theme | Replaceable sound pack directory (~20 UI sound events) |
| Layout density | Compact / Normal / Comfortable (affects padding and margins) |
| Window chrome | Titlebar style, window opacity, border radius |

### Functional Customisation

| Feature | Implementation |
|---------|---------------|
| Tab/panel layout | Drag-reorderable tabs, detachable panels into floating windows |
| Keyboard shortcuts | Full rebindable action registry with conflict detection |
| Command palette | Fuzzy-searchable action palette (Ctrl+P) |
| Workspace profiles | Save/load named workspace layouts (tab order, panel visibility, sizes) |
| Plugin system | Python plugin API with sandboxed execution, hook registration |
| Data sources | Configurable project roots, git remotes, API endpoints |
| Notification rules | Per-event-type threshold, mute, redirect to log |
| Export formats | JSON, CSV, HRF, HTML report, PDF (configurable template) |
| Automation triggers | Timer-based, file-watch, event-based, webhook-incoming |
| Credential providers | OS keyring, encrypted file, environment variable, external vault |

---

# 3. Deliverables

## Phase 0 — Foundation (Week 1-2)

| Deliverable | Description | Acceptance |
|-------------|-------------|------------|
| D0.1 | Thread-safe EventBus with bounded priority queue and prefix routing | 43 tests passing, no data races under 1000 concurrent emits |
| D0.2 | Thread-safe StateStore with SQLite backend | Cross-thread read/write passing, no `ProgrammingError` |
| D0.3 | UI mutation scheduler with overflow protection | `UI_MUTATION_QUEUE_MAX` enforced, no stall on handler exception |
| D0.4 | Event-loop watchdog with adaptive tick interval | Logs ≥5s stalls, dumps stack at ≥12s |
| D0.5 | Global crash hooks (sys.excepthook + threading.excepthook) | Writes to `~/.aion/crash.log`, shows QMessageBox |

## Phase 1 — Core Cognitive Engine (Week 3-6)

| Deliverable | Description | Acceptance |
|-------------|-------------|------------|
| D1.1 | Semantic probability manifold (latent state representation) | 10^6 node capacity, 100 state/s mutation |
| D1.2 | Continuous mutation engine (evolutionary state search) | Mutates trajectories, merges overlapping hypotheses |
| D1.3 | Salience engine (attention-directed compute allocation) | 80% compute on top-5% salience nodes |
| D1.4 | Constraint collapse engine (hard/soft constraint application) | <500ms collapse latency |
| D1.5 | Recursive predictive simulation (MCTS-style beam search) | 3-step prediction horizon |
| D1.6 | Persistent world model with temporal continuity | <5%/hr drift |

## Phase 2 — Cyber-Style UX Shell (Week 7-10)

| Deliverable | Description | Acceptance |
|-------------|-------------|------------|
| D2.1 | Qt6-based main window with dark cyber theme | Startup <5s, 60fps idle |
| D2.2 | Cyber visual components (hex grid, glow, scan-lines, particles) | Toggleable, configurable intensity |
| D2.3 | Tabbed multi-pane layout with drag-reorder | <200ms tab switch |
| D2.4 | Command palette with fuzzy search | Ctrl+P, <100ms search latency |
| D2.5 | Theme system with 60+ colour tokens | Load from JSON, hot-reload |
| D2.6 | Action registry with rebindable shortcuts | Conflict detection, export/import bindings |
| D2.7 | Sound engine with replaceable sound packs | 20 UI events, pack directory |
| D2.8 | Workspace profile save/load | Full panel layout, sizes, visibility |

## Phase 3 — Customisability (Week 11-14)

| Deliverable | Description | Acceptance |
|-------------|-------------|------------|
| D3.1 | Font/opacity/animation speed controls | Per-component overrides |
| D3.2 | Layout density presets (Compact/Normal/Comfortable) | Immediate apply |
| D3.3 | Detachable panels into floating windows | Drag tab out, re-dock |
| D3.4 | Plugin API with sandboxed Python execution | Hook registry, capability gating |
| D3.5 | Notification rules engine | Per-event-type routing |
| D3.6 | Export pipeline (JSON/CSV/HRF/HTML/PDF) | Configurable templates |
| D3.7 | Automation triggers (timer, file-watch, event, webhook) | Rule chain execution |
| D3.8 | Credential provider abstraction (keyring, file, env, vault) | Pluggable backend |

## Phase 4 — Integration & Hardening (Week 15-18)

| Deliverable | Description | Acceptance |
|-------------|-------------|------------|
| D4.1 | Full subprocess timeout coverage (100% of UI-thread calls) | 0 untimed calls |
| D4.2 | Long-session soak test (8 hours sustained load) | 0 crashes, <5% memory growth |
| D4.3 | Click-through validation script (all interactive paths) | 100% of button/slot paths |
| D4.4 | Performance regression suite (p95 frame time, lag, memory) | Automated CI gate |
| D4.5 | Thread-safety audit pass (formal review) | Zero data race reports |
| D4.6 | Documentation: architecture, API, theme, plugin, security | Complete and reviewed |

---

# 4. Development Plan — Detailed Phases

## Phase 0: Foundation — Crash-Proof Base

The highest priority is a system that **cannot crash** from thread races, widget lifetime issues, or missing timeouts.

### Week 1: EventBus + TaskStore Thread Safety

```
Day 1-2:  EventBus RLock audit + test with concurrent emitter harness
          Add thread-spawning test that emits 1000 events from 4 threads
Day 3-4:  TaskStore check_same_thread=False + Lock
          Migrate all sqlite3 access to go through locked wrapper
Day 5:    Collapsible pane RuntimeError audit
          Fix all animation callbacks that walk parent chains
```

**Test harness:**
```python
def test_concurrent_eventbus():
    bus = EventBus()
    results = []
    def handler(e): results.append(e)
    bus.subscribe("test", handler)
    def emitter():
        for _ in range(250):
            bus.emit("test", payload={"i": _})
    threads = [threading.Thread(target=emitter) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(results) == 1000  # no dropped events from corruption
```

### Week 2: UI Stability Infrastructure

```
Day 1-2:  Global crash hooks (sys.excepthook, threading.excepthook)
          Crash log writer with rotation
Day 3-4:  Event-loop watchdog
          Adaptive tick (500ms base, throttles up under pressure)
Day 5:    Subprocess _safe_subprocess_run migration for remaining 40 calls
          Audit each call site; add timeout or move to background worker
```

## Phase 1: Cognitive Engine

The cognitive engine is a **bounded probabilistic state manifold** that evolves over time. It does not enumerate all states — it compresses, prunes, and focuses.

### Core Architecture

```
┌─────────────────────────────────────────┐
│           Semantic Manifold             │
│  (latent state vectors + topology)      │
├─────────────────────────────────────────┤
│           Mutation Engine               │
│  (evolutionary search, merge, spawn)    │
├─────────────────────────────────────────┤
│           Salience Engine               │
│  (attention allocation, entropy gating) │
├─────────────────────────────────────────┤
│        Constraint Collapse Engine       │
│  (hard/soft constraints, coherence)     │
├─────────────────────────────────────────┤
│      Recursive Predictive Simulator     │
│  (beam search, MCTS, temporal rollup)   │
├─────────────────────────────────────────┤
│           Persistent World Model        │
│  (checkpoint, drift detection, restore) │
└─────────────────────────────────────────┘
```

### Key Data Structures

```python
@dataclass
class SemanticNode:
    id: str
    vector: np.ndarray          # latent representation
    salience: float
    confidence: float
    entropy: float
    created: float              # monotonic timestamp
    last_mutated: float
    dependencies: set[str]      # node IDs
    predictions: list[Prediction]

@dataclass
class Mutation:
    source_id: str
    target_ids: list[str]
    operation: str              # SPAWN, MERGE, PERTURB, PRUNE
    delta_vector: np.ndarray
    confidence: float

@dataclass
class SalienceMap:
    node_scores: dict[str, float]
    gradient: dict[str, float]  # predicted information gain
    budget_remaining: float
```

### Week 3: Semantic State Manifold

```
Day 1-2:  SemanticNode dataclass + vector store (numpy-backed)
Day 3-4:  Topology construction (nearest-neighbour graph, k=8)
Day 5:    Serialization/deserialization, checkpoint format
```

### Week 4: Mutation Engine

```
Day 1-2:  Mutation dataclass + operation dispatcher
Day 3-4:  SPAWN (create child from parent + random perturbation)
          MERGE (average overlapping nodes)
          PERTURB (random walk in latent space)
          PRUNE (remove low-salience nodes)
Day 5:    Mutation scheduler (continuous background loop)
```

### Week 5: Salience Engine

```
Day 1-2:  Salience scoring functions:
          - Novelty (distance from existing nodes)
          - Predictive divergence (prediction error)
          - Semantic density (local neighbourhood complexity)
          - Risk (entropy × confidence⁻¹)
          - Utility (historical outcome score)
Day 3-4:  Compute budget allocator (top-N by score)
Day 5:    Integration with Mutation Engine (salience-gated mutation)
```

### Week 6: Constraint Collapse + Recursive Prediction

```
Day 1-2:  Hard constraint engine (logical/physical boundaries)
          Soft constraint engine (preference-weighted)
Day 3-4:  Recursive predictive simulator
          Beam search over k=8 branches, depth=3
Day 5:    Persistent world model
          Checkpoint every N mutations
          Drift detection (hash comparison)
          Rollback on critical drift
```

## Phase 2: Cyber-Style UX Shell

The UX is designed for **immersion and operability** — dark, glowing, responsive.

### Visual Design Tokens

```json
{
  "theme_name": "aion-cyber-dark",
  "colors": {
    "background": "#0a0e1a",
    "background_secondary": "#111827",
    "background_tertiary": "#1a2235",
    "surface": "#1e293b",
    "surface_hover": "#263548",
    "border": "#2a3a5c",
    "border_focus": "#00f0ff",
    "text_primary": "#e2e8f0",
    "text_secondary": "#94a3b8",
    "text_accent": "#00f0ff",
    "accent_primary": "#00f0ff",
    "accent_secondary": "#ff00aa",
    "accent_warning": "#ffaa00",
    "accent_error": "#ff3355",
    "accent_success": "#00ff88",
    "glow_accent": "rgba(0, 240, 255, 0.3)",
    "glow_warning": "rgba(255, 170, 0, 0.3)",
    "glow_error": "rgba(255, 51, 85, 0.3)"
  },
  "typography": {
    "font_family_ui": "Inter, SF Pro, sans-serif",
    "font_family_mono": "JetBrains Mono, Fira Code, monospace",
    "font_size_small": 11,
    "font_size_normal": 13,
    "font_size_large": 15,
    "font_size_header": 18,
    "font_size_title": 24
  },
  "spacing": {
    "compact": { "padding": 4, "margin": 2, "gap": 2 },
    "normal": { "padding": 8, "margin": 4, "gap": 4 },
    "comfortable": { "padding": 12, "margin": 8, "gap": 8 }
  },
  "animation": {
    "duration_short_ms": 150,
    "duration_medium_ms": 250,
    "duration_long_ms": 400,
    "easing": "ease_in_out_quad",
    "global_speed_multiplier": 1.0
  }
}
```

### Week 7: Main Window Shell

```
Day 1-2:  Qt6 main window with dark theme and cyber-palette stylesheet
Day 3-4:  Tab system with drag-reorder (QTabBar + QStackedWidget)
Day 5:    Command palette (QDialog + fuzzy matching via rapidfuzz)
```

### Week 8: Cyber Visual Components

```
Day 1-2:  HexGridOverlay — QWidget with configurable hex tiling
          Support density (hex size), opacity, animation (pulse)
Day 3-4:  Glow effects — QGraphicsDropShadowEffect presets
          Scan-line overlay — QWidget with line pattern
Day 5:    Particle system — lightweight cursor trail
```

### Week 9: Theme System + Action Registry

```
Day 1-2:  Theme loader (JSON → QPalette + stylesheet tokens)
          Hot-reload on file change
Day 3-4:  Action registry (name → shortcut → callback)
          Conflict detection (duplicate shortcut warning)
Day 5:    Keybinding editor UI
```

### Week 10: Sound Engine + Workspace Profiles

```
Day 1-2:  Sound engine (QSoundEffect or wrapped player)
          20 UI events (tab switch, button click, error, etc.)
          Sound pack directory: ~/.aion/sounds/<pack>/
Day 3-5:  Workspace profile save/load
          Full panel state: visibility, size, position, tab order
```

## Phase 3: Customisability

### Week 11: Cosmetic Controls

```
Day 1-2:  Font family/size picker per component type
Day 3-4:  Opacity sliders (bg, fg, overlay, particles)
Day 5:    Animation speed global multiplier
```

### Week 12: Layout + Panels

```
Day 1-2:  Layout density presets (Compact/Normal/Comfortable)
Day 3-4:  Detachable panels (QWidget + QMainWindow floating)
Day 5:    Panel re-docking via drag-to-tab-bar
```

### Week 13: Plugin System

```
Day 1-2:  Plugin discovery (directory scan + import hook)
          Manifest format (name, version, hooks, capabilities)
Day 3-4:  Sandboxed execution (restricted Python environment)
          Capability gating (filesystem, network, subprocess, etc.)
Day 5:    Hook registry (events: on_startup, on_tick, on_event, on_shutdown)
```

### Week 14: Automation + Export

```
Day 1-2:  Notification rules engine
          Matchers: event_type, source, severity, regex payload
          Actions: log, dialog, sound, webhook, script
Day 3-4:  Export pipeline
          JSON/CSV/HRF as plain serialization
          HTML/PDF via Jinja2 templates + weasyprint
Day 5:    Automation triggers (timer, file-watch, event-bus, webhook)
```

## Phase 4: Integration & Hardening

### Week 15: Subprocess Timeout Completion

```
Audit all 40+ remaining subprocess.run() calls on UI thread:
  - Add timeout= parameter (30s default, 60s for network ops)
  - Or route through run_in_background()
  - Add regression test: "subprocess hangs returns error within timeout"
```

### Week 16: Long-Session Soak

```
8-hour automated run with:
  - Synthetic workload generator (mutation, event, refresh cycles)
  - Memory sampling every 60s
  - Frame time sampling every 10s
  - Event-loop lag sampling every 1s
  - Crash = FAIL, >5% memory growth/hr = WARN
```

### Week 17: Click-Through Validation

```
Automated script that exercises every button, menu, shortcut:
  - Tab switches: all tabs, all sub-tabs
  - CRUD operations: create, read, update, delete for all entity types
  - Settings: every toggle, slider, combo box
  - Customisation: every theme, font, opacity, animation setting
  - Failure paths: disconnected network, missing git, empty project
```

### Week 18: Documentation + Final Review

```
- Architecture.md: system components, data flow, thread model
- API.md: public interfaces, plugin hooks, event types
- Theme.md: theme file format, token reference
- Plugin.md: plugin authoring guide, sandbox model
- Security.md: credential handling, sandbox, network policy
```

---

# 5. Architectural Principles

### Thread Safety

```
┌────────────────┐     ┌─────────────────┐
│   Main Thread  │     │  Background Thread │
│  (Qt Event Loop) │     │  (Telemetry/Timer) │
├────────────────┤     ├─────────────────┤
│ Widget mutation │     │ Event emission   │
│ via mutation     │     │ via EventBus     │
│ queue (locked)   │     │ (locked)         │
│ TaskStore read/  │     │ TaskStore read   │
│ write (locked)   │     │ (locked)         │
│ Subprocess with  │     │ Filesystem ops   │
│ timeout          │     │ (no Qt access)   │
└────────────────┘     └─────────────────┘
        │                      │
        └──────────┬───────────┘
                   ▼
          ┌────────────────┐
          │   EventBus     │
          │  (RLock guard) │
          └────────────────┘
```

### Stability Hierarchy

1. **Must not crash** — Thread safety, widget lifetime, exception hooks
2. **Must not freeze** — Subprocess timeouts, non-blocking workers, timer inflight guards
3. **Must not corrupt** — EventBus locks, TaskStore locks, mutation queue overflow
4. **Must be diagnosable** — Watchdog, crash logs, performance telemetry
5. **Must be recoverable** — Crash hooks show dialog, startup retry, world model checkpoint

---

# 6. Development Environment

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Runtime |
| PyQt6 | 6.5+ | GUI shell |
| NumPy | 1.24+ | Vector operations |
| SciPy | 1.10+ | KD-tree, distance metrics |
| pytest | 7+ | Test framework |
| pytest-benchmark | 4+ | Performance regression |
| mypy | 1.0+ | Type checking |
| ruff | 0.1+ | Linting |
| pre-commit | 3+ | Hook automation |

---

# 7. CI/CD Pipeline

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Lint    │ → │  Type    │ → │  Test    │ → │  Bench   │
│ (ruff)   │   │ (mypy)   │   │ (pytest) │   │(pytest-  │
│          │   │          │   │          │   │ bench)   │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
                                               │
                                               ▼
                                        ┌──────────┐
                                        │  Build   │
                                        │ (PyInst.)│
                                        └──────────┘
```

### CI Gates

| Gate | Command | Failure |
|------|---------|---------|
| Lint | `ruff check .` | Block PR |
| Type | `mypy --strict src/` | Block PR |
| Test | `pytest tests/ -q` | Block PR |
| Bench | `pytest --benchmark-compare` | Warn on >5% regression |
| Build | `pyinstaller aion.spec` | Block PR |
| Soak | `pytest tests/soak/ --soak-hours=1` | Block merge to main |

---

# 8. Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Semantic manifold combinatorial explosion | High | Critical | Aggressive salience gating, hard node caps, adaptive pruning |
| QT6 thread-safety regression | Medium | Critical | Full thread-safety audit in CI, concurrent emitter test harness |
| EventBus deadlock from RLock misuse | Low | High | Code review, starvation test with mixed-priority emitters |
| Plugin sandbox escape | Low | Critical | Restricted Python environment, capability gating, no filesystem by default |
| Theme system hot-reload race | Low | Medium | Apply theme via mutation queue on main thread |
| Long-session memory leak | Medium | High | Per-hour memory budget, trend alert, optional GC trigger |
| World model drift accumulation | Medium | Medium | Periodic checkpoint + rollback, drift score trending |
| Cross-language semantic equivalence regression | Medium | Medium | Regression test suite per supported language |

---

# 9. Success Measurement

### Week-over-Week Metrics

| Metric | Tracking |
|--------|----------|
| Tests passing | Absolute count, % coverage |
| Crash-free runtime | Hours without crash in soak |
| P95 frame time | Milliseconds, trend-line |
| Event-loop lag (p99) | Milliseconds, trend-line |
| Memory growth rate | % per hour in soak |
| Startup time | Seconds, cold start |
| Subprocess timeout coverage | % of UI-thread calls with timeout |

### Release Gates

| Gate | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|------|---------|---------|---------|---------|---------|
| 0 crashes in 1hr soak | ✓ | ✓ | ✓ | ✓ | ✓ |
| <5% memory growth/hr | ✓ | ✓ | ✓ | ✓ | ✓ |
| All tests passing | ✓ | ✓ | ✓ | ✓ | ✓ |
| <100ms p95 event-loop lag | ✓ | ✓ | ✓ | ✓ | ✓ |
| Startup <5s | ✓ | ✓ | ✓ | ✓ | ✓ |
| Theme system operational | | | ✓ | ✓ | ✓ |
| Plugin API stable | | | | ✓ | ✓ |
| Thread-safety audit clean | | | | | ✓ |

---

*This document defines the AION architecture, success criteria, and development plan. It is a living document — update as implementation reveals new constraints and opportunities.*
