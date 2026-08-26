# -*- coding: utf-8 -*-

import threading

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                              QHeaderView, QGroupBox, QTabWidget, QTextEdit,
                              QDoubleSpinBox, QScrollArea, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from constants import *
from regression import (validate_at_point, coded_to_natural, effect_label,
                        feature_pretty_label, sort_features, FACTORS)


class ResultsWindow(QMainWindow):
    _val_text_ready = pyqtSignal(str)
    _val_done = pyqtSignal()

    def __init__(self, result: dict, params: dict, parent=None):
        super().__init__(parent)
        self.result = result
        self.params = params
        self.setWindowTitle("Результаты ОЦКП")
        self.setMinimumSize(RESULTS_WINDOW_WIDTH, RESULTS_WINDOW_HEIGHT)
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 8, 14, 8)

        tabs = QTabWidget()
        tabs.setFont(QFont("Arial", FONT_SIZE_LABEL))

        tabs.addTab(self._create_equations_tab(), "Уравнения")
        tabs.addTab(self._create_coefficients_tab(), "Коэффициенты")
        tabs.addTab(self._create_experiments_tab(), "Таблица экспериментов")
        tabs.addTab(self._create_validation_tab(), "Проверка в точке")

        layout.addWidget(tabs)
        central.setLayout(layout)

    # ── Вкладка 1: Уравнения ─────────────────────────────────────

    def _create_equations_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(6)

        # Сводка
        summary_group = QGroupBox("Сводка эксперимента")
        summary_group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        summary_group.setStyleSheet(self._group_style())
        summary_layout = QGridLayout()

        r = self.result
        summary_data = [
            ("Опытов всего", f"{r['N']}"),
            ("Ядро ПФЭ 2⁴", f"{r['n_core']}"),
            ("Звёздные", f"{r['n_star']}"),
            ("Центральные (n₀)", f"{r['n0']}"),
            ("Звёздное плечо α", f"{r['alpha']:.6f}"),
            ("S = √(n_ядро/N)", f"{r['S']:.6f}"),
            ("Ср. отн. ошибка", f"{r['avg_rel_err']:.2f}%"),
        ]

        for i, (label, value) in enumerate(summary_data):
            col = i % 4
            row = i // 4
            lbl = QLabel(label)
            lbl.setFont(QFont("Arial", FONT_SIZE_LABEL - 2))
            lbl.setStyleSheet("color: #78909C;")
            val = QLabel(value)
            val.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
            summary_layout.addWidget(lbl, row * 2, col)
            summary_layout.addWidget(val, row * 2 + 1, col)

        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Уравнения
        layout.addWidget(self._equation_box(
            "Нелинейная модель с центрированными квадратами (zⱼ² − S)",
            r['eq_centered'],
            subtitle="Именно в этой форме матрица ортогональна — коэффициенты вычисляются по формулам МНК."))

        layout.addWidget(self._equation_box(
            f"Нелинейная модель — окончательное уравнение (S = {r['S']:.4f} подставлено, скобки раскрыты)",
            r['eq_expanded'],
            subtitle="Стандартная форма: здесь b₀′ = b₀ − S·Σbⱼⱼ. Квадраты факторов — в обычном виде."))

        layout.addWidget(self._equation_box(
            "Нелинейная модель в натуральных переменных",
            r['eq_natural'],
            subtitle="После подстановки zⱼ = (Xⱼ − cⱼ)/dⱼ в окончательное уравнение."))

        layout.addStretch()
        widget.setLayout(layout)
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        return scroll

    def _equation_box(self, title, equation, subtitle=None):
        group = QGroupBox(title)
        group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        group.setStyleSheet(self._group_style())
        gl = QVBoxLayout()

        if subtitle:
            sub = QLabel(subtitle)
            sub.setFont(QFont("Arial", FONT_SIZE_LABEL - 3))
            sub.setStyleSheet("color: #78909C;")
            sub.setWordWrap(True)
            gl.addWidget(sub)

        eq_label = QLabel(equation)
        eq_label.setFont(QFont("Courier New", FONT_SIZE_EQUATION))
        eq_label.setWordWrap(True)
        eq_label.setStyleSheet(f"""
            background-color: {COLOR_SECTION_BG};
            padding: 10px;
            border: 1px solid {COLOR_BORDER};
            border-radius: 4px;
        """)
        eq_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        gl.addWidget(eq_label)

        group.setLayout(gl)
        return group

    # ── Вкладка 2: Коэффициенты ──────────────────────────────────

    def _create_coefficients_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(8)

        r = self.result
        coeffs = r['coeffs']
        expanded = r['expanded_coeffs']
        denominators = r['denominators']

        sorted_features = sort_features(coeffs.keys())

        table = QTableWidget(len(sorted_features), 4)
        table.setFont(QFont("Arial", FONT_SIZE_TABLE))
        table.setHorizontalHeaderLabels([
            "Коэффициент",
            "Значение (центрированная форма)",
            "Значение (после раскрытия скобок)",
            "Знаменатель Σφ²",
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        for i, f in enumerate(sorted_features):
            # Метка
            table.setItem(i, 0, QTableWidgetItem(feature_pretty_label(f)))

            # Центрированное значение
            c_val = coeffs[f]
            table.setItem(i, 1, QTableWidgetItem(f"{c_val:.6f}"))

            # Раскрытое значение
            e_val = expanded.get(f, 0.0)
            if f == ():
                # b0 отличается
                item = QTableWidgetItem(f"{e_val:.6f}  (b₀ − S·Σbⱼⱼ)")
                item.setForeground(QColor("#FF9800"))
                table.setItem(i, 2, item)
            else:
                # Остальные не меняются
                table.setItem(i, 2, QTableWidgetItem(f"{e_val:.6f}"))

            # Знаменатель
            den = denominators.get(f, 0.0)
            den_explanation = self._denominator_explanation(f, r)
            table.setItem(i, 3, QTableWidgetItem(f"{den:.4f}  {den_explanation}"))

        table.resizeRowsToContents()

        layout.addWidget(table)
        widget.setLayout(layout)
        return widget

    def _denominator_explanation(self, feature, r):
        """Пояснение, из какой формулы получается знаменатель."""
        if not feature:
            return f"(= N)"
        if feature[0] == 'sq':
            return f"(≈ 2α⁴ = {2 * r['alpha']**4:.4f})"
        if len(feature) == 1:
            return f"(= n_ядро + 2α² = {r['n_core']} + {2 * r['alpha']**2:.2f})"
        if len(feature) == 2:
            return f"(= n_ядро = {r['n_core']})"
        return ""

    # ── Вкладка 3: Таблица экспериментов ─────────────────────────

    def _create_experiments_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(6)

        r = self.result
        details = r['run_details']

        table = QTableWidget(len(details), 11)
        table.setFont(QFont("Arial", FONT_SIZE_TABLE))
        table.setHorizontalHeaderLabels([
            "№", "Тип",
            "z₁", "z₂", "z₃", "z₄",
            "λ₁ нат", "μ₁ нат", "λ₂ нат", "μ₂ нат",
            "y",
        ])

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        factor_names = r['factor_names']

        for i, d in enumerate(details):
            table.setItem(i, 0, QTableWidgetItem(str(d['run'])))

            type_item = QTableWidgetItem(d['type'])
            if d['type'] == 'звёзд.':
                type_item.setForeground(QColor("#AB47BC"))
            elif d['type'] == 'центр':
                type_item.setForeground(QColor("#2196F3"))
            table.setItem(i, 1, type_item)

            for j, v in enumerate(d['coded']):
                table.setItem(i, 2 + j, QTableWidgetItem(f"{v:.4f}"))

            for j, key in enumerate(factor_names):
                table.setItem(i, 6 + j, QTableWidgetItem(f"{d['natural'][key]:.4f}"))

            table.setItem(i, 10, QTableWidgetItem(f"{d['y_exp']:.6f}"))

        table.resizeRowsToContents()
        layout.addWidget(table)
        widget.setLayout(layout)
        return widget

    # ── Вкладка 4: Проверка в точке ─────────────────────────────

    def _create_validation_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(8)

        input_group = QGroupBox("Нормированные координаты точки (от −1 до +1)")
        input_group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        input_group.setStyleSheet(self._group_style())
        ig_layout = QVBoxLayout()

        self.val_spins = []
        for i, f in enumerate(FACTORS):
            row = QHBoxLayout()
            lbl = QLabel(f"z{i+1} ({f['label']}):")
            lbl.setFont(QFont("Arial", FONT_SIZE_LABEL))
            lbl.setFixedWidth(120)
            row.addWidget(lbl)

            spin = QDoubleSpinBox()
            spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
            spin.setRange(-3.0, 3.0)
            spin.setValue(DEFAULT_VALIDATION_POINT[i])
            spin.setSingleStep(0.1)
            spin.setDecimals(3)
            spin.setFixedWidth(120)
            row.addWidget(spin)

            row.addStretch()
            ig_layout.addLayout(row)
            self.val_spins.append(spin)

        btn_row = QHBoxLayout()
        self.val_button = QPushButton("Проверить")
        self.val_button.setFont(QFont("Arial", FONT_SIZE_BUTTON, QFont.Weight.Bold))
        self.val_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_BUTTON};
                color: white;
                border: none;
                padding: 8px 22px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_BUTTON_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {COLOR_BUTTON_SECONDARY};
            }}
        """)
        self.val_button.clicked.connect(self._run_validation)
        btn_row.addWidget(self.val_button)
        btn_row.addStretch()
        ig_layout.addLayout(btn_row)

        input_group.setLayout(ig_layout)
        layout.addWidget(input_group)

        self.val_output = QTextEdit()
        self.val_output.setFont(QFont("Courier New", FONT_SIZE_EQUATION))
        self.val_output.setReadOnly(True)
        self.val_output.setMinimumHeight(300)
        self.val_output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_WIDGET_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 10px;
            }}
        """)
        self._val_text_ready.connect(self.val_output.setText)
        self._val_done.connect(lambda: self.val_button.setEnabled(True))
        self._val_done.connect(lambda: self.val_button.setText("Проверить"))
        layout.addWidget(self.val_output)

        widget.setLayout(layout)
        return widget

    def _run_validation(self):
        coded_point = [s.value() for s in self.val_spins]

        self.val_button.setEnabled(False)
        self.val_button.setText("Выполняется симуляция...")

        def worker():
            try:
                lines = []
                alpha = self.result['alpha']
                is_core = all(abs(abs(v) - 1.0) < 1e-9 for v in coded_point)
                is_center = all(abs(v) < 1e-9 for v in coded_point)
                near_alpha = any(abs(abs(v) - alpha) < 1e-9 for v in coded_point)

                if is_core or is_center or near_alpha:
                    lines.append("⚠ Внимание: выбранная точка может быть точкой плана.")
                    lines.append("  Для честной валидации выберите точку, не совпадающую с планом.")
                    lines.append("")

                extrapolation = any(abs(v) > alpha + 1e-6 for v in coded_point)
                if extrapolation:
                    lines.append(f"⚠ ВНИМАНИЕ: точка за пределами |z| = α = {alpha:.4f} — экстраполяция!")
                    lines.append("")

                nat = coded_to_natural(coded_point, self.result['factor_names'],
                                       self.result['centers'], self.result['deltas'])
                lines.append("Натуральные значения:")
                for key in self.result['factor_names']:
                    f = next(f for f in FACTORS if f['key'] == key)
                    lines.append(f"  {f['label']} = {nat[key]:.4f}")
                lines.append("")

                v = validate_at_point(
                    coded_point, self.result,
                    self.params['sigma1'], self.params['sigma2'],
                    self.params['replications'], self.params['limit_value'],
                    self.params['response_key'],
                )
                lines.append("═" * 60)
                lines.append(f"  y (моделирование):              {v['y_real']:.6f}")
                lines.append(f"  ŷ (центрир. модель):            {v['y_pred']:.6f}")
                lines.append(f"  ŷ (раскрытая модель):           {v['y_pred_expanded']:.6f}")
                lines.append(f"  ŷ (натуральная модель):         {v['y_pred_natural']:.6f}")
                lines.append("")
                lines.append(f"  |Δ| = {v['err']:.6f}    относительная ошибка = {v['rel_err']:.2f}%")
                lines.append("")
                lines.append("Все три формы уравнения дают одно и то же значение —")
                lines.append("они математически эквивалентны.")

                self._val_text_ready.emit('\n'.join(lines))
            except Exception as e:
                self._val_text_ready.emit(f"Ошибка: {e}")
            finally:
                self._val_done.emit()

        self._val_thread = threading.Thread(target=worker, daemon=True)
        self._val_thread.start()

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
                left: 12px;
                padding: 0 6px;
            }}
        """
