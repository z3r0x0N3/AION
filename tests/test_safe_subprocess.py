import subprocess

import pytest

from aion.safe_subprocess import (
    safe_subprocess_run,
    run_in_background,
    SubprocessTimeoutError,
    audit_subprocess_calls,
)


class TestSafeSubprocess:
    def test_successful_run(self):
        result = safe_subprocess_run(["echo", "hello"], timeout=5)
        assert result.returncode == 0
        assert "hello" in result.stdout

    def test_timeout_raises(self):
        with pytest.raises(SubprocessTimeoutError):
            safe_subprocess_run(["sleep", "10"], timeout=0.1)

    def test_run_in_background(self):
        results = []

        def callback(result, error):
            results.append((result, error))

        thread = run_in_background(
            ["echo", "bg"], callback=callback, timeout=5
        )
        thread.join(timeout=3)
        assert len(results) == 1
        assert results[0][0] is not None
        assert results[0][1] is None

    def test_run_in_background_error(self):
        results = []

        def callback(result, error):
            results.append((result, error))

        thread = run_in_background(
            ["sleep", "10"], callback=callback, timeout=0.1
        )
        thread.join(timeout=2)
        assert len(results) == 1
        assert results[0][1] is not None

    def test_audit_subprocess_calls(self):
        import aion.safe_subprocess as mod
        calls = audit_subprocess_calls(mod)
        assert isinstance(calls, list)
