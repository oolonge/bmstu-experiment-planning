# -*- coding: utf-8 -*-

# Размеры окон
MAIN_WINDOW_WIDTH = 1100
MAIN_WINDOW_HEIGHT = 730
RESULTS_WINDOW_WIDTH = 1450
RESULTS_WINDOW_HEIGHT = 750

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

# 4 варьируемых фактора
FACTORS = [
    {'key': 'lambda1', 'label': 'λ₁', 'desc': 'Интенсивность поступления (тип 1)'},
    {'key': 'mu1',     'label': 'μ₁', 'desc': 'Интенсивность обслуживания (тип 1)'},
    {'key': 'lambda2', 'label': 'λ₂', 'desc': 'Интенсивность поступления (тип 2)'},
    {'key': 'mu2',     'label': 'μ₂', 'desc': 'Интенсивность обслуживания (тип 2)'},
]

FACTOR_INDEX_MAP = {i: f['key'] for i, f in enumerate(FACTORS)}
FACTOR_KEY_TO_INDEX = {f['key']: i for i, f in enumerate(FACTORS)}

# Значения по умолчанию (min, max) — подобраны так, чтобы ρ попал в нелинейную зону
# Центр: λ=2.0, μ=6.5 → ρ ≈ 2·(2.0/6.5) ≈ 0.615
# Худшая точка ядра: λ=2.4, μ=6.0 → ρ ≈ 0.8
# Худшая звёздная точка: λ≈2.57, μ≈5.79 → ρ ≈ 0.89
DEFAULT_RANGES = {
    'lambda1': (1.6, 2.4),
    'mu1':     (6.0, 7.0),
    'lambda2': (1.6, 2.4),
    'mu2':     (6.0, 7.0),
}

# Границы ρ для нелинейной области
DEFAULT_MIN_RHO_NONLINEAR = 0.3   # в центре плана ρ должен быть >= этого
DEFAULT_MAX_RHO_STAR = 0.95       # в звёздной точке ρ не должен превышать этого

# Фиксированные параметры (не варьируются)
DEFAULT_SIGMA1 = 0.15
DEFAULT_SIGMA2 = 0.12

# Параметры моделирования
DEFAULT_LIMIT_VALUE = 10000
DEFAULT_REPLICATIONS = 3

# ОЦКП: число центральных точек
DEFAULT_N0 = 1
N_FACTORS = 4
N_CORE = 2 ** N_FACTORS  # = 16, ядро ПФЭ 2^4

# Выходные переменные
RESPONSE_OPTIONS = [
    {'key': 'avg_wait', 'label': 'Среднее время ожидания (все заявки)'},
    {'key': 'avg_sojourn', 'label': 'Среднее время пребывания (все заявки)'},
]

# Значения по умолчанию для проверки в точке (НЕ точка плана — не вершина куба и не ось)
DEFAULT_VALIDATION_POINT = [0.3, -0.5, 0.6, -0.2]

# Надстрочные индексы
SUBSCRIPTS = {0: '₀', 1: '₁', 2: '₂', 3: '₃', 4: '₄'}
