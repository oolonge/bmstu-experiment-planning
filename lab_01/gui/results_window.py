# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QTableWidget, QTableWidgetItem,
                              QGroupBox, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from constants import *


class ResultsWindow(QDialog):

    def __init__(self, results: dict, params: dict, parent=None):
        super().__init__(parent)
        self.results = results
        self.params = params
        self.init_ui()
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

    def init_ui(self):
        self.setWindowTitle("Результаты моделирования")
        self.setFixedSize(RESULTS_WINDOW_WIDTH, RESULTS_WINDOW_HEIGHT)
        self.setModal(True)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("Результаты моделирования")
        title_font = QFont("Arial", FONT_SIZE_TITLE + 2)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Загрузка системы
        load_group = self._create_load_group()
        main_layout.addWidget(load_group)

        # Статистика по типам заявок
        stats_group = self._create_stats_group()
        main_layout.addWidget(stats_group)

        main_layout.addStretch()

        # Кнопка закрытия
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton("Закрыть")
        close_button.setFont(QFont("Arial", FONT_SIZE_BUTTON))
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_BUTTON_SECONDARY};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_BUTTON_SECONDARY_HOVER};
            }}
        """)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _create_load_group(self) -> QGroupBox:
        group = QGroupBox("Загрузка системы")
        group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        group.setStyleSheet(self._get_group_style())

        layout = QVBoxLayout()

        rho1 = self.params['lambda1'] / self.params['mu1'] if self.params['mu1'] > 0 else 0
        rho2 = self.params['lambda2'] / self.params['mu2'] if self.params['mu2'] > 0 else 0
        rho_total = rho1 + rho2
        regime = "СТАЦИОНАРНЫЙ" if rho_total < 1 else "НЕСТАЦИОНАРНЫЙ"

        table = QTableWidget(4, 2)
        table.setFont(QFont("Arial", FONT_SIZE_RESULT))
        table.horizontalHeader().setVisible(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setMaximumHeight(140)

        rows = [
            ("Режим:", regime),
            ("Расчётная загрузка ρ:", f"{self.results['theoretical_load']:.4f}"),
            ("Фактическая загрузка:", f"{self.results['actual_load']:.4f}"),
            ("ρ₁ / ρ₂:", f"{rho1:.4f} / {rho2:.4f}"),
        ]

        for i, (label, value) in enumerate(rows):
            table.setItem(i, 0, QTableWidgetItem(label))
            item = QTableWidgetItem(value)
            if i == 0:
                color = QColor(COLOR_SUCCESS) if rho_total < 1 else QColor(COLOR_ERROR)
                item.setForeground(color)
                item.setFont(QFont("Arial", FONT_SIZE_RESULT, QFont.Weight.Bold))
            table.setItem(i, 1, item)

        layout.addWidget(table)
        group.setLayout(layout)
        return group

    def _create_stats_group(self) -> QGroupBox:
        group = QGroupBox("Статистика по заявкам")
        group.setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        group.setStyleSheet(self._get_group_style())

        layout = QVBoxLayout()

        table = QTableWidget(5, 3)
        table.setFont(QFont("Arial", FONT_SIZE_RESULT))
        table.setHorizontalHeaderLabels(["Параметр", "Тип 1", "Тип 2"])
        table.horizontalHeader().setFont(QFont("Arial", FONT_SIZE_LABEL, QFont.Weight.Bold))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setMaximumHeight(190)

        r = self.results
        rows = [
            ("Сгенерировано", str(r['generated_1']), str(r['generated_2'])),
            ("Обработано", str(r['served_1']), str(r['served_2'])),
            ("Ср. время ожидания", f"{r['avg_wait_1']:.4f}", f"{r['avg_wait_2']:.4f}"),
            ("Ср. время пребывания", f"{r['avg_sojourn_1']:.4f}", f"{r['avg_sojourn_2']:.4f}"),
            ("Время моделирования", f"{r['total_time']:.2f}", ""),
        ]

        for i, (param, v1, v2) in enumerate(rows):
            table.setItem(i, 0, QTableWidgetItem(param))
            table.setItem(i, 1, QTableWidgetItem(v1))
            table.setItem(i, 2, QTableWidgetItem(v2))

        if r['queue_left'] > 0:
            warning = QLabel(f"В очереди осталось {r['queue_left']} заявок")
            warning.setFont(QFont("Arial", FONT_SIZE_LABEL))
            warning.setStyleSheet(f"color: {COLOR_ERROR};")
            warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(warning)

        layout.addWidget(table)
        group.setLayout(layout)
        return group

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
