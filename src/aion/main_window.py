from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from aion.action_registry import ActionRegistry
from aion.command_palette import CommandPalette
from aion.theme import Theme, apply_theme, default_theme
from aion.cyber_visuals import HexGridOverlay
from aion.sound_engine import SoundEngine
from aion.tab_system import CyberTabWidget
from aion.workspace_profile import WorkspaceProfileManager


class AionMainWindow(QMainWindow):
    def __init__(
        self,
        theme: Theme | None = None,
        action_registry: ActionRegistry | None = None,
        sound_engine: SoundEngine | None = None,
    ) -> None:
        super().__init__()
        self._theme = theme or default_theme()
        self._action_registry = action_registry or ActionRegistry()
        self._sound_engine = sound_engine or SoundEngine()
        self._profile_manager = WorkspaceProfileManager()

        self._command_palette: CommandPalette | None = None
        self._tab_widget: CyberTabWidget | None = None
        self._tick_count = 0

        from aion.semantic_manifold import SemanticManifold
        from aion.mutation_engine import MutationEngine
        from aion.salience_engine import SalienceEngine
        from aion.constraint_engine import ConstraintCollapseEngine
        from aion.world_model import WorldModel
        from aion.telemetry import PerformanceTelemetry

        self._manifold = SemanticManifold(vector_dim=64, max_nodes=10_000)
        for _ in range(50):
            self._manifold.create_node()
        self._manifold.rebuild_tree_if_needed()

        self._mutation_engine = MutationEngine(self._manifold, mutation_interval=0.01)
        self._salience_engine = SalienceEngine(self._manifold)
        self._constraint_engine = ConstraintCollapseEngine(self._manifold)
        self._constraint_engine.add_hard_constraint("normalize")
        self._world_model = WorldModel(self._manifold, checkpoint_interval=500)
        self._telemetry = PerformanceTelemetry()
        self._fs_engine = None
        self._fs_watcher = None
        self._max_nodes_cycle = 100

        self._build_ui()
        self._build_default_panels()
        self._register_default_actions()
        self._apply_theme()
        self._setup_watchdog()

    def _build_ui(self) -> None:
        self.setWindowTitle("AION")
        self.setMinimumSize(1024, 720)
        self.resize(1400, 900)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._hex_overlay = HexGridOverlay(self)
        self._hex_overlay.lower()
        self._hex_overlay.setVisible(False)

        self._tab_widget = CyberTabWidget()
        layout.addWidget(self._tab_widget)

        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet("padding: 2px 8px;")
        self.setStatusBar(self._status_bar)

    def _register_default_actions(self) -> None:
        reg = self._action_registry
        reg.register(
            "command_palette",
            "Ctrl+P",
            self._show_command_palette,
            description="Open command palette",
            category="navigation",
        )
        reg.register(
            "toggle_hex_grid",
            "Ctrl+H",
            self._toggle_hex_grid,
            description="Toggle hex grid overlay",
            category="view",
        )

    def _apply_theme(self) -> None:
        apply_theme(self._theme)
        self._update_stylesheet()

    def _update_stylesheet(self) -> None:
        self.setStyleSheet(self._theme.to_stylesheet())

    def _show_command_palette(self) -> None:
        if self._command_palette is None:
            self._command_palette = CommandPalette(self._action_registry, self)
        self._command_palette.show()

    def _toggle_hex_grid(self) -> None:
        visible = not self._hex_overlay.isVisible()
        self._hex_overlay.setVisible(visible)

    def _on_max_nodes_changed(self, value: int) -> None:
        self._max_nodes_cycle = value
        self._mutation_engine.max_mutations_per_tick = value
        if hasattr(self, "_console"):
            self._console.appendPlainText(f"[config] max nodes per cycle set to {value}")

    def _browse_root(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Root Directory")
        if path:
            self._root_path_input.setText(path)

    def _start_fs_watch(self) -> None:
        root_text = self._root_path_input.text().strip()
        if not root_text:
            self.set_status("Enter a root path first", timeout=3000)
            return
        root_path = Path(root_text).expanduser().resolve()
        if not root_path.is_dir():
            self.set_status(f"Not a valid directory: {root_path}", timeout=3000)
            return
        try:
            from aion.filesystem_cognition import FilesystemCognitiveEngine, FilesystemWatcher
            db_path = root_path / ".aion_fs" / "file_meta.db"
            self._fs_engine = FilesystemCognitiveEngine(root_path, db_path=db_path)
            self._fs_watcher = FilesystemWatcher(self._fs_engine)
            count = self._fs_watcher.index_and_watch(max_files=self._max_nodes_cycle * 10)
            self.set_status(f"FS watch started on {root_path} — {count} files indexed", timeout=5000)
            if hasattr(self, "_console"):
                self._console.appendPlainText(
                    f"[fs] watching {root_path} — {count} files indexed, {self._fs_engine.path_count()} in manifold"
                )
        except Exception as e:
            self.set_status(f"FS watch failed: {e}", timeout=5000)
            if hasattr(self, "_console"):
                self._console.appendPlainText(f"[fs] error: {e}")

    def _build_default_panels(self) -> None:
        console = QPlainTextEdit()
        console.setReadOnly(True)
        console.setPlaceholderText("AION cognitive engine output...")
        mono = QFont("JetBrains Mono", 11)
        mono.setStyleHint(QFont.StyleHint.Monospace)
        console.setFont(mono)
        console.appendPlainText("AION v0.1.0 — Cognitive Runtime Online")
        console.appendPlainText("───" * 20)
        self._console = console
        self.add_panel("Console", console)

        stats = QWidget()
        stats_layout = QVBoxLayout(stats)
        stats_layout.setSpacing(8)
        self._status_labels = {}
        for key in ["State Nodes", "Mutations", "Salience", "Confidence", "Entropy", "Drift"]:
            row = QHBoxLayout()
            label_key = QLabel(f"{key}:")
            label_key.setStyleSheet("color: #00f0ff; font-weight: bold;")
            label_val = QLabel("0")
            label_val.setStyleSheet("color: #e2e8f0;")
            row.addWidget(label_key)
            row.addWidget(label_val)
            row.addStretch()
            stats_layout.addLayout(row)
            self._status_labels[key] = label_val
        stats_layout.addStretch()
        self.add_panel("Status", stats)

        controls = QWidget()
        ctrl_layout = QVBoxLayout(controls)
        ctrl_layout.setSpacing(6)

        max_label = QLabel("Max Nodes / Cycle:")
        max_label.setStyleSheet("color: #00f0ff; font-weight: bold;")
        ctrl_layout.addWidget(max_label)
        self._max_nodes_spin = QSpinBox()
        self._max_nodes_spin.setRange(10, 10000)
        self._max_nodes_spin.setValue(100)
        self._max_nodes_spin.valueChanged.connect(self._on_max_nodes_changed)
        self._max_nodes_spin.setStyleSheet(
            "background: #111827; color: #e2e8f0; border: 1px solid #2a3a5c; padding: 4px;"
        )
        ctrl_layout.addWidget(self._max_nodes_spin)

        root_label = QLabel("Root Path:")
        root_label.setStyleSheet("color: #00f0ff; font-weight: bold;")
        ctrl_layout.addWidget(root_label)
        path_row = QHBoxLayout()
        self._root_path_input = QLineEdit()
        self._root_path_input.setPlaceholderText("~/projects or /path/to/watch")
        self._root_path_input.setStyleSheet(
            "background: #111827; color: #e2e8f0; border: 1px solid #2a3a5c; padding: 4px;"
        )
        path_row.addWidget(self._root_path_input)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_root)
        path_row.addWidget(browse_btn)
        ctrl_layout.addLayout(path_row)

        start_fs_btn = QPushButton("Start FS Watch")
        start_fs_btn.clicked.connect(self._start_fs_watch)
        ctrl_layout.addWidget(start_fs_btn)

        ctrl_layout.addWidget(QLabel("───"))
        buttons = [
            ("Toggle Hex Grid", self._toggle_hex_grid),
            ("Command Palette (Ctrl+P)", self._show_command_palette),
            ("Save Profile", lambda: self.save_profile("default")),
            ("Load Profile", lambda: self.load_profile("default")),
        ]
        for text, cb in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(cb)
            ctrl_layout.addWidget(btn)
        ctrl_layout.addStretch()
        self.add_panel("Controls", controls)

        telemetry = QWidget()
        tel_layout = QVBoxLayout(telemetry)
        tel_layout.setSpacing(8)
        self._progress_bars = {}
        for key in ["CPU", "Memory", "Frame Time"]:
            row = QHBoxLayout()
            lbl = QLabel(f"{key}:")
            lbl.setStyleSheet("color: #94a3b8;")
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setMaximumWidth(200)
            bar.setStyleSheet("""
                QProgressBar { background: #1a2235; border: 1px solid #2a3a5c; height: 12px; text-align: center; color: #e2e8f0; font-size: 10px; }
                QProgressBar::chunk { background: #00f0ff; }
            """)
            row.addWidget(lbl)
            row.addWidget(bar)
            row.addStretch()
            tel_layout.addLayout(row)
            self._progress_bars[key] = bar
        tel_layout.addStretch()
        self.add_panel("Telemetry", telemetry)

        self.set_status("AION ready — 4 panels loaded")

    def _setup_watchdog(self) -> None:
        self._watchdog_timer = QTimer(self)
        self._watchdog_timer.timeout.connect(self._watchdog_tick)
        self._watchdog_timer.start(500)

    def _watchdog_tick(self) -> None:
        self._tick_count += 1
        self._mutation_engine.max_mutations_per_tick = self._max_nodes_cycle
        self._mutation_engine.tick()
        self._manifold.rebuild_tree_if_needed()

        if self._fs_engine and self._tick_count % 3 == 0:
            self._fs_engine.manifold.rebuild_tree_if_needed()

        if self._tick_count % 2 == 0:
            smap = self._salience_engine.compute_salience_map()

        if self._tick_count % 5 == 0:
            for node in self._manifold.get_random_nodes(min(2, self._manifold.size)):
                self._constraint_engine.collapse(node.id)

        if self._tick_count % 20 == 0:
            self._world_model.detect_drift()
            self._world_model.checkpoint()

        nodes = self._manifold.size
        mutations = self._mutation_engine.mutation_count
        avg_salience = sum(n.salience for n in self._manifold.nodes.values()) / max(1, nodes)
        avg_confidence = sum(n.confidence for n in self._manifold.nodes.values()) / max(1, nodes)
        avg_entropy = sum(n.entropy for n in self._manifold.nodes.values()) / max(1, nodes)
        drift = self._world_model.drift_score

        if self._fs_engine:
            fs_nodes = self._fs_engine.path_count()
            node_display = f"{nodes} (fs:{fs_nodes})"
        else:
            node_display = str(nodes)

        self._status_labels["State Nodes"].setText(node_display)
        self._status_labels["Mutations"].setText(str(mutations))
        self._status_labels["Salience"].setText(f"{avg_salience:.4f}")
        self._status_labels["Confidence"].setText(f"{avg_confidence:.4f}")
        self._status_labels["Entropy"].setText(f"{avg_entropy:.4f}")
        self._status_labels["Drift"].setText(f"{drift:.5f}")

        self._progress_bars["CPU"].setValue(int(avg_salience * 100))
        self._progress_bars["Memory"].setValue(nodes // 100)
        self._progress_bars["Frame Time"].setValue(int((1 - avg_confidence) * 50))

        if self._tick_count % 10 == 0 and hasattr(self, "_console"):
            if avg_entropy > 0.5:
                mood = "exploring diverse states"
            elif avg_salience > 0.1:
                mood = "converging on salient regions"
            else:
                mood = "settling into stable structure"
            line = (
                f"── cycle {self._tick_count} ──\n"
                f"  {nodes} active nodes  ·  {mutations:,} total mutations\n"
                f"  avg salience {avg_salience:.3f}  ·  avg confidence {avg_confidence:.3f}  ·  avg entropy {avg_entropy:.3f}\n"
                f"  drift {drift:.5f}  ·  {mood}\n"
            )
            if self._fs_engine:
                recent = self._fs_engine.top_recent(5)
                line += f"  fs: {self._fs_engine.path_count()} files tracked\n"
                line += "  recent files:\n"
                for m in recent:
                    line += f"    {m.path}  (recency {m.recency_score:.2f}, {m.size//1024 if m.size > 1024 else 1}KB)\n"
            self._console.appendPlainText(line)

    def add_panel(
        self, title: str, widget: QWidget, index: int = -1
    ) -> int:
        if self._tab_widget is None:
            return -1
        return self._tab_widget.addTab(widget, title)

    def remove_panel(self, index: int) -> None:
        if self._tab_widget is not None:
            self._tab_widget.removeTab(index)

    def set_status(self, message: str, timeout: int = 0) -> None:
        self._status_bar.showMessage(message, timeout)

    @property
    def tab_widget(self) -> CyberTabWidget | None:
        return self._tab_widget

    @property
    def theme(self) -> Theme:
        return self._theme

    @theme.setter
    def theme(self, theme: Theme) -> None:
        self._theme = theme
        self._apply_theme()

    @property
    def action_registry(self) -> ActionRegistry:
        return self._action_registry

    @property
    def sound_engine(self) -> SoundEngine:
        return self._sound_engine

    @property
    def profile_manager(self) -> WorkspaceProfileManager:
        return self._profile_manager

    def save_profile(self, name: str) -> None:
        profile = self._profile_manager.save(name, self)
        self.set_status(f"Profile '{name}' saved")

    def load_profile(self, name: str) -> None:
        if self._profile_manager.load(name, self):
            self.set_status(f"Profile '{name}' loaded")
        else:
            self.set_status(f"Profile '{name}' not found", timeout=3000)
