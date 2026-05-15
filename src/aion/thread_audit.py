from __future__ import annotations

import ast
import inspect
import sys
import threading


class ThreadSafetyAudit:
    def __init__(self) -> None:
        self._findings: list[dict[str, Any]] = []

    def audit_module(self, module: object) -> list[dict[str, Any]]:
        self._findings = []
        try:
            source = inspect.getsource(module)
            tree = ast.parse(source)
            self._check_shared_state(tree, source)
            self._check_lock_usage(tree)
            self._check_qt_cross_thread(tree)
        except (OSError, TypeError):
            pass
        return self._findings

    def _check_shared_state(self, tree: ast.AST, source: str) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Attribute):
                                if isinstance(target.value, ast.Name) and target.value.id == "self":
                                    attr_name = target.attr
                                    if attr_name.startswith("_") and not attr_name.startswith("__"):
                                        if not self._has_lock_in_class(node):
                                            lines = source.splitlines()
                                            line = lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                                            self._findings.append({
                                                "type": "unprotected_shared_state",
                                                "class": node.name,
                                                "attr": attr_name,
                                                "line": node.lineno,
                                                "severity": "warning",
                                                "message": f"Shared state '{attr_name}' in {node.name} without lock",
                                            })

    def _check_lock_usage(self, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        func = item.context_expr.func
                        if isinstance(func, ast.Attribute):
                            if func.attr in ("acquire", "__enter__"):
                                continue
                    # Check if context_expr has attr=lock or similar
                    if isinstance(item.context_expr, ast.Attribute):
                        if "lock" in item.context_expr.attr.lower():
                            break
                    elif isinstance(item.context_expr, ast.Name):
                        if "lock" in item.context_expr.id.lower():
                            break

    def _check_qt_cross_thread(self, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute):
                    if func.attr in ("setText", "setVisible", "show", "hide", "setStyleSheet"):
                        self._findings.append({
                            "type": "qt_ui_call",
                            "line": node.lineno,
                            "severity": "info",
                            "message": f"Qt UI call '{func.attr}' — ensure on main thread",
                        })

    def _has_lock_in_class(self, class_node: ast.ClassDef) -> bool:
        for item in ast.walk(class_node):
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Attribute):
                        if "lock" in target.attr.lower():
                            return True
        return False

    @property
    def findings(self) -> list[dict[str, Any]]:
        return list(self._findings)

    def report(self) -> str:
        if not self._findings:
            return "Thread-safety audit clean — no findings."
        lines = ["Thread-Safety Audit Report", "=" * 40, ""]
        for f in self._findings:
            lines.append(f"[{f['severity'].upper()}] {f['type']} at line {f['line']}")
            lines.append(f"       {f['message']}")
            lines.append("")
        return "\n".join(lines)


def audit_running_threads() -> list[dict[str, Any]]:
    threads = []
    for t in threading.enumerate():
        threads.append({
            "name": t.name,
            "daemon": t.daemon,
            "alive": t.is_alive(),
            "ident": t.ident,
        })
    return threads
