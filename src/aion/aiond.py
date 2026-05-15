#!/usr/bin/env python3
"""AION Daemon — headless cognitive engine with MCP server.

Starts the cognitive engine, filesystem watcher, and MCP server.
Runs as a background daemon. The GUI connects to it via MCP for control.
"""

import argparse
import os
import signal
import sys
import time
from pathlib import Path

BASE_DIR = Path.home() / ".aion"
DB_PATH = BASE_DIR / "enriched.db"
PID_PATH = BASE_DIR / "aiond.pid"
LOG_PATH = BASE_DIR / "aiond.log"


def log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")
    print(line, file=sys.stderr)


def run_daemon(args: argparse.Namespace) -> None:
    from aion.semantic_manifold import SemanticManifold
    from aion.mutation_engine import MutationEngine
    from aion.salience_engine import SalienceEngine
    from aion.constraint_engine import ConstraintCollapseEngine
    from aion.world_model import WorldModel
    from aion.enriched_store import EnrichedStore
    from aion.node_enricher import enrich_file
    from aion.filesystem_cognition import FilesystemCognitiveEngine, FilesystemWatcher
    import aion.mcp_server as mcp_server

    manifold = SemanticManifold(vector_dim=64, max_nodes=args.max_nodes)
    for _ in range(50):
        manifold.create_node()
    manifold.rebuild_tree_if_needed()

    mutation_engine = MutationEngine(manifold, mutation_interval=0.01)
    salience_engine = SalienceEngine(manifold)
    constraint_engine = ConstraintCollapseEngine(manifold)
    constraint_engine.add_hard_constraint("normalize")
    world_model = WorldModel(manifold, checkpoint_interval=500)

    store = EnrichedStore(DB_PATH)
    mcp_server.init(store)
    store.log_event("daemon.start", "aiond", "Daemon started")

    fs_engine: FilesystemCognitiveEngine | None = None
    fs_watcher: FilesystemWatcher | None = None

    if args.root:
        fs_db = Path(args.root) / ".aion_fs" / "file_meta.db"
        fs_engine = FilesystemCognitiveEngine(args.root, manifold=None, db_path=fs_db)
        fs_watcher = FilesystemWatcher(fs_engine)
        count = fs_watcher.index_and_watch(max_files=args.max_nodes * 10)
        store.log_event("fs.start", str(args.root), f"Indexed {count} files")
        log(f"FS watch started on {args.root} — {count} files")

    log(f"AION daemon started (pid={os.getpid()}, max_nodes={args.max_nodes})")

    tick = 0
    try:
        while True:
            tick += 1
            mutation_engine.max_mutations_per_tick = args.max_nodes
            mutation_engine.tick()
            manifold.rebuild_tree_if_needed()

            if tick % 2 == 0:
                salience_engine.compute_salience_map()

            if tick % 5 == 0:
                for node in manifold.get_random_nodes(min(2, manifold.size)):
                    constraint_engine.collapse(node.id)

            if tick % 20 == 0:
                world_model.detect_drift()
                world_model.checkpoint()

            if fs_engine and tick % 3 == 0:
                fs_engine.manifold.rebuild_tree_if_needed()

            if tick % 10 == 0:
                nodes = manifold.size
                mutations = mutation_engine.mutation_count
                avg_sal = sum(n.salience for n in manifold.nodes.values()) / max(1, nodes)
                avg_conf = sum(n.confidence for n in manifold.nodes.values()) / max(1, nodes)
                avg_ent = sum(n.entropy for n in manifold.nodes.values()) / max(1, nodes)
                drift = world_model.drift_score
                fs_count = fs_engine.path_count() if fs_engine else 0

                store.upsert_telemetry({
                    "node_count": nodes, "mutation_count": mutations,
                    "avg_salience": avg_sal, "avg_confidence": avg_conf,
                    "avg_entropy": avg_ent, "drift_score": drift,
                    "fs_file_count": fs_count,
                    "memory_mb": 0, "cpu_percent": 0,
                })

                if fs_engine and tick % 30 == 0:
                    for meta in fs_engine.top_recent(5):
                        node = fs_engine.node_for_path(meta.path)
                        if node and node.id:
                            enriched = enrich_file(meta.path)
                            enriched.update({
                                "salience": node.salience,
                                "confidence": node.confidence,
                                "entropy": node.entropy,
                                "recency_score": meta.recency_score,
                                "size_weight": meta.size_weight,
                                "last_indexed": meta.last_indexed,
                            })
                            store.upsert_node(node.id, enriched)

            time.sleep(0.5)

    except KeyboardInterrupt:
        log("Daemon shutting down")
        store.log_event("daemon.stop", "aiond", "Daemon stopped by interrupt")
        if fs_watcher:
            fs_watcher.stop()
        store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="AION Daemon")
    parser.add_argument("--root", type=str, default=None, help="Root path for filesystem watch")
    parser.add_argument("--max-nodes", type=int, default=100, help="Max nodes per cycle")
    parser.add_argument("--daemon", action="store_true", help="Daemonize (fork to background)")
    parser.add_argument("--mcp-only", action="store_true", help="Run MCP server only, no engine")
    parser.add_argument("--mcp-port", type=int, default=8124, help="MCP server port")
    parser.add_argument("--mcp-host", type=str, default="127.0.0.1", help="MCP server host")
    args = parser.parse_args()

    if args.mcp_only:
        from aion.enriched_store import EnrichedStore
        import aion.mcp_server as mcp_server
        store = EnrichedStore(DB_PATH)
        mcp_server.init(store)
        log(f"MCP-only server on {args.mcp_host}:{args.mcp_port}")
        mcp_server.run_server(host=args.mcp_host, port=args.mcp_port)
        return

    if args.daemon:
        pid = os.fork()
        if pid > 0:
            print(f"AION daemon started (pid={pid})")
            sys.exit(0)
        os.setsid()

    run_daemon(args)


if __name__ == "__main__":
    main()
