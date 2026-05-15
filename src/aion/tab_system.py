from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtWidgets import QStackedWidget, QTabBar, QVBoxLayout, QWidget


class DraggableTabBar(QTabBar):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMovable(True)
        self.setTabsClosable(True)
        self.setDocumentMode(True)
        self.setExpanding(False)
        self._drag_start_pos: QPoint | None = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)


class CyberTabWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tab_bar = DraggableTabBar(self)
        self._stack = QStackedWidget(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._tab_bar)
        layout.addWidget(self._stack)

        self._tab_bar.currentChanged.connect(self._stack.setCurrentIndex)
        self._tab_bar.tabCloseRequested.connect(self._close_tab)

        self._tab_bar.setStyleSheet("""
            QTabBar::tab {
                padding: 6px 16px;
                min-width: 80px;
            }
        """)

    def addTab(self, widget: QWidget, title: str) -> int:
        index = self._stack.addWidget(widget)
        self._tab_bar.insertTab(index, title)
        return index

    def removeTab(self, index: int) -> None:
        widget = self._stack.widget(index)
        if widget:
            self._stack.removeWidget(widget)
            widget.deleteLater()
        self._tab_bar.removeTab(index)

    def currentIndex(self) -> int:
        return self._tab_bar.currentIndex()

    def setCurrentIndex(self, index: int) -> None:
        self._tab_bar.setCurrentIndex(index)

    def count(self) -> int:
        return self._tab_bar.count()

    def tabText(self, index: int) -> str:
        return self._tab_bar.tabText(index)

    def setTabText(self, index: int, text: str) -> None:
        self._tab_bar.setTabText(index, text)

    def _close_tab(self, index: int) -> None:
        self.removeTab(index)

    @property
    def tab_bar(self) -> DraggableTabBar:
        return self._tab_bar
