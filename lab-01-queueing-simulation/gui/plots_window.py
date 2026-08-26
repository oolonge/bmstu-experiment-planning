# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import numpy as np

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from constants import *


class PlotsWindow(QMainWindow):

    def __init__(self, plots_data: list, parent=None):
        super().__init__(parent)
        self.plots_data = plots_data
        self.current_idx = 0
        self.smooth_enabled = PLOT_SMOOTH
        self.init_ui()
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

    def init_ui(self):
        self.setWindowTitle("Графики зависимостей (стационарный режим)")
        self.setFixedSize(PLOTS_WINDOW_WIDTH, PLOTS_WINDOW_HEIGHT)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Область графика
        self.fig = Figure(figsize=(9, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.fig)
        main_layout.addWidget(self.canvas)

        # Навигация
        nav_layout = QHBoxLayout()

        prev_button = QPushButton("◀ Предыдущий")
        prev_button.setFont(QFont("Arial", FONT_SIZE_BUTTON))
        prev_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_BUTTON};
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_BUTTON_HOVER};
            }}
        """)
        prev_button.clicked.connect(self._prev_plot)
        nav_layout.addWidget(prev_button)

        nav_layout.addStretch()

        self.counter_label = QLabel()
        self.counter_label.setFont(QFont("Arial", FONT_SIZE_LABEL))
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.counter_label)

        self.smooth_checkbox = QCheckBox("Сглаживание")
        self.smooth_checkbox.setFont(QFont("Arial", FONT_SIZE_LABEL))
        self.smooth_checkbox.setChecked(self.smooth_enabled)
        self.smooth_checkbox.toggled.connect(self._on_smooth_toggled)
        nav_layout.addWidget(self.smooth_checkbox)

        nav_layout.addStretch()

        next_button = QPushButton("Следующий ▶")
        next_button.setFont(QFont("Arial", FONT_SIZE_BUTTON))
        next_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_BUTTON};
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_BUTTON_HOVER};
            }}
        """)
        next_button.clicked.connect(self._next_plot)
        nav_layout.addWidget(next_button)

        main_layout.addLayout(nav_layout)
        central_widget.setLayout(main_layout)

        self._update_plot()

    def _smooth_curve(self, x, y):
        """Полиномиальная аппроксимация: восстанавливает гладкую кривую по точкам."""
        if len(x) < 2:
            return x, y
        x_arr = np.array(x)
        y_arr = np.array(y)
        degree = min(PLOT_SMOOTH_POLY_DEGREE, len(x) - 1)
        coeffs = np.polyfit(x_arr, y_arr, degree)
        poly = np.poly1d(coeffs)
        x_smooth = np.linspace(x_arr[0], x_arr[-1], PLOT_SMOOTH_POINTS)
        y_smooth = poly(x_smooth)
        y_smooth = np.maximum(y_smooth, 0)
        return x_smooth.tolist(), y_smooth.tolist()

    def _update_plot(self):
        if not self.plots_data:
            return

        plot = self.plots_data[self.current_idx]

        self.ax.clear()

        if self.smooth_enabled and len(plot['x']) >= 2:
            x1, y1 = self._smooth_curve(plot['x'], plot['y1'])
            x2, y2 = self._smooth_curve(plot['x'], plot['y2'])
            self.ax.plot(x1, y1, 'b-', linewidth=2,
                         label="Тип 1 (высокий приоритет)")
            self.ax.plot(x2, y2, 'r--', linewidth=2,
                         label="Тип 2 (низкий приоритет)")
        else:
            self.ax.plot(plot['x'], plot['y1'], 'b-o', linewidth=2,
                         markersize=5, label="Тип 1 (высокий приоритет)")
            self.ax.plot(plot['x'], plot['y2'], 'r--s', linewidth=2,
                         markersize=5, label="Тип 2 (низкий приоритет)")

        self.ax.set_title(plot['title'], fontsize=12, fontweight='bold')
        self.ax.set_xlabel(plot['xlabel'], fontsize=11)
        self.ax.set_ylabel("Среднее время ожидания", fontsize=11)
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(fontsize=10)
        self.fig.tight_layout()
        self.canvas.draw()

        self.counter_label.setText(
            f"График {self.current_idx + 1} из {len(self.plots_data)}")

    def _on_smooth_toggled(self, checked: bool):
        self.smooth_enabled = checked
        self._update_plot()

    def _next_plot(self):
        if self.plots_data:
            self.current_idx = (self.current_idx + 1) % len(self.plots_data)
            self._update_plot()

    def _prev_plot(self):
        if self.plots_data:
            self.current_idx = (self.current_idx - 1) % len(self.plots_data)
            self._update_plot()
