from __future__ import annotations

import subprocess
import sys
import threading
import time
from typing import Any


class SubprocessTimeoutError(subprocess.TimeoutExpired):
    pass


def safe_subprocess_run(
    args: list[str],
    timeout: float = 30.0,
    shell: bool = False,
    capture_output: bool = True,
    **kwargs: Any,
) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(
            args,
            timeout=timeout,
            shell=shell,
            capture_output=capture_output,
            text=True,
            **kwargs,
        )
        return result
    except subprocess.TimeoutExpired as e:
        raise SubprocessTimeoutError(
            cmd=e.cmd,
            timeout=e.timeout,
            output=e.output,
            stderr=e.stderr,
        ) from e


def run_in_background(
    args: list[str],
    callback: callable | None = None,
    timeout: float = 60.0,
    **kwargs: Any,
) -> threading.Thread:
    results: dict[str, Any] = {"result": None, "error": None}

    def _run() -> None:
        try:
            results["result"] = safe_subprocess_run(args, timeout=timeout, **kwargs)
        except Exception as e:
            results["error"] = e
        if callback:
            try:
                callback(results["result"], results["error"])
            except Exception:
                pass

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t


def audit_subprocess_calls(module: object) -> list[dict[str, Any]]:
    import ast
    import inspect

    calls: list[dict[str, Any]] = []
    try:
        source = inspect.getsource(module)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "run":
                    call_info = {
                        "line": node.lineno,
                        "has_timeout": any(
                            kw.arg == "timeout" for kw in node.keywords if kw.arg is not None
                        ),
                    }
                    calls.append(call_info)
    except (OSError, TypeError):
        pass
    return calls
