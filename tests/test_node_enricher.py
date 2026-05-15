import tempfile
from pathlib import Path

import pytest

from aion.node_enricher import enrich_file, _detect_language, _count_comments, _extract_imports


class TestNodeEnricher:
    def test_enrich_python_file(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("# comment\nimport os\nimport sys\n\nx = 1\ny = 2\n")
            path = f.name
        try:
            data = enrich_file(path)
            assert data["language"] == "Python"
            assert data["extension"] == ".py"
            assert data["line_count"] >= 6
            assert data["comment_lines"] >= 1
            assert len(data["imports"]) >= 2
        finally:
            Path(path).unlink()

    def test_enrich_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data = enrich_file(tmpdir)
            assert data["is_dir"] is True

    def test_detect_language(self):
        assert _detect_language(Path("main.py")) == "Python"
        assert _detect_language(Path("main.rs")) == "Rust"
        assert _detect_language(Path("main.js")) == "JavaScript"
        assert _detect_language(Path("unknown.xyz")) == "Unknown"

    def test_count_comments_python(self):
        lines = ["# header", "x = 1", "# footer", "", "y = 2"]
        assert _count_comments(lines, ".py") == 2

    def test_count_comments_cpp(self):
        lines = ["// header", "int x = 1;", "/* block */", "y = 2"]
        assert _count_comments(lines, ".cpp") >= 2

    def test_extract_imports_python(self):
        lines = ["import os", "from pathlib import Path", "x = 1"]
        imps = _extract_imports(lines, ".py")
        assert "import os" in imps
        assert "from pathlib import Path" in imps

    def test_extract_imports_rust(self):
        lines = ["use std::fs;", "use std::path::Path;", "fn main() {}"]
        imps = _extract_imports(lines, ".rs")
        assert len(imps) >= 2

    def test_checksums(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"hello world")
            path = f.name
        try:
            data = enrich_file(path)
            assert len(data["checksum_md5"]) == 32
            assert len(data["checksum_sip32"]) > 0
        finally:
            Path(path).unlink()

    def test_symlink(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target.txt"
            target.write_text("real")
            link = Path(tmpdir) / "link.txt"
            link.symlink_to(target)
            data = enrich_file(link)
            assert data["symlink_target"] == str(target)
