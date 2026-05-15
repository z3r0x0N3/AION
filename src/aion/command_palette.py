from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from aion.action_registry import ActionRegistry


class CommandPalette(QDialog):
    def __init__(
        self, registry: ActionRegistry, parent: object | None = None
    ) -> None:
        super().__init__(parent)
        self._registry = registry
        self.setWindowTitle("Commands")
        self.setModal(True)
        self.resize(500, 400)
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.FramelessWindowHint
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Type a command...")
        self._search.textChanged.connect(self._filter)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.itemClicked.connect(self._execute_selected)
        layout.addWidget(self._list)

        self._search.setFocus()
        self._search.returnPressed.connect(self._execute_first)

        self._populate()
        self.setStyleSheet("""
            CommandPalette {
                background-color: #1e293b;
                border: 1px solid #00f0ff;
                border-radius: 4px;
            }
            QLineEdit {
                background-color: #111827;
                color: #e2e8f0;
                border: 1px solid #2a3a5c;
                padding: 6px 10px;
                font-size: 14px;
            }
            QListWidget {
                background-color: #111827;
                color: #e2e8f0;
                border: none;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item:selected {
                background-color: #263548;
                color: #00f0ff;
            }
        """)

    def _populate(self) -> None:
        self._list.clear()
        for name, binding in self._registry.all_bindings.items():
            shortcut = binding.current_shortcut or binding.default_shortcut
            text = f"{binding.description}  [{shortcut}]" if shortcut else binding.description
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, name)
            self._list.addItem(item)

    def _filter(self) -> None:
        query = self._search.text().lower()
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item is None:
                continue
            item.setHidden(query not in item.text().lower())

    def _execute_selected(self, item: QListWidgetItem) -> None:
        name = item.data(Qt.ItemDataRole.UserRole)
        if name:
            self._registry.execute(name)
        self.accept()

    def _execute_first(self) -> None:
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item and not item.isHidden():
                self._execute_selected(item)
                return

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key.Key_Down:
            current = self._list.currentRow()
            self._list.setCurrentRow(min(current + 1, self._list.count() - 1))
        elif event.key() == Qt.Key.Key_Up:
            current = self._list.currentRow()
            self._list.setCurrentRow(max(current - 1, 0))
        else:
            super().keyPressEvent(event)
