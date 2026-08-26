# -*- coding: utf-8 -*-

import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QDoubleSpinBox, QSpinBox,
                              QGroupBox, QMessageBox, QRadioButton,
                              QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont

from constants import *
from simulation import Simulation, validate_params, build_all_plots
from gui.results_window import ResultsWindow
from gui.plots_window import PlotsWindow


class SimulationWorker(QObject):
    finished = pyqtSignal(dict, dict, list)
    error = pyqtSignal(str)

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        try:
            sim = Simulation(**self.params)
            results = sim.run()
            plots = build_all_plots(self.params)
            self.finished.emit(results, self.params, plots)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.plots_window = None
        self.init_ui()
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

    def init_ui(self):
        self.setWindowTitle("Лабораторная №1: Моделирование СМО")
        self.setFixedSize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("Моделирование одноканальной СМО")
        title_font = QFont("Arial", FONT_SIZE_TITLE + 2)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        subtitle = QLabel("Относительные приоритеты • Нормальное поступление • Экспоненциальное обслуживание")
        subtitle.setFont(QFont("Arial", 9))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #7F8C8D;")
        main_layout.addWidget(subtitle)

        # Генератор 1
        gen1_group = self._create_generator_group(
            "Генератор заявок типа 1 (высокий приоритет)",
            DEFAULT_LAMBDA1, DEFAULT_SIGMA1, DEFAULT_MU1)
        self.lambda1_spin, self.sigma1_spin, self.mu1_spin = self._last_spins
        main_layout.addWidget(gen1_group)

        # Генератор 2
        gen2_group = self._create_generator_group(
            "Генератор заявок типа 2 (низкий приоритет)",
            DEFAULT_LAMBDA2, DEFAULT_SIGMA2, DEFAULT_MU2)
        self.lambda2_spin, self.sigma2_spin, self.mu2_spin = self._last_spins
        main_layout.addWidget(gen2_group)

        # Условие завершения
        limit_group = self._create_limit_group()
        main_layout.addWidget(limit_group)

        main_layout.addStretch()

        # Кнопка запуска
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.run_button = QPushButton("Запустить моделирование")
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
        self.run_button.clicked.connect(self._start_simulation)
        button_layout.addWidget(self.run_button)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        central_widget.setLayout(main_layout)

    def _create_generator_group(self, title: str,
                                 default_lam: float, default_sigma: float,
                                 default_mu: float) -> QGroupBox:
        group = QGroupBox(title)
        group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        group.setStyleSheet(self._get_group_style())

        layout = QHBoxLayout()
        layout.setSpacing(15)

        # λ
        lam_label = QLabel("λ:")
        lam_label.setFont(QFont("Arial", FONT_SIZE_LABEL))
        layout.addWidget(lam_label)

        lam_spin = QDoubleSpinBox()
        lam_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        lam_spin.setRange(0.01, 100.0)
        lam_spin.setValue(default_lam)
        lam_spin.setSingleStep(0.1)
        lam_spin.setDecimals(2)
        layout.addWidget(lam_spin)

        # σ
        sigma_label = QLabel("σ:")
        sigma_label.setFont(QFont("Arial", FONT_SIZE_LABEL))
        layout.addWidget(sigma_label)

        sigma_spin = QDoubleSpinBox()
        sigma_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        sigma_spin.setRange(0.001, 100.0)
        sigma_spin.setValue(default_sigma)
        sigma_spin.setSingleStep(0.01)
        sigma_spin.setDecimals(3)
        layout.addWidget(sigma_spin)

        # μ
        mu_label = QLabel("μ:")
        mu_label.setFont(QFont("Arial", FONT_SIZE_LABEL))
        layout.addWidget(mu_label)

        mu_spin = QDoubleSpinBox()
        mu_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        mu_spin.setRange(0.01, 100.0)
        mu_spin.setValue(default_mu)
        mu_spin.setSingleStep(0.5)
        mu_spin.setDecimals(2)
        layout.addWidget(mu_spin)

        layout.addStretch()
        group.setLayout(layout)

        self._last_spins = (lam_spin, sigma_spin, mu_spin)
        return group

    def _create_limit_group(self) -> QGroupBox:
        group = QGroupBox("Условие завершения моделирования")
        group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        group.setStyleSheet(self._get_group_style())

        layout = QVBoxLayout()

        self.limit_group = QButtonGroup(self)

        # По числу обработанных
        served_layout = QHBoxLayout()
        self.radio_served = QRadioButton("По числу обработанных:")
        self.radio_served.setFont(QFont("Arial", FONT_SIZE_LABEL))
        self.radio_served.setChecked(True)
        self.limit_group.addButton(self.radio_served, 0)
        served_layout.addWidget(self.radio_served)

        self.served_spin = QSpinBox()
        self.served_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        self.served_spin.setRange(100, 100000)
        self.served_spin.setValue(DEFAULT_MAX_SERVED)
        self.served_spin.setSingleStep(1000)
        served_layout.addWidget(self.served_spin)
        served_layout.addStretch()
        layout.addLayout(served_layout)

        # По числу сгенерированных
        gen_layout = QHBoxLayout()
        self.radio_generated = QRadioButton("По числу сгенерированных (с дообслуживанием):")
        self.radio_generated.setFont(QFont("Arial", FONT_SIZE_LABEL))
        self.limit_group.addButton(self.radio_generated, 1)
        gen_layout.addWidget(self.radio_generated)

        self.generated_spin = QSpinBox()
        self.generated_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        self.generated_spin.setRange(100, 100000)
        self.generated_spin.setValue(DEFAULT_MAX_GENERATED)
        self.generated_spin.setSingleStep(1000)
        self.generated_spin.setEnabled(False)
        gen_layout.addWidget(self.generated_spin)
        gen_layout.addStretch()
        layout.addLayout(gen_layout)

        self.limit_group.idToggled.connect(self._on_limit_changed)

        group.setLayout(layout)
        return group

    def _on_limit_changed(self, id: int, checked: bool):
        if not checked:
            return
        self.served_spin.setEnabled(id == 0)
        self.generated_spin.setEnabled(id == 1)

    def _get_group_style(self) -> str:
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

    def _get_params(self) -> dict:
        limit_id = self.limit_group.checkedId()
        if limit_id == 0:
            limit_type = 'served'
            limit_value = self.served_spin.value()
        else:
            limit_type = 'generated'
            limit_value = self.generated_spin.value()

        params = {
            'lambda1': self.lambda1_spin.value(),
            'sigma1': self.sigma1_spin.value(),
            'lambda2': self.lambda2_spin.value(),
            'sigma2': self.sigma2_spin.value(),
            'mu1': self.mu1_spin.value(),
            'mu2': self.mu2_spin.value(),
            'limit_type': limit_type,
            'limit_value': limit_value
        }

        validate_params(params['lambda1'], params['sigma1'], 1)
        validate_params(params['lambda2'], params['sigma2'], 2)

        return params

    def _start_simulation(self):
        try:
            params = self._get_params()
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return

        self.run_button.setEnabled(False)
        self.run_button.setText("Моделирование...")

        self._worker = SimulationWorker(params)
        self._worker.finished.connect(self._on_simulation_finished)
        self._worker.error.connect(self._on_simulation_error)

        self._thread = threading.Thread(target=self._worker.run, daemon=True)
        self._thread.start()

    def _on_simulation_finished(self, results: dict, params: dict, plots: list):
        self.run_button.setEnabled(True)
        self.run_button.setText("Запустить моделирование")

        results_window = ResultsWindow(results, params, self)
        results_window.exec()

        if plots:
            self.plots_window = PlotsWindow(plots, self)
            self.plots_window.show()

    def _on_simulation_error(self, error_msg: str):
        self.run_button.setEnabled(True)
        self.run_button.setText("Запустить моделирование")
        QMessageBox.critical(self, "Ошибка", f"Ошибка моделирования:\n{error_msg}")
