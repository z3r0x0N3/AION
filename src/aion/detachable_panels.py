from __future__ import annotations

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QDockWidget, QMainWindow, QTabWidget, QWidget


class DetachablePanel(QDockWidget):
    def __init__(self, title: str, widget: QWidget, parent: QMainWindow | None = None) -> None:
        super().__init__(title, parent)
        self.setWidget(widget)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.TopDockWidgetArea
            | Qt.DockWidgetArea.BottomDockWidgetArea
        )


class PanelManager:
    def __init__(self, main_window: QMainWindow) -> None:
        self._main = main_window
        self._panels: dict[str, DetachablePanel] = {}

    def add_panel(
        self,
        name: str,
        title: str,
        widget: QWidget,
        area: Qt.DockWidgetArea = Qt.DockWidgetArea.RightDockWidgetArea,
    ) -> DetachablePanel:
        panel = DetachablePanel(title, widget, self._main)
        self._main.addDockWidget(area, panel)
        self._panels[name] = panel
        return panel

    def remove_panel(self, name: str) -> bool:
        panel = self._panels.pop(name, None)
        if panel is None:
            return False
        self._main.removeDockWidget(panel)
        panel.deleteLater()
        return True

    def get_panel(self, name: str) -> DetachablePanel | None:
        return self._panels.get(name)

    def float_panel(self, name: str) -> bool:
        panel = self._panels.get(name)
        if panel is None:
            return False
        panel.setFloating(True)
        return True

    def dock_panel(self, name: str) -> bool:
        panel = self._panels.get(name)
        if panel is None:
            return False
        panel.setFloating(False)
        return True

    @property
    def panel_names(self) -> list[str]:
        return list(self._panels.keys())

    def panel_count(self) -> int:
        return len(self._panels)
