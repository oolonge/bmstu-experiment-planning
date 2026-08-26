# -*- coding: utf-8 -*-

import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                              QGroupBox, QHeaderView, QScrollArea, QTabWidget,
                              QDoubleSpinBox, QTextEdit, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from constants import *
from regression import (validate_at_point, effect_label, run_ffe,
                        predict_from_coefficients, coded_to_natural)


class ResultsWindow(QMainWindow):
    _val_text_ready = pyqtSignal(str)
    _val_done = pyqtSignal()

    def __init__(self, results: dict, params: dict, parent=None):
        super().__init__(parent)
        self.results = results
        self.params = params
        self.dfe = results.get('dfe')
        self.ffe = results.get('ffe')
        self.init_ui()
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

    def init_ui(self):
        self.setWindowTitle("Результаты ДФЭ")
        self.setFixedSize(RESULTS_WINDOW_WIDTH, RESULTS_WINDOW_HEIGHT)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout()
        outer.setContentsMargins(8, 6, 8, 6)

        tabs = QTabWidget()
        tabs.setFont(QFont("Arial", FONT_SIZE_TABLE_HEADER))

        tabs.addTab(self._create_equations_tab(), "Уравнения")
        tabs.addTab(self._create_coefficients_tab(), "Коэффициенты")
        tabs.addTab(self._create_experiments_tab(), "Таблица экспериментов")
        tabs.addTab(self._create_aliasing_tab(), "Схема смешивания")
        tabs.addTab(self._create_validation_tab(), "Проверка в точке")

        outer.addWidget(tabs)
        central.setLayout(outer)

    # ── Вкладка 1: Уравнения ─────────────────────────────────────

    def _create_equations_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(6)

        for label_prefix, result in self._iter_results():
            # Сводка — одна строка
            summary_text = (
                f"{label_prefix}:  "
                f"Экспериментов: {result['n_runs']}   |   "
                f"Ср. отн. ошибка (лин.): {result['avg_rel_err_linear']:.2f}%   |   "
                f"Ср. отн. ошибка (нелин.): {result['avg_rel_err_nonlinear']:.2f}%"
            )
            summary_lbl = QLabel(summary_text)
            summary_lbl.setFont(QFont("Arial", FONT_SIZE_TABLE, QFont.Weight.Bold))
            summary_lbl.setStyleSheet(
                f"background-color: {COLOR_WIDGET_BG}; "
                f"border: 1px solid {COLOR_BORDER}; "
                f"border-radius: 4px; padding: 6px 10px;"
            )
            layout.addWidget(summary_lbl)

            # Уравнения
            for title, eq in [
                ("Линейная (нормированные)", result['eq_lin_norm']),
                ("Линейная (натуральные)", result['eq_lin_nat']),
                ("Нелинейная (нормированные)", result['eq_full_norm']),
                ("Нелинейная (натуральные)", result['eq_full_nat']),
            ]:
                g = QGroupBox(f"{label_prefix}: {title}")
                g.setFont(QFont("Arial", FONT_SIZE_TABLE, QFont.Weight.Bold))
                g.setStyleSheet(self._group_style())
                gl = QVBoxLayout()
                eq_lbl = QLabel(eq)
                eq_lbl.setFont(QFont("Courier New", FONT_SIZE_EQUATION))
                eq_lbl.setWordWrap(True)
                eq_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                gl.addWidget(eq_lbl)
                g.setLayout(gl)
                layout.addWidget(g)

        layout.addStretch()
        widget.setLayout(layout)

        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        return scroll

    # ── Вкладка 2: Коэффициенты ──────────────────────────────────

    def _create_coefficients_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(6)

        if self.ffe and self.dfe:
            layout.addWidget(self._coeff_comparison_table(
                "Линейные коэффициенты",
                self.ffe['linear_coeffs'], self.dfe['linear_coeffs'],
                max_effect_len=1))
            layout.addWidget(self._coeff_comparison_table(
                "Все коэффициенты (с взаимодействиями)",
                self.ffe['full_coeffs'], self.dfe['full_coeffs']))
        else:
            result = self.dfe or self.ffe
            layout.addWidget(self._coeff_single_table(
                "Линейные коэффициенты", result['linear_coeffs'], result,
                max_effect_len=1))
            layout.addWidget(self._coeff_single_table(
                "Все коэффициенты", result['full_coeffs'], result))

        layout.addStretch()
        widget.setLayout(layout)
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        return scroll

    def _coeff_single_table(self, title, coeffs, result=None, max_effect_len=None):
        group = QGroupBox(title)
        group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        group.setStyleSheet(self._group_style())
        gl = QVBoxLayout()

        full_coeffs = result.get('full_coeffs', coeffs) if result else coeffs
        alias_map = result.get('alias_map', {}) if result else {}
        if max_effect_len is not None:
            alias_map = {k: v for k, v in alias_map.items() if len(k) <= max_effect_len}

        all_keys = sorted(set(coeffs.keys()) | set(alias_map.keys()),
                          key=lambda e: (len(e), e))

        table = QTableWidget(len(all_keys), 2)
        table.setFont(QFont("Arial", FONT_SIZE_TABLE))
        table.setHorizontalHeaderLabels(["Коэффициент", "Значение"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setDefaultSectionSize(22)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        for i, key in enumerate(all_keys):
            label = "b₀" if not key else f"b({effect_label(key)})"
            table.setItem(i, 0, QTableWidgetItem(label))

            if key in coeffs:
                table.setItem(i, 1, QTableWidgetItem(f"{coeffs[key]:.6f}"))
            elif key in alias_map:
                alias_key = alias_map[key]
                alias_val = full_coeffs.get(alias_key, 0.0)
                alias_name = effect_label(alias_key)
                item = QTableWidgetItem(
                    f"{alias_val:.6f}  (совп. с {alias_name})")
                item.setForeground(QColor("#FF9800"))
                table.setItem(i, 1, item)
            else:
                item = QTableWidgetItem("—")
                item.setForeground(QColor("#BDBDBD"))
                table.setItem(i, 1, item)

        table.setMaximumHeight(min(40 + len(all_keys) * 32, 400))
        gl.addWidget(table)
        group.setLayout(gl)
        return group

    def _coeff_comparison_table(self, title, ffe_coeffs, dfe_coeffs,
                               max_effect_len=None):
        group = QGroupBox(title)
        group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        group.setStyleSheet(self._group_style())
        gl = QVBoxLayout()

        alias_map = self.dfe.get('alias_map', {}) if self.dfe else {}
        dfe_full = self.dfe.get('full_coeffs', dfe_coeffs) if self.dfe else dfe_coeffs
        if max_effect_len is not None:
            alias_map = {k: v for k, v in alias_map.items() if len(k) <= max_effect_len}

        all_keys = sorted(
            set(ffe_coeffs.keys()) | set(dfe_coeffs.keys()) | set(alias_map.keys()),
            key=lambda e: (len(e), e))

        table = QTableWidget(len(all_keys), 3)
        table.setFont(QFont("Arial", FONT_SIZE_TABLE))
        table.setHorizontalHeaderLabels(["Коэффициент", "ПФЭ", "ДФЭ"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setDefaultSectionSize(22)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        for i, key in enumerate(all_keys):
            label = "b₀" if not key else f"b({effect_label(key)})"
            table.setItem(i, 0, QTableWidgetItem(label))

            if key in ffe_coeffs:
                table.setItem(i, 1, QTableWidgetItem(f"{ffe_coeffs[key]:.6f}"))
            else:
                item = QTableWidgetItem("—")
                item.setForeground(QColor("#BDBDBD"))
                table.setItem(i, 1, item)

            if key in dfe_coeffs:
                table.setItem(i, 2, QTableWidgetItem(f"{dfe_coeffs[key]:.6f}"))
            elif key in alias_map:
                alias_key = alias_map[key]
                alias_val = dfe_full.get(alias_key, 0.0)
                alias_name = effect_label(alias_key)
                item = QTableWidgetItem(
                    f"{alias_val:.6f}  (совп. с {alias_name})")
                item.setForeground(QColor("#FF9800"))
                table.setItem(i, 2, item)
            else:
                item = QTableWidgetItem("—")
                item.setForeground(QColor("#BDBDBD"))
                table.setItem(i, 2, item)

        table.setMaximumHeight(min(40 + len(all_keys) * 32, 500))
        gl.addWidget(table)
        group.setLayout(gl)
        return group

    # ── Вкладка 3: Таблица экспериментов ─────────────────────────

    def _create_experiments_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(6)

        for label_prefix, result in self._iter_results():
            group = QGroupBox(f"{label_prefix} — Результаты экспериментов")
            group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
            group.setStyleSheet(self._group_style())
            gl = QVBoxLayout()

            details = result['run_details']
            factor_names = result['factor_names']
            n_f = len(factor_names)

            headers = (["№"]
                       + [f"x{FACTOR_KEY_TO_INDEX[k] + 1}" for k in factor_names]
                       + [next(f['label'] for f in FACTORS if f['key'] == k) for k in factor_names]
                       + ["y_эксп", "ŷ_лин", "ŷ_нелин",
                          "|Δ| лин", "|Δ| нелин", "% лин", "% нелин"])

            table = QTableWidget(len(details), len(headers))
            table.setFont(QFont("Arial", FONT_SIZE_TABLE))
            table.setHorizontalHeaderLabels(headers)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            table.verticalHeader().setDefaultSectionSize(22)
            table.verticalHeader().setVisible(False)
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table.setAlternatingRowColors(True)

            for i, d in enumerate(details):
                col = 0
                table.setItem(i, col, QTableWidgetItem(str(d['run'])))
                col += 1

                for v in d['coded']:
                    item = QTableWidgetItem(f"{v:+d}")
                    item.setForeground(QColor("#2196F3") if v == -1 else QColor("#F44336"))
                    table.setItem(i, col, item)
                    col += 1

                nat = d['natural']
                for k in factor_names:
                    table.setItem(i, col, QTableWidgetItem(f"{nat[k]:.4f}"))
                    col += 1

                table.setItem(i, col, QTableWidgetItem(f"{d['y_exp']:.6f}"))
                col += 1
                table.setItem(i, col, QTableWidgetItem(f"{d['y_linear']:.6f}"))
                col += 1
                table.setItem(i, col, QTableWidgetItem(f"{d['y_nonlinear']:.6f}"))
                col += 1
                table.setItem(i, col, QTableWidgetItem(f"{d['err_linear']:.6f}"))
                col += 1
                table.setItem(i, col, QTableWidgetItem(f"{d['err_nonlinear']:.6f}"))
                col += 1
                table.setItem(i, col, QTableWidgetItem(f"{d['rel_err_linear']:.2f}%"))
                col += 1
                table.setItem(i, col, QTableWidgetItem(f"{d['rel_err_nonlinear']:.2f}%"))

            # Строка средних ошибок
            avg_row = QHBoxLayout()
            avg_row.setSpacing(20)
            avg_lbl = QLabel(
                f"Средние ошибки — "
                f"лин.: {result['avg_err_linear']:.6f} ({result['avg_rel_err_linear']:.2f}%), "
                f"нелин.: {result['avg_err_nonlinear']:.6f} ({result['avg_rel_err_nonlinear']:.2f}%)"
            )
            avg_lbl.setFont(QFont("Arial", FONT_SIZE_TABLE, QFont.Weight.Bold))
            avg_lbl.setStyleSheet(f"color: {COLOR_BUTTON};")

            gl.addWidget(table)
            gl.addWidget(avg_lbl)
            group.setLayout(gl)
            layout.addWidget(group)

        widget.setLayout(layout)
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        return scroll

    # ── Вкладка 4: Схема смешивания ──────────────────────────────

    def _create_aliasing_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(6)

        if self.dfe and 'aliasing_str' in self.dfe:
            group = QGroupBox("Схема смешивания (aliasing)")
            group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
            group.setStyleSheet(self._group_style())
            gl = QVBoxLayout()

            text = QTextEdit()
            text.setFont(QFont("Courier New", FONT_SIZE_EQUATION))
            text.setReadOnly(True)
            text.setText(self.dfe['aliasing_str'])
            text.setMinimumHeight(300)
            gl.addWidget(text)

            group.setLayout(gl)
            layout.addWidget(group)

            # Пояснение
            note = QLabel(
                "Определяющее соотношение I = ... показывает, какие эффекты неразличимы.\n"
                "Чем выше разрешающая способность (III < IV < V), тем лучше:\n"
                "  III — главные эффекты смешаны с парными взаимодействиями\n"
                "  IV  — главные эффекты смешаны только с тройными взаимодействиями\n"
                "  V   — главные эффекты и парные взаимодействия не смешаны"
            )
            note.setFont(QFont("Arial", FONT_SIZE_TABLE))
            note.setStyleSheet("color: #78909C;")
            layout.addWidget(note)
        else:
            lbl = QLabel("Схема смешивания доступна только для ДФЭ.")
            lbl.setFont(QFont("Arial", FONT_SIZE_LABEL))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    # ── Вкладка 5: Проверка в произвольной точке ─────────────────

    def _create_validation_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(6)

        # Ввод координат
        input_group = QGroupBox("Нормированные координаты точки (от −1 до +1)")
        input_group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        input_group.setStyleSheet(self._group_style())
        ig_layout = QVBoxLayout()
        ig_layout.setSpacing(10)

        self.val_spins = []
        factor_names = (self.dfe or self.ffe)['factor_names']

        for i, key in enumerate(factor_names):
            row = QHBoxLayout()
            row.setSpacing(12)

            f = next(f for f in FACTORS if f['key'] == key)
            lbl = QLabel(f"z{i + 1} ({f['label']}):")
            lbl.setFont(QFont("Arial", FONT_SIZE_LABEL))
            lbl.setFixedWidth(200)
            row.addWidget(lbl)

            spin = QDoubleSpinBox()
            spin.setFont(QFont("Arial", FONT_SIZE_INPUT))
            spin.setRange(-2.0, 2.0)
            spin.setValue(0.0)
            spin.setSingleStep(0.1)
            spin.setDecimals(3)
            spin.setFixedWidth(150)
            row.addWidget(spin)

            self.val_spins.append(spin)
            row.addStretch()
            ig_layout.addLayout(row)

        # Кнопка
        btn_row = QHBoxLayout()
        self.val_button = QPushButton("Проверить")
        self.val_button.setFont(QFont("Arial", FONT_SIZE_BUTTON, QFont.Weight.Bold))
        self.val_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_BUTTON};
                color: white;
                border: none;
                padding: 12px 30px;
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

        # Результаты проверки
        self.val_output = QTextEdit()
        self._val_text_ready.connect(self.val_output.setText)
        self._val_done.connect(lambda: self.val_button.setEnabled(True))
        self._val_done.connect(lambda: self.val_button.setText("Проверить"))
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
        layout.addWidget(self.val_output)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _run_validation(self):
        coded_point = [spin.value() for spin in self.val_spins]

        # Предупреждение об экстраполяции
        extrapolation = any(abs(v) > 1.0 for v in coded_point)

        self.val_button.setEnabled(False)
        self.val_button.setText("Моделирование...")

        def worker():
            try:
                lines = []
                if extrapolation:
                    lines.append("⚠ ВНИМАНИЕ: точка за пределами [-1, +1] — экстраполяция!\n")

                ref = self.dfe or self.ffe
                nat = coded_to_natural(coded_point, ref['factor_names'],
                                       ref['centers'], ref['deltas'])
                lines.append("Натуральные значения:")
                for key in ref['factor_names']:
                    f = next(f for f in FACTORS if f['key'] == key)
                    lines.append(f"  {f['label']} = {nat[key]:.4f}")
                lines.append("")

                for label, result in self._iter_results():
                    v = validate_at_point(
                        coded_point, result,
                        self.params['sigma1'], self.params['sigma2'],
                        self.params['replications'], self.params['limit_value'],
                        self.params['response_key'],
                    )
                    lines.append(f"═══ {label} ═══")
                    lines.append(f"  y (моделирование):  {v['y_real']:.6f}")
                    lines.append(f"  ŷ (линейная):       {v['y_linear']:.6f}"
                                 f"   |Δ| = {v['err_linear']:.6f}"
                                 f"   ({v['rel_err_linear']:.2f}%)")
                    lines.append(f"  ŷ (нелинейная):     {v['y_nonlinear']:.6f}"
                                 f"   |Δ| = {v['err_nonlinear']:.6f}"
                                 f"   ({v['rel_err_nonlinear']:.2f}%)")
                    lines.append("")

                self._val_text_ready.emit('\n'.join(lines))
            except Exception as e:
                self._val_text_ready.emit(f"Ошибка: {e}")
            finally:
                self._val_done.emit()

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    # ── Утилиты ──────────────────────────────────────────────────

    def _iter_results(self):
        """Итератор по доступным результатам с подписями."""
        items = []
        if self.ffe:
            items.append((f"ПФЭ 2⁴ ({self.ffe['n_runs']} опытов)", self.ffe))
        if self.dfe:
            items.append((f"ДФЭ ({self.dfe['n_runs']} опытов)", self.dfe))
        return items

    def _group_style(self):
        return f"""
            QGroupBox {{
                background-color: {COLOR_WIDGET_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                margin-top: 6px;
                padding: 6px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
            }}
        """
