"""Show weather icons and font options for visual review.

Usage:
    python icon_demo.py
"""
import os
import sys

from PyQt5.QtCore import Qt, QByteArray
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QFontDatabase
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QScrollArea, QGridLayout,
)
from PyQt5.QtSvg import QSvgRenderer


ICONS = [
    ('sunny', 'sunny.svg'),
    ('partly-cloudy', 'partly-cloudy.svg'),
    ('cloudy', 'cloudy.svg'),
    ('rain', 'rain.svg'),
    ('windy', 'windy.svg'),
    ('thunderstorm', 'thunderstorm.svg'),
]

# Candidate fonts for the app (only those installed locally are shown)
FONT_CANDIDATES = [
    'Segoe UI',
    'Arial',
    'Calibri',
    'Tahoma',
    'Verdana',
    'Trebuchet MS',
    'DejaVu Sans',
    'Liberation Sans',
    'Noto Sans',
    'Georgia',
    'Times New Roman',
    'Consolas',
    'Courier New',
    'Impact',
]

ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons')
ICON_SIZE = 96
OPACITY = 0.28
CELL_BG = '#d3d3d3'  # match main window grey
HINT_ALPHA = int(OPACITY * 255)


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


def available_fonts():
    installed = set(QFontDatabase().families())
    return [name for name in FONT_CANDIDATES if name in installed]


def make_icon_cell(name, filename, opacity):
    cell = QFrame()
    cell.setFixedSize(120, 140)
    cell.setStyleSheet(f'border: 1px solid black; background-color: {CELL_BG};')
    layout = QVBoxLayout(cell)

    icon = QLabel()
    icon.setPixmap(render_icon(filename, opacity=opacity))
    icon.setAlignment(Qt.AlignCenter)
    icon.setStyleSheet('border: none; background: transparent;')

    label = QLabel(name)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet('border: none; background: transparent;')

    layout.addWidget(icon)
    layout.addWidget(label)
    return cell


def apply_app_main_font(label, family=None):
    """Match main.py update_cell title/body text styling."""
    font = label.font()
    if family:
        font.setFamily(family)
    font.setBold(True)
    font.setPointSize(int(font.pointSize() * 1.5))
    label.setFont(font)


def apply_app_corner_font(label, family=None):
    """Match main.py _weather_corner_label styling."""
    font = label.font()
    if family:
        font.setFamily(family)
    font.setBold(True)
    font.setPointSize(max(16, int(font.pointSize() * 1.8)))
    label.setFont(font)


def make_font_cell(font_name, icon_filename='sunny.svg'):
    """Mock a bottom-row cell: main text + faint +0 / temp corners."""
    # Roughly same cell size as main.py (480x320 grid with _fudge=12)
    cell = QFrame()
    cell.setFixedSize(148, 148)
    cell.setStyleSheet(f'border: 1px solid black; background-color: {CELL_BG};')

    stack = QGridLayout(cell)
    stack.setContentsMargins(4, 2, 4, 2)
    stack.setSpacing(0)

    icon = QLabel()
    icon.setPixmap(render_icon(icon_filename, size=90, opacity=OPACITY))
    icon.setAlignment(Qt.AlignCenter)
    icon.setStyleSheet('border: none; background: transparent;')
    stack.addWidget(icon, 0, 0)

    # Same pattern as main.py: title + body
    family = None if font_name == '(app default)' else font_name
    main = QLabel('Wind\n12g14 SW')
    main.setAlignment(Qt.AlignCenter)
    main.setStyleSheet('border: none; background: transparent;')
    apply_app_main_font(main, family)
    stack.addWidget(main, 0, 0)

    offset = QLabel('+0')
    offset.setStyleSheet(
        f'border: none; background: transparent; color: rgba(51, 51, 51, {HINT_ALPHA});'
    )
    apply_app_corner_font(offset, family)
    stack.addWidget(offset, 0, 0, Qt.AlignTop | Qt.AlignLeft)

    temp = QLabel('72°F')
    temp.setStyleSheet(
        f'border: none; background: transparent; color: rgba(51, 51, 51, {HINT_ALPHA});'
    )
    apply_app_corner_font(temp, family)
    stack.addWidget(temp, 0, 0, Qt.AlignBottom | Qt.AlignRight)

    name = QLabel(font_name)
    name.setAlignment(Qt.AlignCenter)
    name.setStyleSheet('border: none; background: transparent; color: #555;')
    nfont = QFont()
    nfont.setPointSize(8)
    name.setFont(nfont)

    wrapper = QVBoxLayout()
    wrapper.setSpacing(2)
    wrapper.addWidget(cell)
    wrapper.addWidget(name)

    holder = QWidget()
    holder.setLayout(wrapper)
    return holder


class IconDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Weather icon + font review')
        self.setMinimumSize(900, 700)

        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(CELL_BG))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        page = QWidget()
        root = QVBoxLayout(page)

        root.addWidget(QLabel('Icons at app opacity (~28%) on the same grey as the clock cells'))
        row = QHBoxLayout()
        for name, filename in ICONS:
            row.addWidget(make_icon_cell(name, filename, OPACITY))
        root.addLayout(row)

        root.addWidget(QLabel('Full opacity (for spotting fill/background issues):'))
        row_full = QHBoxLayout()
        for name, filename in ICONS:
            row_full.addWidget(make_icon_cell(name, filename, 1.0))
        root.addLayout(row_full)

        fonts = ['(app default)'] + available_fonts()
        root.addWidget(QLabel(
            f'Font candidates using app styling: bold main ×1.5, bold corners ×1.8 '
            f'({len(fonts) - 1} installed + current default):'
        ))

        fonts_grid = QGridLayout()
        fonts_grid.setSpacing(10)
        cols = 4
        for i, font_name in enumerate(fonts):
            # Cycle icons so each font preview isn't identical
            icon_file = ICONS[i % len(ICONS)][1]
            fonts_grid.addWidget(make_font_cell(font_name, icon_file), i // cols, i % cols)
        root.addLayout(fonts_grid)
        root.addStretch(1)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = IconDemo()
    win.show()
    sys.exit(app.exec_())
