# -*- coding: utf-8 -*-

# Размеры окон (×1.5 от лабы 2)
MAIN_WINDOW_WIDTH = 1100
MAIN_WINDOW_HEIGHT = 900
RESULTS_WINDOW_WIDTH = 1430
RESULTS_WINDOW_HEIGHT = 950

# Размеры шрифтов
FONT_SIZE_TITLE = 21
FONT_SIZE_SUBTITLE = 14
FONT_SIZE_LABEL = 16
FONT_SIZE_INPUT = 16
FONT_SIZE_BUTTON = 17
FONT_SIZE_RESULT = 16
FONT_SIZE_TABLE = 14
FONT_SIZE_TABLE_HEADER = 16
FONT_SIZE_EQUATION = 16

# Цвета
COLOR_BACKGROUND = "#F5F5F5"
COLOR_WIDGET_BG = "#FFFFFF"
COLOR_BUTTON = "#2196F3"
COLOR_BUTTON_HOVER = "#1976D2"
COLOR_BUTTON_SUCCESS = "#4CAF50"
COLOR_BUTTON_SUCCESS_HOVER = "#388E3C"
COLOR_BUTTON_SECONDARY = "#78909C"
COLOR_BUTTON_SECONDARY_HOVER = "#546E7A"
COLOR_ERROR = "#F44336"
COLOR_SUCCESS = "#4CAF50"
COLOR_WARNING = "#FF9800"
COLOR_SECTION_BG = "#FAFAFA"
COLOR_BORDER = "#E0E0E0"

# 4 варьируемых фактора ДФЭ
FACTORS = [
    {'key': 'lambda1', 'label': 'λ₁', 'desc': 'Интенсивность поступления (тип 1)'},
    {'key': 'mu1',     'label': 'μ₁', 'desc': 'Интенсивность обслуживания (тип 1)'},
    {'key': 'lambda2', 'label': 'λ₂', 'desc': 'Интенсивность поступления (тип 2)'},
    {'key': 'mu2',     'label': 'μ₂', 'desc': 'Интенсивность обслуживания (тип 2)'},
]

# Индексный маппинг x1..x4 -> ключи факторов
FACTOR_INDEX_MAP = {i: f['key'] for i, f in enumerate(FACTORS)}
FACTOR_KEY_TO_INDEX = {f['key']: i for i, f in enumerate(FACTORS)}

# Значения по умолчанию (min, max)
DEFAULT_RANGES = {
    'lambda1': (1.0, 1.5),
    'mu1':     (9.0, 11.0),
    'lambda2': (1.0, 2.0),
    'mu2':     (11.0, 13.0),
}

# Граница линейности (из ЛР1)
DEFAULT_MAX_RHO_LINEAR = 0.6

# Фиксированные параметры (не варьируются)
DEFAULT_SIGMA1 = 0.15
DEFAULT_SIGMA2 = 0.12

# Параметры моделирования
DEFAULT_LIMIT_VALUE = 10000
DEFAULT_REPLICATIONS = 3

# Дробность (для 4 факторов допустима только полуреплика)
FRACTION = '1/2'
DEFAULT_GENERATOR = 'x4=x1*x2*x3'

# Выходные переменные
RESPONSE_OPTIONS = [
    {'key': 'avg_wait', 'label': 'Среднее время ожидания (все заявки)'},
    {'key': 'avg_sojourn', 'label': 'Среднее время пребывания (все заявки)'},
]

# Надстрочные индексы
SUBSCRIPTS = {0: '₀', 1: '₁', 2: '₂', 3: '₃', 4: '₄', 5: '₅', 6: '₆'}
