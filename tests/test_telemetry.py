import tempfile
from pathlib import Path

from aion.telemetry import PerformanceTelemetry


class TestTelemetry:
    def test_sample_and_summary(self):
        tel = PerformanceTelemetry()
        tel.sample(frame_time_ms=16.7, event_loop_lag_ms=2.0, memory_mb=100.0)
        tel.sample(frame_time_ms=33.3, event_loop_lag_ms=5.0, memory_mb=101.0)
        tel.sample(frame_time_ms=8.3, event_loop_lag_ms=1.0, memory_mb=102.0)
        summary = tel.summary()
        assert summary["sample_count"] == 3
        assert summary["frame_time_p50"] > 0
        assert summary["frame_time_p95"] > 0
        assert summary["memory_growth_mb"] == 2.0

    def test_save_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tel = PerformanceTelemetry(log_dir=tmpdir)
            tel.sample(frame_time_ms=16.0, memory_mb=50.0)
            path = tel.save("test_run")
            assert Path(path).exists()
            content = Path(path).read_text()
            assert "frame_time_p50" in content

    def test_clear_resets(self):
        tel = PerformanceTelemetry()
        tel.sample(frame_time_ms=10.0)
        assert tel.summary()["sample_count"] == 1
        tel.clear()
        assert tel.summary() == {}

    def test_empty_summary(self):
        tel = PerformanceTelemetry()
        assert tel.summary() == {}
