# AION Architecture

## Overview

AION is a bounded cognitive runtime that models an effectively infinite probabilistic state space by dynamically compressing uncertainty into coherent, actionable structure. It is a salience-directed semantic optimization engine that recursively allocates compute where informational gain is highest.

## System Components

```
┌─────────────────────────────────────────────┐
│              EventBus                        │
│  (thread-safe priority queue + pub/sub)      │
├─────────────────────────────────────────────┤
│              StateStore                      │
│  (SQLite-backed key-value with TTL/version)  │
├─────────────────────────────────────────────┤
│           Semantic Manifold                  │
│  (latent state vectors + KD-tree topology)   │
├─────────────────────────────────────────────┤
│           Mutation Engine                    │
│  (SPAWN/MERGE/PERTURB/PRUNE operations)      │
├─────────────────────────────────────────────┤
│           Salience Engine                    │
│  (5-factor scoring + compute allocation)     │
├─────────────────────────────────────────────┤
│        Constraint Collapse Engine            │
│  (hard/soft constraint application)          │
├─────────────────────────────────────────────┤
│      Recursive Predictive Simulator          │
│  (MCTS beam search k=8, depth=3)            │
├─────────────────────────────────────────────┤
│           World Model                        │
│  (checkpoint, drift detection, rollback)     │
├─────────────────────────────────────────────┤
│        Cyber-Style UI Shell (PyQt6)          │
│  (main window, tabs, command palette,        │
│   hex grid, scan-lines, particles)           │
├─────────────────────────────────────────────┤
│        Customisation Layer                   │
│  (theme, density, fonts, panels, plugins)    │
└─────────────────────────────────────────────┘
```

## Thread Model

- **Main thread**: Qt event loop, widget mutation via mutation queue
- **Background threads**: Mutation engine, timer triggers, file watch, webhook listener
- **Synchronisation**: RLock on all shared state (EventBus, StateStore, Manifold, etc.)
- **UI mutation queue**: Bounded deque, drained on main thread tick

## Data Flow

1. Events enter via EventBus (pub/sub with priority queue)
2. Semantic manifold evolves via mutation engine (SPAWN/MERGE/PERTURB/PRUNE)
3. Salience engine scores nodes (novelty, divergence, density, risk, utility)
4. Constraint collapse engine applies hard/soft constraints
5. Predictive simulator runs beam search over future state trajectories
6. World model checkpoints periodically and detects drift
7. UI shell renders state through cyber-style components
