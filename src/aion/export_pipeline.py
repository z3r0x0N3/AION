from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aion.semantic_manifold import SemanticManifold


@dataclass
class ExportOptions:
    format: str = "json"
    indent: int = 2
    include_vectors: bool = True
    include_predictions: bool = True
    template_path: str | None = None


class ExportPipeline:
    def __init__(self) -> None:
        self._jinja_available = False
        try:
            import jinja2
            self._jinja_available = True
            self._jinja = jinja2
        except ImportError:
            pass

    def export(self, manifold: SemanticManifold, options: ExportOptions) -> str:
        if options.format == "json":
            return self._to_json(manifold, options)
        elif options.format == "csv":
            return self._to_csv(manifold, options)
        elif options.format == "hrf":
            return self._to_hrf(manifold)
        elif options.format == "html":
            return self._to_html(manifold, options)
        elif options.format == "pdf":
            return self._to_pdf(manifold, options)
        else:
            raise ValueError(f"Unsupported format: {options.format}")

    def export_to_file(self, manifold: SemanticManifold, path: str | Path, options: ExportOptions | None = None) -> Path:
        path = Path(path)
        if options is None:
            ext = path.suffix.lstrip(".") or "json"
            options = ExportOptions(format=ext)
        content = self.export(manifold, options)
        path.write_text(content)
        return path

    def _to_json(self, manifold: SemanticManifold, options: ExportOptions) -> str:
        data = self._build_data(manifold, options)
        return json.dumps(data, indent=options.indent, default=str)

    def _to_csv(self, manifold: SemanticManifold, options: ExportOptions) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "salience", "confidence", "entropy", "created", "last_mutated"])
        for node in manifold.nodes.values():
            writer.writerow([
                node.id, node.salience, node.confidence, node.entropy,
                node.created, node.last_mutated,
            ])
        return output.getvalue()

    def _to_hrf(self, manifold: SemanticManifold) -> str:
        lines = ["# AION State Dump (HRF)", f"# Nodes: {manifold.size}", f"# Vector dim: {manifold.vector_dim}", ""]
        for node in manifold.nodes.values():
            lines.append(f"--- {node.id} ---")
            lines.append(f"  salience:     {node.salience:.4f}")
            lines.append(f"  confidence:   {node.confidence:.4f}")
            lines.append(f"  entropy:      {node.entropy:.4f}")
            lines.append(f"  dependencies: {len(node.dependencies)}")
            lines.append(f"  predictions:  {len(node.predictions)}")
        return "\n".join(lines)

    def _to_html(self, manifold: SemanticManifold, options: ExportOptions) -> str:
        if not self._jinja_available:
            return self._fallback_html(manifold)
        try:
            template_str = options.template_path or self._default_html_template()
            if options.template_path:
                from jinja2 import Environment, FileSystemLoader
                template_dir = Path(options.template_path).parent
                env = Environment(loader=FileSystemLoader(str(template_dir)))
                template = env.get_template(Path(options.template_path).name)
            else:
                from jinja2 import Environment, BaseLoader
                env = Environment(loader=BaseLoader())
                template = env.from_string(template_str)
            data = self._build_data(manifold, options)
            return template.render(data=data)
        except Exception:
            return self._fallback_html(manifold)

    def _to_pdf(self, manifold: SemanticManifold, options: ExportOptions) -> str:
        html = self._to_html(manifold, options)
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html).write_pdf()
            return pdf_bytes.decode("latin-1")
        except ImportError:
            return html

    def _build_data(self, manifold: SemanticManifold, options: ExportOptions) -> dict:
        nodes_list = []
        for node in manifold.nodes.values():
            entry: dict[str, Any] = {
                "id": node.id,
                "salience": node.salience,
                "confidence": node.confidence,
                "entropy": node.entropy,
                "created": node.created,
                "last_mutated": node.last_mutated,
                "dependencies": list(node.dependencies),
            }
            if options.include_vectors:
                entry["vector"] = node.vector.tolist()
            if options.include_predictions:
                entry["predictions"] = [
                    {"target_id": p.target_id, "probability": p.probability}
                    for p in node.predictions
                ]
            nodes_list.append(entry)
        return {
            "node_count": manifold.size,
            "vector_dim": manifold.vector_dim,
            "nodes": nodes_list,
        }

    def _fallback_html(self, manifold: SemanticManifold) -> str:
        rows = "".join(
            f"<tr><td>{n.id[:8]}</td><td>{n.salience:.3f}</td>"
            f"<td>{n.confidence:.3f}</td><td>{n.entropy:.3f}</td></tr>"
            for n in manifold.nodes.values()
        )
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>AION Export</title>
<style>body {{ font-family: monospace; background: #0a0e1a; color: #e2e8f0; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #2a3a5c; padding: 4px 8px; text-align: left; }}
th {{ background: #1a2235; }}</style></head>
<body><h1>AION State Export</h1>
<p>Nodes: {manifold.size} | Vector dim: {manifold.vector_dim}</p>
<table><tr><th>ID</th><th>Salience</th><th>Confidence</th><th>Entropy</th></tr>{rows}</table></body></html>"""

    def _default_html_template(self) -> str:
        return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>AION Export</title>
<style>
body { font-family: monospace; background: #0a0e1a; color: #e2e8f0; margin: 20px; }
h1 { color: #00f0ff; }
table { border-collapse: collapse; width: 100%; margin-top: 12px; }
th, td { border: 1px solid #2a3a5c; padding: 4px 8px; text-align: left; }
th { background: #1a2235; color: #00f0ff; }
tr:nth-child(even) { background: #111827; }
</style></head>
<body>
<h1>AION State Export</h1>
<p>Nodes: {{ data.node_count }} | Vector dim: {{ data.vector_dim }}</p>
<table>
<tr><th>ID</th><th>Salience</th><th>Confidence</th><th>Entropy</th></tr>
{% for node in data.nodes %}
<tr><td>{{ node.id[:8] }}</td><td>{{ "%.3f"|format(node.salience) }}</td>
<td>{{ "%.3f"|format(node.confidence) }}</td><td>{{ "%.3f"|format(node.entropy) }}</td></tr>
{% endfor %}
</table>
</body></html>"""
