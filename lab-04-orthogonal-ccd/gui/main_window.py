# -*- coding: utf-8 -*-

import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QDoubleSpinBox, QSpinBox,
                              QGroupBox, QMessageBox, QComboBox,
                              QScrollArea, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont

from constants import *
from regression import run_occd
from gui.results_window import ResultsWindow


class OCCDWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        try:
            p = self.params
            result = run_occd(
                p['factor_ranges'], p['sigma1'], p['sigma2'],
                p['replications'], p['limit_value'],
                p['response_key'], p['n0'],
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
        self.setWindowTitle("Лабораторная №4: ОЦКП на имитационной модели СМО")
        self.setFixedSize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

        central = QWidget()
        self.setCentralWidget(central)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(20, 8, 20, 8)

        # ── Заголовок ──
        title = QLabel("Ортогональный центральный композиционный план (ОЦКП)")
        title.setFont(QFont("Arial", FONT_SIZE_TITLE, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(
            "Одноканальная СМО  •  Относительные приоритеты  •  "
            "4 фактора: λ₁, μ₁, λ₂, μ₂  •  Модель 2-го порядка"
        )
        subtitle.setFont(QFont("Arial", FONT_SIZE_SUBTITLE))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #78909C;")
        layout.addWidget(subtitle)

        layout.addSpacing(4)

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

        # ── Настройки ОЦКП ──
        occd_group = self._create_occd_settings_group()
        layout.addWidget(occd_group)

        # ── Факторы ──
        factors_group = self._create_factors_group()
        layout.addWidget(factors_group)

        # ── Фиксированные параметры ──
        fixed_group = self._create_fixed_params_group()
        layout.addWidget(fixed_group)

        # ── Параметры моделирования ──
        sim_group = self._create_sim_params_group()
        layout.addWidget(sim_group)

        layout.addStretch()
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
        self._update_occd_info()

    # ── Группа настроек ОЦКП ─────────────────────────────────────

    def _create_occd_settings_group(self):
        group = QGroupBox("Параметры ОЦКП")
        group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        group.setStyleSheet(self._group_style())
        layout = QVBoxLayout()
        layout.setSpacing(8)

        row1 = QHBoxLayout()
        row1.setSpacing(20)

        core_label = QLabel("Ядро: ПФЭ 2⁴ = 16 опытов")
        core_label.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        core_label.setStyleSheet(f"color: {COLOR_BUTTON};")
        row1.addWidget(core_label)

        row1.addSpacing(30)

        star_label = QLabel("Звёздных точек: 2·4 = 8")
        star_label.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        star_label.setStyleSheet(f"color: {COLOR_BUTTON};")
        row1.addWidget(star_label)

        row1.addSpacing(30)

        n0_label = QLabel("Центральных точек (n₀):")
        n0_label.setFont(QFont("Arial", FONT_SIZE_LABEL))
        row1.addWidget(n0_label)

        self.n0_spin = QSpinBox()
        self.n0_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        self.n0_spin.setRange(1, 10)
        self.n0_spin.setValue(DEFAULT_N0)
        self.n0_spin.setFixedWidth(80)
        self.n0_spin.valueChanged.connect(self._update_occd_info)
        self.n0_spin.valueChanged.connect(self._update_button_text)
        row1.addWidget(self.n0_spin)

        row1.addStretch()
        layout.addLayout(row1)

        self.occd_info_label = QLabel()
        self.occd_info_label.setFont(QFont("Arial", FONT_SIZE_LABEL - 2))
        self.occd_info_label.setStyleSheet(f"color: {COLOR_SUCCESS};")
        layout.addWidget(self.occd_info_label)

        group.setLayout(layout)
        return group

    def _update_occd_info(self, *_):
        if not hasattr(self, 'occd_info_label') or not hasattr(self, 'n0_spin'):
            return
        from math import sqrt
        n_core = N_CORE
        n_star = 2 * N_FACTORS
        n0 = self.n0_spin.value()
        N = n_core + n_star + n0
        alpha_sq = 0.5 * (sqrt(n_core * N) - n_core)
        alpha = sqrt(alpha_sq)
        S = sqrt(n_core / N)
        self.occd_info_label.setText(
            f"Итого опытов: N = {N}    •    α = √{alpha_sq:.4f} ≈ {alpha:.4f}    •    S = √({n_core}/{N}) ≈ {S:.4f}"
        )

    def _update_button_text(self):
        if not hasattr(self, 'run_button') or not hasattr(self, 'n0_spin'):
            return
        N = N_CORE + 2 * N_FACTORS + self.n0_spin.value()
        self.run_button.setText(f"Провести ОЦКП ({N} опытов)")

    # ── Факторы ──────────────────────────────────────────────────

    def _create_factors_group(self):
        group = QGroupBox("Варьируемые факторы (4 фактора)")
        group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        group.setStyleSheet(self._group_style())

        layout = QVBoxLayout()
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(10)
        cols = [("Фактор", 200), ("Min", 100), ("Max", 100),
                ("Центр (x₀)", 100), ("Δ", 100), ("Звёзд. min", 100), ("Звёзд. max", 100)]
        for text, w in cols:
            lbl = QLabel(text)
            lbl.setFont(QFont("Arial", FONT_SIZE_LABEL - 2, QFont.Weight.Bold))
            lbl.setFixedWidth(w)
            lbl.setStyleSheet("color: #78909C;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.addWidget(lbl)
        header.addStretch()
        layout.addLayout(header)

        for factor in FACTORS:
            rng = DEFAULT_RANGES.get(factor['key'], (1.0, 2.0))
            row = self._create_factor_row(factor, rng[0], rng[1])
            layout.addLayout(row)

        # ρ-индикатор
        layout.addSpacing(4)
        rho_row = QHBoxLayout()
        rho_row.setSpacing(12)

        rho_label = QLabel("ρ в ядре:")
        rho_label.setFont(QFont("Arial", FONT_SIZE_LABEL))
        rho_row.addWidget(rho_label)

        self.rho_core_label = QLabel()
        self.rho_core_label.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        rho_row.addWidget(self.rho_core_label)

        rho_row.addSpacing(30)

        rho_label2 = QLabel("ρ в звёздных точках:")
        rho_label2.setFont(QFont("Arial", FONT_SIZE_LABEL))
        rho_row.addWidget(rho_label2)

        self.rho_star_label = QLabel()
        self.rho_star_label.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        rho_row.addWidget(self.rho_star_label)

        rho_row.addStretch()
        layout.addLayout(rho_row)

        group.setLayout(layout)
        return group

    def _create_factor_row(self, factor, default_min, default_max):
        row = QHBoxLayout()
        row.setSpacing(10)

        name = QLabel(f"{factor['label']}  —  {factor['desc']}")
        name.setFont(QFont("Arial", FONT_SIZE_LABEL))
        name.setFixedWidth(200)
        row.addWidget(name)

        min_spin = QDoubleSpinBox()
        min_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        min_spin.setRange(0.001, 100.0)
        min_spin.setValue(default_min)
        min_spin.setSingleStep(0.1)
        min_spin.setDecimals(3)
        min_spin.setFixedWidth(100)
        row.addWidget(min_spin)

        max_spin = QDoubleSpinBox()
        max_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        max_spin.setRange(0.001, 100.0)
        max_spin.setValue(default_max)
        max_spin.setSingleStep(0.1)
        max_spin.setDecimals(3)
        max_spin.setFixedWidth(100)
        row.addWidget(max_spin)

        center_label = QLabel()
        center_label.setFont(QFont("Arial", FONT_SIZE_INPUT))
        center_label.setFixedWidth(100)
        center_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_label.setStyleSheet(f"color: {COLOR_BUTTON};")
        row.addWidget(center_label)

        delta_label = QLabel()
        delta_label.setFont(QFont("Arial", FONT_SIZE_INPUT))
        delta_label.setFixedWidth(100)
        delta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        delta_label.setStyleSheet("color: #78909C;")
        row.addWidget(delta_label)

        star_min_label = QLabel()
        star_min_label.setFont(QFont("Arial", FONT_SIZE_INPUT))
        star_min_label.setFixedWidth(100)
        star_min_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        star_min_label.setStyleSheet("color: #AB47BC;")
        row.addWidget(star_min_label)

        star_max_label = QLabel()
        star_max_label.setFont(QFont("Arial", FONT_SIZE_INPUT))
        star_max_label.setFixedWidth(100)
        star_max_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        star_max_label.setStyleSheet("color: #AB47BC;")
        row.addWidget(star_max_label)

        def update(*_):
            from math import sqrt
            lo, hi = min_spin.value(), max_spin.value()
            center = (lo + hi) / 2
            delta = (hi - lo) / 2
            center_label.setText(f"{center:.3f}")
            delta_label.setText(f"{delta:.3f}")
            # Звёздные: с учётом текущего n0
            n0 = self.n0_spin.value() if hasattr(self, 'n0_spin') else 1
            N = N_CORE + 2 * N_FACTORS + n0
            alpha_sq = 0.5 * (sqrt(N_CORE * N) - N_CORE)
            alpha = sqrt(alpha_sq)
            star_min_label.setText(f"{center - alpha * delta:.3f}")
            star_max_label.setText(f"{center + alpha * delta:.3f}")
            self._update_rho_indicator()

        min_spin.valueChanged.connect(update)
        max_spin.valueChanged.connect(update)
        if hasattr(self, 'n0_spin'):
            self.n0_spin.valueChanged.connect(update)
        update()

        row.addStretch()
        self.factor_spins[factor['key']] = (min_spin, max_spin)
        return row

    def _update_rho_indicator(self, *_):
        if not hasattr(self, 'rho_core_label') or 'lambda1' not in self.factor_spins:
            return
        from math import sqrt
        lam1_min, lam1_max = self.factor_spins['lambda1'][0].value(), self.factor_spins['lambda1'][1].value()
        lam2_min, lam2_max = self.factor_spins['lambda2'][0].value(), self.factor_spins['lambda2'][1].value()
        mu1_min, mu1_max = self.factor_spins['mu1'][0].value(), self.factor_spins['mu1'][1].value()
        mu2_min, mu2_max = self.factor_spins['mu2'][0].value(), self.factor_spins['mu2'][1].value()

        if mu1_min <= 0 or mu2_min <= 0:
            self.rho_core_label.setText("μ_min ≤ 0!")
            self.rho_core_label.setStyleSheet(f"color: {COLOR_ERROR};")
            return

        # Худшая точка ядра: λ_max + μ_min
        rho_core_worst = lam1_max / mu1_min + lam2_max / mu2_min

        # Центр плана
        lam1_c = (lam1_min + lam1_max) / 2
        lam2_c = (lam2_min + lam2_max) / 2
        mu1_c = (mu1_min + mu1_max) / 2
        mu2_c = (mu2_min + mu2_max) / 2
        rho_center = lam1_c / mu1_c + lam2_c / mu2_c

        # Звёздные точки — нужно посчитать худшую
        n0 = self.n0_spin.value() if hasattr(self, 'n0_spin') else 1
        N = N_CORE + 2 * N_FACTORS + n0
        alpha = sqrt(0.5 * (sqrt(N_CORE * N) - N_CORE))

        lam1_d = (lam1_max - lam1_min) / 2
        lam2_d = (lam2_max - lam2_min) / 2
        mu1_d = (mu1_max - mu1_min) / 2
        mu2_d = (mu2_max - mu2_min) / 2

        # Звёздная точка с max λ₁: λ₁ = центр + α·Δ, остальные = центр
        rhos_star = [
            (lam1_c + alpha * lam1_d) / mu1_c + lam2_c / mu2_c,  # star λ₁+
            (lam1_c - alpha * lam1_d) / mu1_c + lam2_c / mu2_c,  # star λ₁-
            lam1_c / (mu1_c + alpha * mu1_d) + lam2_c / mu2_c,   # star μ₁+ (уменьшает ρ)
            lam1_c / (mu1_c - alpha * mu1_d) + lam2_c / mu2_c,   # star μ₁-
            lam1_c / mu1_c + (lam2_c + alpha * lam2_d) / mu2_c,  # star λ₂+
            lam1_c / mu1_c + (lam2_c - alpha * lam2_d) / mu2_c,  # star λ₂-
            lam1_c / mu1_c + lam2_c / (mu2_c + alpha * mu2_d),   # star μ₂+
            lam1_c / mu1_c + lam2_c / (mu2_c - alpha * mu2_d),   # star μ₂-
        ]
        rho_star_worst = max(rhos_star)

        # Отображение
        def colorize(rho, ok_range):
            lo, hi = ok_range
            if lo <= rho <= hi:
                return COLOR_SUCCESS
            return COLOR_ERROR

        self.rho_core_label.setText(
            f"worst = {rho_core_worst:.3f}  (центр ρ = {rho_center:.3f})")
        # В центре ρ должен быть >= MIN_RHO_NONLINEAR
        if rho_center < DEFAULT_MIN_RHO_NONLINEAR:
            self.rho_core_label.setStyleSheet(f"color: {COLOR_WARNING};")
        elif rho_core_worst >= 1.0:
            self.rho_core_label.setStyleSheet(f"color: {COLOR_ERROR};")
        else:
            self.rho_core_label.setStyleSheet(f"color: {COLOR_SUCCESS};")

        self.rho_star_label.setText(f"worst = {rho_star_worst:.3f}")
        if rho_star_worst > DEFAULT_MAX_RHO_STAR:
            self.rho_star_label.setStyleSheet(f"color: {COLOR_ERROR};")
        else:
            self.rho_star_label.setStyleSheet(f"color: {COLOR_SUCCESS};")

    # ── Фиксированные параметры ──────────────────────────────────

    def _create_fixed_params_group(self):
        group = QGroupBox("Фиксированные параметры (не варьируются)")
        group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        group.setStyleSheet(self._group_style())

        layout = QHBoxLayout()
        layout.setSpacing(16)

        lbl1 = QLabel("σ₁ (СКО поступления, тип 1):")
        lbl1.setFont(QFont("Arial", FONT_SIZE_LABEL))
        layout.addWidget(lbl1)

        self.sigma1_spin = QDoubleSpinBox()
        self.sigma1_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        self.sigma1_spin.setRange(0.001, 10.0)
        self.sigma1_spin.setValue(DEFAULT_SIGMA1)
        self.sigma1_spin.setSingleStep(0.01)
        self.sigma1_spin.setDecimals(3)
        self.sigma1_spin.setFixedWidth(90)
        layout.addWidget(self.sigma1_spin)

        layout.addSpacing(14)

        lbl2 = QLabel("σ₂ (СКО поступления, тип 2):")
        lbl2.setFont(QFont("Arial", FONT_SIZE_LABEL))
        layout.addWidget(lbl2)

        self.sigma2_spin = QDoubleSpinBox()
        self.sigma2_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        self.sigma2_spin.setRange(0.001, 10.0)
        self.sigma2_spin.setValue(DEFAULT_SIGMA2)
        self.sigma2_spin.setSingleStep(0.01)
        self.sigma2_spin.setDecimals(3)
        self.sigma2_spin.setFixedWidth(90)
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
        layout.setSpacing(16)

        lbl1 = QLabel("Обслужить заявок:")
        lbl1.setFont(QFont("Arial", FONT_SIZE_LABEL))
        layout.addWidget(lbl1)

        self.limit_spin = QSpinBox()
        self.limit_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        self.limit_spin.setRange(100, 100000)
        self.limit_spin.setValue(DEFAULT_LIMIT_VALUE)
        self.limit_spin.setSingleStep(1000)
        self.limit_spin.setFixedWidth(110)
        layout.addWidget(self.limit_spin)

        layout.addSpacing(14)

        lbl2 = QLabel("Повторов на точку:")
        lbl2.setFont(QFont("Arial", FONT_SIZE_LABEL))
        layout.addWidget(lbl2)

        self.repl_spin = QSpinBox()
        self.repl_spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
        self.repl_spin.setRange(1, 50)
        self.repl_spin.setValue(DEFAULT_REPLICATIONS)
        self.repl_spin.setFixedWidth(80)
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
                margin-top: 8px;
                padding: 8px;
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

    def _check_rho_limits(self, factor_ranges):
        from math import sqrt
        lam1_min, lam1_max = factor_ranges['lambda1']
        lam2_min, lam2_max = factor_ranges['lambda2']
        mu1_min, mu1_max = factor_ranges['mu1']
        mu2_min, mu2_max = factor_ranges['mu2']

        lam1_c = (lam1_min + lam1_max) / 2
        lam2_c = (lam2_min + lam2_max) / 2
        mu1_c = (mu1_min + mu1_max) / 2
        mu2_c = (mu2_min + mu2_max) / 2
        rho_center = lam1_c / mu1_c + lam2_c / mu2_c

        if rho_center < DEFAULT_MIN_RHO_NONLINEAR:
            raise ValueError(
                f"ρ в центре плана = {rho_center:.4f} < {DEFAULT_MIN_RHO_NONLINEAR}\n\n"
                f"Для ОЦКП нужна нелинейная область.\n"
                f"Увеличьте λ или уменьшите μ, чтобы ρ_центр ≥ {DEFAULT_MIN_RHO_NONLINEAR}."
            )

        # Звёздные точки
        n0 = self.n0_spin.value()
        N = N_CORE + 2 * N_FACTORS + n0
        alpha = sqrt(0.5 * (sqrt(N_CORE * N) - N_CORE))

        lam1_d = (lam1_max - lam1_min) / 2
        lam2_d = (lam2_max - lam2_min) / 2
        mu1_d = (mu1_max - mu1_min) / 2
        mu2_d = (mu2_max - mu2_min) / 2

        # Худшая звёздная точка
        rhos_star = [
            (lam1_c + alpha * lam1_d) / mu1_c + lam2_c / mu2_c,
            lam1_c / (mu1_c - alpha * mu1_d) + lam2_c / mu2_c,
            lam1_c / mu1_c + (lam2_c + alpha * lam2_d) / mu2_c,
            lam1_c / mu1_c + lam2_c / (mu2_c - alpha * mu2_d),
        ]
        rho_star_worst = max(rhos_star)

        if rho_star_worst > DEFAULT_MAX_RHO_STAR:
            raise ValueError(
                f"ρ в худшей звёздной точке = {rho_star_worst:.4f} > {DEFAULT_MAX_RHO_STAR}\n\n"
                f"Система переходит в зону перегрузки.\n"
                f"Уменьшите интервалы варьирования λ или μ."
            )

        # Проверить, что в звёздных не μ_min ≤ 0
        if mu1_c - alpha * mu1_d <= 0 or mu2_c - alpha * mu2_d <= 0:
            raise ValueError(
                "В звёздной точке μ становится ≤ 0. Уменьшите интервал варьирования μ."
            )

    def _start_experiment(self):
        try:
            factor_ranges = self._get_factor_ranges()
            self._check_rho_limits(factor_ranges)
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return

        params = {
            'factor_ranges': factor_ranges,
            'sigma1': self.sigma1_spin.value(),
            'sigma2': self.sigma2_spin.value(),
            'replications': self.repl_spin.value(),
            'limit_value': self.limit_spin.value(),
            'response_key': self.response_combo.currentData(),
            'n0': self.n0_spin.value(),
        }

        self.run_button.setEnabled(False)
        self.run_button.setText("Выполняется эксперимент...")

        self._worker = OCCDWorker(params)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._params = params

        self._thread = threading.Thread(target=self._worker.run, daemon=True)
        self._thread.start()

    def _on_finished(self, result):
        self.run_button.setEnabled(True)
        self._update_button_text()

        self._results_window = ResultsWindow(result, self._params, self)
        self._results_window.show()

    def _on_error(self, msg):
        self.run_button.setEnabled(True)
        self._update_button_text()
        QMessageBox.critical(self, "Ошибка", f"Ошибка эксперимента:\n{msg}")
