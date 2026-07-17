"""Show all weather icons in a row for visual review.

Usage:
    python icon_demo.py
"""
import os
import sys

from PyQt5.QtCore import Qt, QByteArray
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PyQt5.QtSvg import QSvgRenderer


ICONS = [
    ('sunny', 'sunny.svg'),
    ('partly-cloudy', 'partly-cloudy.svg'),
    ('cloudy', 'cloudy.svg'),
    ('rain', 'rain.svg'),
    ('windy', 'windy.svg'),
    ('thunderstorm', 'thunderstorm.svg'),
]

ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons')
ICON_SIZE = 96
OPACITY = 0.28
CELL_BG = QColor(211, 211, 211)  # match main window grey


def render_icon(filename, size=ICON_SIZE, opacity=OPACITY):
    path = os.path.join(ICON_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        svg = f.read().replace('currentColor', '#333333')

    renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setOpacity(opacity)
    renderer.render(painter)
    painter.end()
    return pixmap


class IconDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Weather icon review')
        self.setMinimumSize(780, 220)

        palette = self.palette()
        palette.setColor(self.backgroundRole(), CELL_BG)
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        root = QVBoxLayout(self)
        root.addWidget(QLabel('Icons at app opacity (~28%) on the same grey as the clock cells'))

        row = QHBoxLayout()
        for name, filename in ICONS:
            cell = QFrame()
            cell.setFixedSize(120, 140)
            cell.setStyleSheet('border: 1px solid black; background-color: #d3d3d3;')
            layout = QVBoxLayout(cell)

            icon = QLabel()
            icon.setPixmap(render_icon(filename))
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet('border: none; background: transparent;')

            label = QLabel(name)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet('border: none; background: transparent;')

            layout.addWidget(icon)
            layout.addWidget(label)
            row.addWidget(cell)

        root.addLayout(row)
        root.addWidget(QLabel('Full opacity (for spotting fill/background issues):'))

        row_full = QHBoxLayout()
        for name, filename in ICONS:
            cell = QFrame()
            cell.setFixedSize(120, 140)
            cell.setStyleSheet('border: 1px solid black; background-color: #d3d3d3;')
            layout = QVBoxLayout(cell)

            icon = QLabel()
            icon.setPixmap(render_icon(filename, opacity=1.0))
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet('border: none; background: transparent;')

            label = QLabel(name)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet('border: none; background: transparent;')

            layout.addWidget(icon)
            layout.addWidget(label)
            row_full.addWidget(cell)

        root.addLayout(row_full)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = IconDemo()
    win.show()
    sys.exit(app.exec_())
