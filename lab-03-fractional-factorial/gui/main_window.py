# -*- coding: utf-8 -*-

import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QDoubleSpinBox, QSpinBox,
                              QGroupBox, QMessageBox, QComboBox, QCheckBox,
                              QLineEdit, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont

from constants import *
from regression import run_ffe, run_dfe, validate_generators
from gui.results_window import ResultsWindow


class DFEWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        try:
            p = self.params
            results = {}

            # ДФЭ
            dfe_result = run_dfe(
                p['factor_ranges'], p['sigma1'], p['sigma2'],
                p['replications'], p['limit_value'],
                p['generators_text'], p['fraction'], p['response_key'],
            )
            results['dfe'] = dfe_result

            # ПФЭ для сравнения
            if p.get('compare_ffe'):
                ffe_result = run_ffe(
                    p['factor_ranges'], p['sigma1'], p['sigma2'],
                    p['replications'], p['limit_value'], p['response_key'],
                )
                results['ffe'] = ffe_result

            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.factor_spins = {}
        self.init_ui()
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

    def init_ui(self):
        self.setWindowTitle("Лабораторная №3: ДФЭ 2^(4−p) на имитационной модели СМО")
        self.resize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

        central = QWidget()
        self.setCentralWidget(central)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(20, 6, 20, 10)

        # ── Заголовок (компактный) ──
        header = QLabel(
            "Дробный факторный эксперимент 2^(4−p)  —  "
            "Одноканальная СМО  •  Относительные приоритеты  •  "
            "4 фактора: λ₁, μ₁, λ₂, μ₂"
        )
        header.setFont(QFont("Arial", FONT_SIZE_SUBTITLE))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #78909C;")
        layout.addWidget(header)

        # ── Выходная переменная ──
        resp_layout = QHBoxLayout()
        resp_label = QLabel("Выходная переменная:")
        resp_label.setFont(QFont("Arial", FONT_SIZE_LABEL))
        resp_layout.addWidget(resp_label)

        self.response_combo = QComboBox()
        self.response_combo.setFont(QFont("Arial", FONT_SIZE_INPUT))
        self.response_combo.setMinimumWidth(300)
        for opt in RESPONSE_OPTIONS:
            self.response_combo.addItem(opt['label'], opt['key'])
        resp_layout.addWidget(self.response_combo)
        resp_layout.addStretch()
        layout.addLayout(resp_layout)

        # ── Настройки ДФЭ ──
        dfe_group = self._create_dfe_settings_group()
        layout.addWidget(dfe_group)

        # ── Факторы ──
        factors_group = self._create_factors_group()
        layout.addWidget(factors_group)

        # ── Фиксированные параметры ──
        fixed_group = self._create_fixed_params_group()
        layout.addWidget(fixed_group)

        # ── Параметры моделирования ──
        sim_group = self._create_sim_params_group()
        layout.addWidget(sim_group)

        # ── Кнопка запуска ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.run_button = QPushButton()
        self.run_button.setFont(QFont("Arial", FONT_SIZE_BUTTON, QFont.Weight.Bold))
        self.run_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_BUTTON_SUCCESS};
                color: white;
                border: none;
                padding: 10px 28px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_BUTTON_SUCCESS_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {COLOR_BUTTON_SECONDARY};
            }}
        """)
        self.run_button.clicked.connect(self._start_experiment)
        btn_layout.addWidget(self.run_button)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        content.setLayout(layout)
        scroll.setWidget(content)

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        central.setLayout(outer)

        self._update_button_text()

    # ── Группа настроек ДФЭ ──────────────────────────────────────

    def _create_dfe_settings_group(self):
        group = QGroupBox("Настройки дробного факторного эксперимента")
        group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        group.setStyleSheet(self._group_style())
        layout = QVBoxLayout()
        layout.setSpacing(6)

        # Строка 1: информация о дробности + сравнение
        row1 = QHBoxLayout()
        row1.setSpacing(14)

        frac_label = QLabel("Полуреплика 2^(4−1) = 8 опытов")
        frac_label.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        frac_label.setStyleSheet(f"color: {COLOR_BUTTON};")
        row1.addWidget(frac_label)

        row1.addSpacing(30)

        self.compare_check = QCheckBox("Сравнить с ПФЭ 2⁴ (16 опытов)")
        self.compare_check.setFont(QFont("Arial", FONT_SIZE_LABEL))
        self.compare_check.setChecked(True)
        self.compare_check.stateChanged.connect(self._update_button_text)
        row1.addWidget(self.compare_check)

        row1.addStretch()
        layout.addLayout(row1)

        # Строка 2: генератор
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        gen_label = QLabel("Генератор:")
        gen_label.setFont(QFont("Arial", FONT_SIZE_LABEL))
        row2.addWidget(gen_label)

        self.gen_edit = QLineEdit()
        self.gen_edit.setFont(QFont("Courier New", FONT_SIZE_INPUT))
        self.gen_edit.setMinimumWidth(300)
        self.gen_edit.setText(DEFAULT_GENERATOR)
        self.gen_edit.setPlaceholderText("Например: x4=x1*x2*x3")
        self.gen_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_WIDGET_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 6px 10px;
            }}
        """)
        row2.addWidget(self.gen_edit)

        self.gen_status = QLabel("")
        self.gen_status.setFont(QFont("Arial", FONT_SIZE_LABEL - 2))
        self.gen_status.setMinimumWidth(200)
        row2.addWidget(self.gen_status)

        row2.addStretch()
        layout.addLayout(row2)

        self.gen_edit.textChanged.connect(self._validate_gen_input)

        group.setLayout(layout)
        self._validate_gen_input()
        return group

    def _validate_gen_input(self, *_):
        text = self.gen_edit.text().strip()
        if not text:
            self.gen_status.setText("")
            return
        err = validate_generators(text, 4, 1)
        if err:
            self.gen_status.setText(f"Ошибка: {err}")
            self.gen_status.setStyleSheet(f"color: {COLOR_ERROR};")
        else:
            self.gen_status.setText("OK")
            self.gen_status.setStyleSheet(f"color: {COLOR_SUCCESS};")

    def _update_button_text(self):
        if not hasattr(self, 'run_button'):
            return
        text = "Провести ДФЭ (8 опытов)"
        if self.compare_check.isChecked():
            text += " + ПФЭ (16 опытов)"
        self.run_button.setText(text)

    # ── Факторы ──────────────────────────────────────────────────

    def _create_factors_group(self):
        group = QGroupBox("Варьируемые факторы (4 фактора)")
        group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        group.setStyleSheet(self._group_style())

        layout = QVBoxLayout()
        layout.setSpacing(4)

        # Заголовки
        header = QHBoxLayout()
        header.setSpacing(8)
        cols = [("Фактор", 260), ("Min", 130), ("Max", 130), ("Центр (x₀)", 130), ("Δ", 130)]
        for text, w in cols:
            lbl = QLabel(text)
            lbl.setFont(QFont("Arial", FONT_SIZE_LABEL - 2, QFont.Weight.Bold))
            lbl.setFixedWidth(w)
            lbl.setStyleSheet("color: #78909C;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.addWidget(lbl)
        header.addStretch()
        layout.addLayout(header)

        # Строки факторов
        for factor in FACTORS:
            rng = DEFAULT_RANGES.get(factor['key'], (1.0, 2.0))
            row = self._create_factor_row(factor, rng[0], rng[1])
            layout.addLayout(row)

        # ρ-индикатор
        rho_row = QHBoxLayout()
        rho_row.setSpacing(8)

        rho_label = QLabel("ρ_max (граница линейности):")
        rho_label.setFont(QFont("Arial", FONT_SIZE_LABEL))
        rho_row.addWidget(rho_label)

        self.rho_max_spin = QDoubleSpinBox()
        self.rho_max_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        self.rho_max_spin.setRange(0.1, 0.99)
        self.rho_max_spin.setValue(DEFAULT_MAX_RHO_LINEAR)
        self.rho_max_spin.setSingleStep(0.05)
        self.rho_max_spin.setDecimals(2)
        self.rho_max_spin.setFixedWidth(80)
        self.rho_max_spin.valueChanged.connect(self._update_rho_indicator)
        rho_row.addWidget(self.rho_max_spin)

        rho_row.addSpacing(16)

        self.rho_worst_label = QLabel()
        self.rho_worst_label.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        rho_row.addWidget(self.rho_worst_label)

        rho_row.addStretch()
        layout.addLayout(rho_row)

        group.setLayout(layout)
        return group

    def _create_factor_row(self, factor, default_min, default_max):
        row = QHBoxLayout()
        row.setSpacing(10)

        name = QLabel(f"{factor['label']}  —  {factor['desc']}")
        name.setFont(QFont("Arial", FONT_SIZE_LABEL))
        name.setFixedWidth(260)
        row.addWidget(name)

        min_spin = QDoubleSpinBox()
        min_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        min_spin.setRange(0.001, 100.0)
        min_spin.setValue(default_min)
        min_spin.setSingleStep(0.1)
        min_spin.setDecimals(3)
        min_spin.setFixedWidth(130)
        row.addWidget(min_spin)

        max_spin = QDoubleSpinBox()
        max_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        max_spin.setRange(0.001, 100.0)
        max_spin.setValue(default_max)
        max_spin.setSingleStep(0.1)
        max_spin.setDecimals(3)
        max_spin.setFixedWidth(130)
        row.addWidget(max_spin)

        center_label = QLabel()
        center_label.setFont(QFont("Arial", FONT_SIZE_INPUT))
        center_label.setFixedWidth(130)
        center_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_label.setStyleSheet(f"color: {COLOR_BUTTON};")
        row.addWidget(center_label)

        delta_label = QLabel()
        delta_label.setFont(QFont("Arial", FONT_SIZE_INPUT))
        delta_label.setFixedWidth(130)
        delta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        delta_label.setStyleSheet("color: #78909C;")
        row.addWidget(delta_label)

        def update(*_):
            lo, hi = min_spin.value(), max_spin.value()
            center_label.setText(f"{(lo + hi) / 2:.3f}")
            delta_label.setText(f"{(hi - lo) / 2:.3f}")
            self._update_rho_indicator()

        min_spin.valueChanged.connect(update)
        max_spin.valueChanged.connect(update)
        update()

        row.addStretch()
        self.factor_spins[factor['key']] = (min_spin, max_spin)
        return row

    def _update_rho_indicator(self, *_):
        if not hasattr(self, 'rho_worst_label') or 'lambda1' not in self.factor_spins:
            return
        lam1_max = self.factor_spins['lambda1'][1].value()
        lam2_max = self.factor_spins['lambda2'][1].value()
        mu1_min = self.factor_spins['mu1'][0].value()
        mu2_min = self.factor_spins['mu2'][0].value()

        if mu1_min <= 0 or mu2_min <= 0:
            self.rho_worst_label.setText("ρ_worst: μ_min ≤ 0!")
            self.rho_worst_label.setStyleSheet(f"color: {COLOR_ERROR};")
            return

        rho_worst = lam1_max / mu1_min + lam2_max / mu2_min
        rho_limit = self.rho_max_spin.value()

        if rho_worst <= rho_limit:
            self.rho_worst_label.setText(f"ρ_worst = {rho_worst:.4f} ≤ {rho_limit}")
            self.rho_worst_label.setStyleSheet(f"color: {COLOR_SUCCESS};")
        else:
            self.rho_worst_label.setText(
                f"ρ_worst = {rho_worst:.4f} > {rho_limit} — выход за линейную область!")
            self.rho_worst_label.setStyleSheet(f"color: {COLOR_ERROR};")

    def _check_rho_limit(self, factor_ranges):
        lam1_max = factor_ranges['lambda1'][1]
        lam2_max = factor_ranges['lambda2'][1]
        mu1_min = factor_ranges['mu1'][0]
        mu2_min = factor_ranges['mu2'][0]

        rho_worst = lam1_max / mu1_min + lam2_max / mu2_min
        rho_limit = self.rho_max_spin.value()

        if rho_worst > rho_limit:
            raise ValueError(
                f"Наихудшая загрузка ρ = {rho_worst:.4f} > {rho_limit}\n"
                f"(λ₁_max/μ₁_min + λ₂_max/μ₂_min = "
                f"{lam1_max:.3f}/{mu1_min:.3f} + {lam2_max:.3f}/{mu2_min:.3f})\n\n"
                f"Уменьшите интервалы варьирования λ или увеличьте μ,\n"
                f"чтобы все точки плана лежали в линейной области."
            )

    # ── Фиксированные параметры ──────────────────────────────────

    def _create_fixed_params_group(self):
        group = QGroupBox("Фиксированные параметры (не варьируются)")
        group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        group.setStyleSheet(self._group_style())

        layout = QHBoxLayout()
        layout.setSpacing(8)

        lbl1 = QLabel("σ₁  (СКО поступления, тип 1):")
        lbl1.setFont(QFont("Arial", FONT_SIZE_LABEL))
        layout.addWidget(lbl1)

        self.sigma1_spin = QDoubleSpinBox()
        self.sigma1_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        self.sigma1_spin.setRange(0.001, 10.0)
        self.sigma1_spin.setValue(DEFAULT_SIGMA1)
        self.sigma1_spin.setSingleStep(0.01)
        self.sigma1_spin.setDecimals(3)
        self.sigma1_spin.setFixedWidth(120)
        layout.addWidget(self.sigma1_spin)

        layout.addSpacing(6)

        lbl2 = QLabel("σ₂  (СКО поступления, тип 2):")
        lbl2.setFont(QFont("Arial", FONT_SIZE_LABEL))
        layout.addWidget(lbl2)

        self.sigma2_spin = QDoubleSpinBox()
        self.sigma2_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        self.sigma2_spin.setRange(0.001, 10.0)
        self.sigma2_spin.setValue(DEFAULT_SIGMA2)
        self.sigma2_spin.setSingleStep(0.01)
        self.sigma2_spin.setDecimals(3)
        self.sigma2_spin.setFixedWidth(120)
        layout.addWidget(self.sigma2_spin)

        layout.addStretch()
        group.setLayout(layout)
        return group

    # ── Параметры моделирования ──────────────────────────────────

    def _create_sim_params_group(self):
        group = QGroupBox("Параметры моделирования")
        group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        group.setStyleSheet(self._group_style())

        layout = QHBoxLayout()
        layout.setSpacing(8)

        lbl1 = QLabel("Обслужить заявок:")
        lbl1.setFont(QFont("Arial", FONT_SIZE_LABEL))
        layout.addWidget(lbl1)

        self.limit_spin = QSpinBox()
        self.limit_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        self.limit_spin.setRange(100, 100000)
        self.limit_spin.setValue(DEFAULT_LIMIT_VALUE)
        self.limit_spin.setSingleStep(1000)
        self.limit_spin.setFixedWidth(140)
        layout.addWidget(self.limit_spin)

        layout.addSpacing(6)

        lbl2 = QLabel("Повторов на точку:")
        lbl2.setFont(QFont("Arial", FONT_SIZE_LABEL))
        layout.addWidget(lbl2)

        self.repl_spin = QSpinBox()
        self.repl_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        self.repl_spin.setRange(1, 50)
        self.repl_spin.setValue(DEFAULT_REPLICATIONS)
        self.repl_spin.setFixedWidth(100)
        layout.addWidget(self.repl_spin)

        layout.addStretch()
        group.setLayout(layout)
        return group

    # ── Стили ─────────────────────────────────────────────────────

    def _group_style(self):
        return f"""
            QGroupBox {{
                background-color: {COLOR_WIDGET_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                margin-top: 14px;
                padding: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
            }}
        """

    # ── Запуск эксперимента ───────────────────────────────────────

    def _get_factor_ranges(self):
        ranges = {}
        for factor in FACTORS:
            min_spin, max_spin = self.factor_spins[factor['key']]
            lo, hi = min_spin.value(), max_spin.value()
            if lo >= hi:
                raise ValueError(f"Фактор {factor['label']}: min ({lo:.3f}) >= max ({hi:.3f})")
            if lo <= 0:
                raise ValueError(f"Фактор {factor['label']}: min ({lo:.3f}) должен быть > 0")
            ranges[factor['key']] = (lo, hi)
        return ranges

    def _start_experiment(self):
        # Валидация
        try:
            factor_ranges = self._get_factor_ranges()
            self._check_rho_limit(factor_ranges)
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return

        gen_text = self.gen_edit.text().strip()

        err = validate_generators(gen_text, 4, 1)
        if err:
            QMessageBox.critical(self, "Ошибка генератора", err)
            return

        params = {
            'factor_ranges': factor_ranges,
            'sigma1': self.sigma1_spin.value(),
            'sigma2': self.sigma2_spin.value(),
            'replications': self.repl_spin.value(),
            'limit_value': self.limit_spin.value(),
            'generators_text': gen_text,
            'fraction': FRACTION,
            'response_key': self.response_combo.currentData(),
            'compare_ffe': self.compare_check.isChecked(),
        }

        self.run_button.setEnabled(False)
        self.run_button.setText("Выполняется эксперимент...")

        self._worker = DFEWorker(params)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._params = params

        self._thread = threading.Thread(target=self._worker.run, daemon=True)
        self._thread.start()

    def _on_finished(self, results):
        self.run_button.setEnabled(True)
        self._update_button_text()

        self._results_window = ResultsWindow(results, self._params, self)
        self._results_window.show()

    def _on_error(self, msg):
        self.run_button.setEnabled(True)
        self._update_button_text()
        QMessageBox.critical(self, "Ошибка", f"Ошибка эксперимента:\n{msg}")
