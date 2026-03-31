# -*- coding: utf-8 -*-

import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QDoubleSpinBox, QSpinBox,
                              QGroupBox, QMessageBox, QComboBox, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont

from constants import *
from regression import run_ffe
from gui.results_window import ResultsWindow


class FFEWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, factor_ranges, response_key, limit_value, replications):
        super().__init__()
        self.factor_ranges = factor_ranges
        self.response_key = response_key
        self.limit_value = limit_value
        self.replications = replications

    def run(self):
        try:
            result = run_ffe(
                self.factor_ranges,
                response_key=self.response_key,
                limit_value=self.limit_value,
                replications=self.replications,
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.factor_spins = {}
        self.init_ui()
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

    def init_ui(self):
        self.setWindowTitle("Лабораторная №2: ПФЭ 2⁶ на имитационной модели СМО")
        self.setFixedSize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 15, 20, 15)

        # Заголовок
        title = QLabel("Полный факторный эксперимент 2⁶")
        title_font = QFont("Arial", FONT_SIZE_TITLE + 2)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        subtitle = QLabel(
            "Одноканальная СМО • Относительные приоритеты • "
            "6 факторов: λ₁, σ₁, μ₁, λ₂, σ₂, μ₂ • 64 эксперимента"
        )
        subtitle.setFont(QFont("Arial", 9))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #7F8C8D;")
        main_layout.addWidget(subtitle)

        # Выходная переменная
        response_layout = QHBoxLayout()
        response_label = QLabel("Выходная переменная:")
        response_label.setFont(QFont("Arial", FONT_SIZE_LABEL))
        response_layout.addWidget(response_label)

        self.response_combo = QComboBox()
        self.response_combo.setFont(QFont("Arial", FONT_SIZE_INPUT))
        for opt in RESPONSE_OPTIONS:
            self.response_combo.addItem(opt['label'], opt['key'])
        response_layout.addWidget(self.response_combo)
        response_layout.addStretch()
        main_layout.addLayout(response_layout)

        # Факторы — тип 1
        factors1_group = self._create_factors_group(
            "Факторы типа 1 (высокий приоритет)",
            [FACTORS[0], FACTORS[1], FACTORS[2]],
            [(DEFAULT_LAMBDA1, DEFAULT_DELTA_LAMBDA1),
             (DEFAULT_SIGMA1, DEFAULT_DELTA_SIGMA1),
             (DEFAULT_MU1, DEFAULT_DELTA_MU1)]
        )
        main_layout.addWidget(factors1_group)

        # Факторы — тип 2
        factors2_group = self._create_factors_group(
            "Факторы типа 2 (низкий приоритет)",
            [FACTORS[3], FACTORS[4], FACTORS[5]],
            [(DEFAULT_LAMBDA2, DEFAULT_DELTA_LAMBDA2),
             (DEFAULT_SIGMA2, DEFAULT_DELTA_SIGMA2),
             (DEFAULT_MU2, DEFAULT_DELTA_MU2)]
        )
        main_layout.addWidget(factors2_group)

        # Параметры моделирования
        params_group = self._create_params_group()
        main_layout.addWidget(params_group)

        main_layout.addStretch()

        # Кнопка запуска
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.run_button = QPushButton("Провести ПФЭ (64 эксперимента)")
        self.run_button.setFont(QFont("Arial", FONT_SIZE_BUTTON))
        self.run_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_BUTTON_SUCCESS};
                color: white;
                border: none;
                padding: 10px 25px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_BUTTON_SUCCESS_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {COLOR_BUTTON_SECONDARY};
            }}
        """)
        self.run_button.clicked.connect(self._start_ffe)
        button_layout.addWidget(self.run_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        central_widget.setLayout(main_layout)

    def _create_factors_group(self, title, factors, defaults):
        group = QGroupBox(title)
        group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        group.setStyleSheet(self._get_group_style())

        layout = QVBoxLayout()
        layout.setSpacing(6)

        header = QHBoxLayout()
        for text, width in [("Фактор", 120), ("Центр (x₀)", 100),
                            ("Интервал (Δ)", 100), ("min", 80), ("max", 80)]:
            lbl = QLabel(text)
            lbl.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            lbl.setFixedWidth(width)
            lbl.setStyleSheet("color: #7F8C8D;")
            header.addWidget(lbl)
        header.addStretch()
        layout.addLayout(header)

        for factor, (center_val, delta_val) in zip(factors, defaults):
            row = self._create_factor_row(factor, center_val, delta_val)
            layout.addLayout(row)

        group.setLayout(layout)
        return group

    def _create_factor_row(self, factor, center_val, delta_val):
        row = QHBoxLayout()
        row.setSpacing(8)

        name = QLabel(f"{factor['label']} ({factor['desc']})")
        name.setFont(QFont("Arial", FONT_SIZE_LABEL))
        name.setFixedWidth(120)
        row.addWidget(name)

        center_spin = QDoubleSpinBox()
        center_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        center_spin.setRange(0.001, 100.0)
        center_spin.setValue(center_val)
        center_spin.setSingleStep(0.1)
        center_spin.setDecimals(3)
        center_spin.setFixedWidth(100)
        row.addWidget(center_spin)

        delta_spin = QDoubleSpinBox()
        delta_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        delta_spin.setRange(0.001, 50.0)
        delta_spin.setValue(delta_val)
        delta_spin.setSingleStep(0.01)
        delta_spin.setDecimals(3)
        delta_spin.setFixedWidth(100)
        row.addWidget(delta_spin)

        min_label = QLabel(f"{center_val - delta_val:.3f}")
        min_label.setFont(QFont("Arial", FONT_SIZE_INPUT))
        min_label.setFixedWidth(80)
        min_label.setStyleSheet("color: #2196F3;")
        row.addWidget(min_label)

        max_label = QLabel(f"{center_val + delta_val:.3f}")
        max_label.setFont(QFont("Arial", FONT_SIZE_INPUT))
        max_label.setFixedWidth(80)
        max_label.setStyleSheet("color: #F44336;")
        row.addWidget(max_label)

        def update_labels(*_):
            c, d = center_spin.value(), delta_spin.value()
            min_label.setText(f"{c - d:.3f}")
            max_label.setText(f"{c + d:.3f}")

        center_spin.valueChanged.connect(update_labels)
        delta_spin.valueChanged.connect(update_labels)

        row.addStretch()

        self.factor_spins[factor['key']] = (center_spin, delta_spin)
        return row

    def _create_params_group(self):
        group = QGroupBox("Параметры моделирования")
        group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        group.setStyleSheet(self._get_group_style())

        layout = QHBoxLayout()
        layout.setSpacing(20)

        lbl1 = QLabel("Обслужить заявок:")
        lbl1.setFont(QFont("Arial", FONT_SIZE_LABEL))
        layout.addWidget(lbl1)

        self.limit_spin = QSpinBox()
        self.limit_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        self.limit_spin.setRange(100, 100000)
        self.limit_spin.setValue(DEFAULT_LIMIT_VALUE)
        self.limit_spin.setSingleStep(1000)
        layout.addWidget(self.limit_spin)

        lbl2 = QLabel("Повторов на точку:")
        lbl2.setFont(QFont("Arial", FONT_SIZE_LABEL))
        layout.addWidget(lbl2)

        self.repl_spin = QSpinBox()
        self.repl_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        self.repl_spin.setRange(1, 50)
        self.repl_spin.setValue(DEFAULT_REPLICATIONS)
        layout.addWidget(self.repl_spin)

        layout.addStretch()
        group.setLayout(layout)
        return group

    def _get_group_style(self):
        return f"""
            QGroupBox {{
                background-color: {COLOR_WIDGET_BG};
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                margin-top: 10px;
                padding: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """

    def _get_factor_ranges(self):
        ranges = []
        for factor in FACTORS:
            center_spin, delta_spin = self.factor_spins[factor['key']]
            c = center_spin.value()
            d = delta_spin.value()
            lo = c - d
            hi = c + d
            if lo <= 0:
                raise ValueError(
                    f"Фактор {factor['label']}: минимум ({lo:.3f}) должен быть > 0"
                )
            ranges.append((lo, hi))
        return ranges

    def _start_ffe(self):
        try:
            factor_ranges = self._get_factor_ranges()
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return

        response_key = self.response_combo.currentData()
        limit_value = self.limit_spin.value()
        replications = self.repl_spin.value()

        self.run_button.setEnabled(False)
        self.run_button.setText("Выполняется ПФЭ...")

        self._worker = FFEWorker(factor_ranges, response_key,
                                  limit_value, replications)
        self._worker.finished.connect(self._on_ffe_finished)
        self._worker.error.connect(self._on_ffe_error)

        self._thread = threading.Thread(target=self._worker.run, daemon=True)
        self._thread.start()

    def _on_ffe_finished(self, result):
        self.run_button.setEnabled(True)
        self.run_button.setText("Провести ПФЭ (64 эксперимента)")

        self._results_window = ResultsWindow(result, self)
        self._results_window.show()

    def _on_ffe_error(self, msg):
        self.run_button.setEnabled(True)
        self.run_button.setText("Провести ПФЭ (64 эксперимента)")
        QMessageBox.critical(self, "Ошибка", f"Ошибка ПФЭ:\n{msg}")
