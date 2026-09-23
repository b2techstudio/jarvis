from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QApplication


def main() -> int:
    QApplication.instance() or QApplication([])
    output = Path(__file__).resolve().parents[1] / "packaging" / "jarvis.ico"
    output.parent.mkdir(parents=True, exist_ok=True)
    size = 256
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    center = image.rect().center()
    gradient = QRadialGradient(center, 118)
    gradient.setColorAt(0.0, QColor("#173b48"))
    gradient.setColorAt(0.72, QColor("#0b151d"))
    gradient.setColorAt(1.0, QColor("#070b10"))
    painter.setBrush(gradient)
    painter.setPen(QPen(QColor("#70e7ff"), 7))
    painter.drawEllipse(15, 15, 226, 226)
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(QColor(112, 231, 255, 160), 4))
    painter.drawEllipse(42, 42, 172, 172)
    painter.setPen(QPen(QColor(112, 231, 255, 100), 3))
    painter.drawEllipse(68, 68, 120, 120)
    painter.setPen(QPen(QColor("#e8f7fb"), 13, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawLine(104, 88, 104, 158)
    painter.drawArc(104, 144, 49, 30, 180 * 16, 180 * 16)
    painter.drawLine(153, 88, 153, 144)
    painter.end()
    if not image.save(str(output), "ICO"):
        raise RuntimeError("Impossible de générer l’icône Windows.")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

