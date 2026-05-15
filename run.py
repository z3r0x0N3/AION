#!/usr/bin/env python3
"""AION — Cognitive Runtime

Usage:
  python run.py              # Launch GUI (embedded engine)
  python run.py --headless   # Run headless daemon
  python run.py --client     # Launch GUI connected to running daemon
  python run.py --mcp-only   # Start only the MCP server
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="AION Cognitive Runtime")
    parser.add_argument("--headless", action="store_true", help="Run headless daemon, no GUI")
    parser.add_argument("--client", action="store_true", help="Launch GUI connected to running daemon")
    parser.add_argument("--mcp-only", action="store_true", help="Start only the MCP server")
    parser.add_argument("--root", type=str, default=None, help="Root path for filesystem watch")
    parser.add_argument("--max-nodes", type=int, default=100, help="Max nodes per cycle")
    parser.add_argument("--mcp-port", type=int, default=8124, help="MCP server port")
    args = parser.parse_args()

    if args.headless:
        cmd = [
            sys.executable, str(Path(__file__).parent / "src" / "aion" / "aiond.py"),
            "--daemon",
            f"--max-nodes={args.max_nodes}",
        ]
        if args.root:
            cmd.append(f"--root={args.root}")
        subprocess.run(cmd)
        return

    if args.mcp_only:
        cmd = [
            sys.executable, str(Path(__file__).parent / "src" / "aion" / "aiond.py"),
            "--mcp-only",
            f"--mcp-port={args.mcp_port}",
        ]
        subprocess.run(cmd)
        return

    if args.client:
        from aion.main_window import AionMainWindow
        from PyQt6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("AION")
        window = AionMainWindow()
        window.set_status(f"Connected to AION daemon on port {args.mcp_port}", timeout=5000)
        window.show()
        sys.exit(app.exec())
        return

    from aion.crash_hooks import install_crash_hooks
    from aion.main_window import AionMainWindow
    from PyQt6.QtWidgets import QApplication

    install_crash_hooks()
    app = QApplication(sys.argv)
    app.setApplicationName("AION")
    window = AionMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
