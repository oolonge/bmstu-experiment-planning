# -*- coding: utf-8 -*-

# Размеры окон
MAIN_WINDOW_WIDTH = 950
MAIN_WINDOW_HEIGHT = 750
RESULTS_WINDOW_WIDTH = 1100
RESULTS_WINDOW_HEIGHT = 700

# Размеры шрифтов
FONT_SIZE_TITLE = 14
FONT_SIZE_LABEL = 11
FONT_SIZE_INPUT = 11
FONT_SIZE_BUTTON = 12
FONT_SIZE_RESULT = 11
FONT_SIZE_TABLE = 10

# Цвета
COLOR_BACKGROUND = "#F5F5F5"
COLOR_WIDGET_BG = "#FFFFFF"
COLOR_BUTTON = "#2196F3"
COLOR_BUTTON_HOVER = "#1976D2"
COLOR_BUTTON_SUCCESS = "#4CAF50"
COLOR_BUTTON_SUCCESS_HOVER = "#388E3C"
COLOR_BUTTON_SECONDARY = "#95A5A6"
COLOR_BUTTON_SECONDARY_HOVER = "#7F8C8D"
COLOR_ERROR = "#F44336"
COLOR_SUCCESS = "#4CAF50"

# Параметры по умолчанию (Вариант 11)
# Центральные значения (из лабы 1)
DEFAULT_LAMBDA1 = 1.5
DEFAULT_SIGMA1 = 0.15
DEFAULT_MU1 = 8.0

DEFAULT_LAMBDA2 = 2.0
DEFAULT_SIGMA2 = 0.12
DEFAULT_MU2 = 10.0

# Интервалы варьирования по умолчанию (±разброс)
DEFAULT_DELTA_LAMBDA1 = 0.3
DEFAULT_DELTA_SIGMA1 = 0.03
DEFAULT_DELTA_MU1 = 1.0

DEFAULT_DELTA_LAMBDA2 = 0.4
DEFAULT_DELTA_SIGMA2 = 0.02
DEFAULT_DELTA_MU2 = 1.5

# Граница линейности загрузки (из графика лабы 1)
# До этого значения ρ зависимость время ожидания(ρ) примерно линейная.
# Все 64 точки плана ПФЭ должны лежать в области ρ ≤ MAX_RHO_LINEAR.
DEFAULT_MAX_RHO_LINEAR = 0.6

# Параметры моделирования
DEFAULT_LIMIT_VALUE = 10000
DEFAULT_REPLICATIONS = 3

# Описание факторов
FACTORS = [
    {'key': 'lambda1', 'label': 'λ₁', 'desc': 'Интенсивность поступления (тип 1)'},
    {'key': 'sigma1',  'label': 'σ₁', 'desc': 'Разброс поступления (тип 1)'},
    {'key': 'mu1',     'label': 'μ₁', 'desc': 'Интенсивность обслуживания (тип 1)'},
    {'key': 'lambda2', 'label': 'λ₂', 'desc': 'Интенсивность поступления (тип 2)'},
    {'key': 'sigma2',  'label': 'σ₂', 'desc': 'Разброс поступления (тип 2)'},
    {'key': 'mu2',     'label': 'μ₂', 'desc': 'Интенсивность обслуживания (тип 2)'},
]

RESPONSE_OPTIONS = [
    {'key': 'avg_wait', 'label': 'Среднее время ожидания (все заявки)'},
    {'key': 'avg_sojourn', 'label': 'Среднее время пребывания (все заявки)'},
]
