from __future__ import annotations

import math

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from app.core.events import AssistantState


class AssistantOrb(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(230, 230)
        self.phase = 0.0
        self.state = AssistantState.IDLE
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)

    def set_state(self, state: AssistantState) -> None:
        self.state = state
        self.update()

    def _tick(self) -> None:
        speed = 0.11 if self.state in {AssistantState.LISTENING, AssistantState.ANALYZING} else 0.045
        self.phase += speed
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center = self.rect().center()
        base = min(self.width(), self.height()) / 2 - 25
        active = self.state is not AssistantState.IDLE
        color = QColor("#70e7ff" if self.state is not AssistantState.ERROR else "#ff6b81")
        for index in range(3):
            pulse = math.sin(self.phase + index * 1.8) * (7 if active else 2)
            radius = base - index * 24 + pulse
            ring = QColor(color)
            ring.setAlpha(180 - index * 45)
            painter.setPen(QPen(ring, 2.5 if index == 0 else 1.3))
            painter.drawEllipse(center, radius, radius)
        glow = QColor(color)
        glow.setAlpha(35 + int((math.sin(self.phase) + 1) * 18))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, base - 55, base - 55)

