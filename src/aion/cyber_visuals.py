from __future__ import annotations

import math
import random

from PyQt6.QtCore import QPoint, QPointF, QRect, QSize, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import QWidget


class HexGridOverlay(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        hex_size: int = 30,
        opacity: float = 0.15,
        pulse_speed: float = 1.0,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._hex_size = hex_size
        self._opacity = opacity
        self._pulse = 0.0
        self._pulse_speed = pulse_speed
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(50)

    def _animate(self) -> None:
        self._pulse += 0.02 * self._pulse_speed
        self.update()

    def set_opacity(self, opacity: float) -> None:
        self._opacity = max(0.0, min(1.0, opacity))
        self.update()

    def set_hex_size(self, size: int) -> None:
        self._hex_size = max(5, size)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor(0, 240, 255)
        color.setAlphaF(self._opacity * (0.7 + 0.3 * math.sin(self._pulse)))
        pen = QPen(color, 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        w = self.width()
        h = self.height()
        hw = self._hex_size * math.sqrt(3)
        hh = self._hex_size * 1.5

        cols = int(w / hw) + 2
        rows = int(h / hh) + 2

        for row in range(rows):
            for col in range(cols):
                x = col * hw + (row % 2) * hw / 2
                y = row * hh - self._hex_size * 0.5
                center = QPointF(x, y)
                path = self._hex_path(center, self._hex_size)
                painter.drawPath(path)

    def _hex_path(self, center: QPointF, size: float) -> QPainterPath:
        path = QPainterPath()
        for i in range(6):
            angle = math.pi / 3 * i - math.pi / 6
            px = center.x() + size * math.cos(angle)
            py = center.y() + size * math.sin(angle)
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        path.closeSubpath()
        return path

    def setVisible(self, visible: bool) -> None:
        super().setVisible(visible)
        if visible:
            self.raise_()
            self._timer.start()
        else:
            self._timer.stop()


class ScanLineOverlay(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        line_spacing: int = 3,
        opacity: float = 0.05,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._line_spacing = line_spacing
        self._opacity = opacity
        self._scroll = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(33)

    def _animate(self) -> None:
        self._scroll = (self._scroll + 0.5) % self._line_spacing
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        color = QColor(0, 0, 0)
        color.setAlphaF(self._opacity)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        for y in range(int(self._scroll), self.height(), self._line_spacing):
            painter.drawRect(0, y, self.width(), 1)


class ParticleSystem(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        max_particles: int = 50,
        opacity: float = 0.4,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setMouseTracking(True)
        self._max_particles = max_particles
        self._opacity = opacity
        self._particles: list[dict] = []
        self._cursor_pos = QPointF(0, 0)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_particles)
        self._timer.start(16)

    def mouseMoveEvent(self, event) -> None:
        self._cursor_pos = QPointF(event.pos())
        self._spawn_particle()

    def _spawn_particle(self) -> None:
        if len(self._particles) >= self._max_particles:
            return
        self._particles.append({
            "x": self._cursor_pos.x(),
            "y": self._cursor_pos.y(),
            "vx": random.uniform(-1, 1),
            "vy": random.uniform(-2, 0),
            "life": 1.0,
            "decay": random.uniform(0.01, 0.03),
            "size": random.uniform(1.5, 3.5),
        })

    def _update_particles(self) -> None:
        for p in self._particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.05
            p["life"] -= p["decay"]
        self._particles = [p for p in self._particles if p["life"] > 0]
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for p in self._particles:
            color = QColor(0, 240, 255)
            color.setAlphaF(p["life"] * self._opacity)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(p["x"], p["y"]), p["size"], p["size"])
