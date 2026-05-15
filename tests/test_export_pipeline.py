import tempfile
from pathlib import Path

import pytest

from aion.semantic_manifold import SemanticManifold
from aion.export_pipeline import ExportPipeline, ExportOptions


@pytest.fixture
def manifold():
    m = SemanticManifold(vector_dim=4, max_nodes=50)
    for _ in range(5):
        m.create_node()
    return m


class TestExportPipeline:
    def test_json_export(self, manifold):
        pipe = ExportPipeline()
        result = pipe.export(manifold, ExportOptions(format="json"))
        import json
        data = json.loads(result)
        assert data["node_count"] == 5
        assert len(data["nodes"]) == 5

    def test_csv_export(self, manifold):
        pipe = ExportPipeline()
        result = pipe.export(manifold, ExportOptions(format="csv"))
        assert "id" in result
        assert "salience" in result
        lines = result.strip().split("\n")
        assert len(lines) == 6  # header + 5 nodes

    def test_hrf_export(self, manifold):
        pipe = ExportPipeline()
        result = pipe.export(manifold, ExportOptions(format="hrf"))
        assert result.startswith("#")
        assert "Nodes: 5" in result

    def test_html_export(self, manifold):
        pipe = ExportPipeline()
        result = pipe.export(manifold, ExportOptions(format="html"))
        assert "<html" in result or "<!DOCTYPE html" in result

    def test_export_to_file(self, manifold):
        pipe = ExportPipeline()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "export.json"
            result = pipe.export_to_file(manifold, path)
            assert result.exists()
            data = result.read_text()
            assert "node_count" in data

    def test_invalid_format(self, manifold):
        pipe = ExportPipeline()
        import pytest
        with pytest.raises(ValueError, match="Unsupported format"):
            pipe.export(manifold, ExportOptions(format="xyz"))

    def test_without_vectors(self, manifold):
        pipe = ExportPipeline()
        result = pipe.export(manifold, ExportOptions(format="json", include_vectors=False))
        import json
        data = json.loads(result)
        assert "vector" not in data["nodes"][0]
