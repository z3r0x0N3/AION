from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from aion.enriched_store import EnrichedStore

mcp = FastMCP("AION Cognitive Engine", description="Query AION's cognitive model of your filesystem")

_store: EnrichedStore | None = None


def init(store: EnrichedStore) -> None:
    global _store
    _store = store


@mcp.resource("aion://stats")
def get_stats() -> str:
    if _store is None:
        return json.dumps({"error": "Store not initialized"})
    return json.dumps(_store.stats(), indent=2, default=str)


@mcp.resource("aion://nodes/top")
def get_top_nodes() -> str:
    if _store is None:
        return json.dumps({"error": "Store not initialized"})
    nodes = _store.query_nodes(limit=50)
    return json.dumps(nodes, indent=2, default=str)


@mcp.resource("aion://telemetry/latest")
def get_latest_telemetry() -> str:
    if _store is None:
        return json.dumps({"error": "Store not initialized"})
    tel = _store.get_telemetry(limit=10)
    return json.dumps(tel, indent=2, default=str)


@mcp.resource("aion://events/recent")
def get_recent_events() -> str:
    if _store is None:
        return json.dumps({"error": "Store not initialized"})
    events = _store.get_events(limit=50)
    return json.dumps(events, indent=2, default=str)


@mcp.tool()
def query_nodes(
    language: str | None = None,
    extension: str | None = None,
    min_salience: float = 0,
    min_recency: float = 0,
    min_size: int = 0,
    max_size: int = 0,
    limit: int = 100,
) -> str:
    if _store is None:
        return json.dumps({"error": "Store not initialized"})
    nodes = _store.query_nodes(
        language=language, extension=extension,
        min_salience=min_salience, min_recency=min_recency,
        min_size=min_size, max_size=max_size, limit=limit,
    )
    return json.dumps(nodes, indent=2, default=str)


@mcp.tool()
def get_node(node_id_or_path: str) -> str:
    if _store is None:
        return json.dumps({"error": "Store not initialized"})
    node = _store.get_node(node_id_or_path)
    if node is None:
        return json.dumps({"error": "Node not found"})
    return json.dumps(node, indent=2, default=str)


@mcp.tool()
def get_telemetry(hours: int = 1) -> str:
    if _store is None:
        return json.dumps({"error": "Store not initialized"})
    tel = _store.get_telemetry(limit=hours * 60)
    return json.dumps(tel, indent=2, default=str)


@mcp.tool()
def get_events(event_type: str | None = None, limit: int = 50) -> str:
    if _store is None:
        return json.dumps({"error": "Store not initialized"})
    events = _store.get_events(event_type=event_type, limit=limit)
    return json.dumps(events, indent=2, default=str)


@mcp.tool()
def stats() -> str:
    if _store is None:
        return json.dumps({"error": "Store not initialized"})
    return json.dumps(_store.stats(), indent=2, default=str)


def run_server(host: str = "127.0.0.1", port: int = 8124) -> None:
    mcp.run(host=host, port=port)


if __name__ == "__main__":
    db = Path.home() / ".aion" / "enriched.db"
    init(EnrichedStore(db))
    print(f"AION MCP server starting on 127.0.0.1:8124 (db: {db})")
    run_server()
