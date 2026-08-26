# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                              QGroupBox, QHeaderView, QScrollArea, QTabWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from constants import *


class ResultsWindow(QMainWindow):

    def __init__(self, result: dict, parent=None):
        super().__init__(parent)
        self.result = result
        self.init_ui()
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

    def init_ui(self):
        self.setWindowTitle("Результаты ПФЭ 2⁶")
        self.setFixedSize(RESULTS_WINDOW_WIDTH, RESULTS_WINDOW_HEIGHT)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout()
        outer.setContentsMargins(10, 10, 10, 10)

        tabs = QTabWidget()
        tabs.setFont(QFont("Arial", FONT_SIZE_LABEL))

        tabs.addTab(self._create_equations_tab(), "Уравнения")
        tabs.addTab(self._create_coefficients_tab(), "Коэффициенты")
        tabs.addTab(self._create_experiments_tab(), "Таблица экспериментов")
        tabs.addTab(self._create_center_tab(), "Центр плана")

        outer.addWidget(tabs)
        central.setLayout(outer)

    # === Вкладка 1: Уравнения ===
    def _create_equations_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        r = self.result

        # Метрики
        metrics_group = QGroupBox("Сводка эксперимента")
        metrics_group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        metrics_group.setStyleSheet(self._get_group_style())
        ml = QHBoxLayout()

        for label, value in [
            ("Факторов:", str(r['n_factors'])),
            ("Экспериментов:", str(r['n_runs'])),
            ("Повторов:", str(r['replications'])),
            ("Ср. отн. ошибка лин.:", f"{r['avg_rel_error_linear']:.2f}%"),
            ("Ср. отн. ошибка нелин.:", f"{r['avg_rel_error_nonlinear']:.2f}%"),
        ]:
            card = QVBoxLayout()
            lbl = QLabel(label)
            lbl.setFont(QFont("Arial", 9))
            lbl.setStyleSheet("color: #7F8C8D;")
            val = QLabel(value)
            val.setFont(QFont("Arial", FONT_SIZE_RESULT, QFont.Weight.Bold))
            card.addWidget(lbl)
            card.addWidget(val)
            ml.addLayout(card)

        metrics_group.setLayout(ml)
        layout.addWidget(metrics_group)

        # Уравнения
        for title, eq_key in [
            ("Линейная модель (нормированные)", 'eq_linear_norm'),
            ("Линейная модель (натуральные)", 'eq_linear_nat'),
            ("Нелинейная модель (нормированные)", 'eq_nonlinear_norm'),
            ("Нелинейная модель (натуральные)", 'eq_nonlinear_nat'),
        ]:
            group = QGroupBox(title)
            group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
            group.setStyleSheet(self._get_group_style())
            gl = QVBoxLayout()
            eq_label = QLabel(r[eq_key])
            eq_label.setFont(QFont("Courier New", FONT_SIZE_TABLE))
            eq_label.setWordWrap(True)
            eq_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            gl.addWidget(eq_label)
            group.setLayout(gl)
            layout.addWidget(group)

        layout.addStretch()
        widget.setLayout(layout)

        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        return scroll

    # === Вкладка 2: Коэффициенты ===
    def _create_coefficients_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        r = self.result
        fl = r['factor_labels']

        # Линейные коэффициенты
        lin_group = QGroupBox("Коэффициенты линейной модели")
        lin_group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        lin_group.setStyleSheet(self._get_group_style())
        ll = QVBoxLayout()

        lin_table = QTableWidget(1, len(fl) + 1)
        lin_table.setFont(QFont("Arial", FONT_SIZE_TABLE))
        headers = ["b₀"] + [f"b({l})" for l in fl]
        lin_table.setHorizontalHeaderLabels(headers)
        lin_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        lin_table.verticalHeader().setVisible(False)
        lin_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lin_table.setMaximumHeight(60)

        lin_table.setItem(0, 0, QTableWidgetItem(f"{r['b0_linear']:.6f}"))
        for j, b in enumerate(r['b_linear']):
            lin_table.setItem(0, j + 1, QTableWidgetItem(f"{b:.6f}"))

        ll.addWidget(lin_table)
        lin_group.setLayout(ll)
        layout.addWidget(lin_group)

        # Нелинейные коэффициенты
        nl_group = QGroupBox("Коэффициенты нелинейной модели")
        nl_group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        nl_group.setStyleSheet(self._get_group_style())
        nl = QVBoxLayout()

        inter = r['interaction_labels']
        all_labels = ["b₀"] + [f"b({l})" for l in fl] + [f"b({l})" for l in inter]
        all_vals = [r['b0_nonlinear']] + r['b_nonlinear'] + r['b_interaction']

        nl_table = QTableWidget(1, len(all_labels))
        nl_table.setFont(QFont("Arial", FONT_SIZE_TABLE))
        nl_table.setHorizontalHeaderLabels(all_labels)
        nl_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        nl_table.verticalHeader().setVisible(False)
        nl_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        nl_table.setMaximumHeight(60)

        for j, v in enumerate(all_vals):
            nl_table.setItem(0, j, QTableWidgetItem(f"{v:.6f}"))

        nl.addWidget(nl_table)
        nl_group.setLayout(nl)
        layout.addWidget(nl_group)

        layout.addStretch()
        widget.setLayout(layout)

        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        return scroll

    # === Вкладка 3: Таблица экспериментов ===
    def _create_experiments_tab(self):
        r = self.result
        details = r['run_details']
        fl = r['factor_labels']
        n_factors = r['n_factors']

        # Столбцы: № | x1..x6 (coded) | X1..X6 (natural) | y_exp | y_lin | y_nl | Δлин | Δнл | %лин | %нл
        n_cols = 1 + n_factors + n_factors + 1 + 1 + 1 + 1 + 1 + 1 + 1
        headers = (["№"]
                   + [f"x({l})" for l in fl]
                   + [l for l in fl]
                   + ["y_эксп", "ŷ_лин", "ŷ_нелин",
                      "|Δ| лин", "|Δ| нелин", "% лин", "% нелин"])

        table = QTableWidget(len(details), len(headers))
        table.setFont(QFont("Arial", FONT_SIZE_TABLE))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)

        for i, d in enumerate(details):
            col = 0
            table.setItem(i, col, QTableWidgetItem(str(d['run'])))
            col += 1

            for v in d['coded']:
                item = QTableWidgetItem(f"{v:+d}")
                if v == -1:
                    item.setForeground(QColor("#2196F3"))
                else:
                    item.setForeground(QColor("#F44336"))
                table.setItem(i, col, item)
                col += 1

            for v in d['natural']:
                table.setItem(i, col, QTableWidgetItem(f"{v:.4f}"))
                col += 1

            table.setItem(i, col, QTableWidgetItem(f"{d['y_experiment']:.6f}"))
            col += 1
            table.setItem(i, col, QTableWidgetItem(f"{d['y_linear']:.6f}"))
            col += 1
            table.setItem(i, col, QTableWidgetItem(f"{d['y_nonlinear']:.6f}"))
            col += 1
            table.setItem(i, col, QTableWidgetItem(f"{d['error_linear']:.6f}"))
            col += 1
            table.setItem(i, col, QTableWidgetItem(f"{d['error_nonlinear']:.6f}"))
            col += 1
            table.setItem(i, col, QTableWidgetItem(f"{d['rel_error_linear']:.2f}%"))
            col += 1
            table.setItem(i, col, QTableWidgetItem(f"{d['rel_error_nonlinear']:.2f}%"))

        return table

    # === Вкладка 4: Сравнение в центре плана ===
    def _create_center_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        r = self.result

        group = QGroupBox("Проверка в центре плана (все факторы = 0)")
        group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        group.setStyleSheet(self._get_group_style())
        gl = QVBoxLayout()

        table = QTableWidget(6, 2)
        table.setFont(QFont("Arial", FONT_SIZE_RESULT))
        table.horizontalHeader().setVisible(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setMaximumHeight(220)

        fl = r['factor_labels']
        center_str = ", ".join(
            f"{fl[j]}={r['center_values'][j]:.3f}" for j in range(r['n_factors']))

        rows = [
            ("Значения факторов:", center_str),
            ("y (моделирование):", f"{r['center_y_real']:.6f}"),
            ("ŷ линейная:", f"{r['center_y_linear']:.6f}"),
            ("ŷ нелинейная:", f"{r['center_y_nonlinear']:.6f}"),
            ("|Δ| линейная:", f"{r['center_error_linear']:.6f}"),
            ("|Δ| нелинейная:", f"{r['center_error_nonlinear']:.6f}"),
        ]

        for i, (label, value) in enumerate(rows):
            table.setItem(i, 0, QTableWidgetItem(label))
            table.setItem(i, 1, QTableWidgetItem(value))

        gl.addWidget(table)

        note = QLabel(
            "В центре плана все кодированные факторы = 0, поэтому\n"
            "предсказание обеих моделей = b₀ (свободный член).\n"
            "Разница с реальным значением показывает точность b₀."
        )
        note.setFont(QFont("Arial", 10))
        note.setStyleSheet("color: #7F8C8D;")
        gl.addWidget(note)

        group.setLayout(gl)
        layout.addWidget(group)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

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
