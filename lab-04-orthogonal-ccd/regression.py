# -*- coding: utf-8 -*-
"""
ОЦКП (Ортогональный Центральный Композиционный План) для СМО с 4 факторами.

План состоит из:
  - Ядра ПФЭ 2^4 = 16 опытов (точки с координатами ±1)
  - 2n = 8 звёздных точек (с координатами ±α на осях)
  - n0 центральных точек (координаты все 0)

Модель 2-го порядка:
  ŷ = b0 + Σ bj·zj + Σ bju·zj·zu + Σ bjj·zj²

Для ортогональности столбцов квадратов используется центрирование:
  (zj² − S), где S = √(n_core / N)

Звёздное плечо:
  α = √( ½·(√(n_core·N) − n_core) )
"""

from itertools import combinations
from math import sqrt
from simulation import run_simulation_averaged
from constants import FACTORS, FACTOR_KEY_TO_INDEX, N_FACTORS, N_CORE


# ── Вспомогательные ──────────────────────────────────────────────

def effect_label(effect):
    """Строковое представление эффекта. () -> '1', ('lambda1',) -> 'x₁'."""
    if not effect:
        return '1'
    parts = []
    for key in effect:
        idx = FACTOR_KEY_TO_INDEX[key]
        parts.append(f'x{idx + 1}')
    return ''.join(parts)


def square_label(key):
    idx = FACTOR_KEY_TO_INDEX[key]
    return f'x{idx + 1}²'


def natural_label(key):
    f = next(f for f in FACTORS if f['key'] == key)
    return f['label']


def natural_square_label(key):
    f = next(f for f in FACTORS if f['key'] == key)
    return f"{f['label']}²"


# ── Параметры ОЦКП ──────────────────────────────────────────────

def compute_occd_params(n_core, n_star, n0):
    """Возвращает (N, alpha, S) для ОЦКП."""
    N = n_core + n_star + n0
    alpha_sq = 0.5 * (sqrt(n_core * N) - n_core)
    alpha = sqrt(alpha_sq)
    S = sqrt(n_core / N)
    return N, alpha, S


# ── Построение матрицы плана ────────────────────────────────────

def create_core_design(n_factors):
    """Ядро ПФЭ 2^n_factors: матрица из ±1, N_CORE строк."""
    n_runs = 2 ** n_factors
    matrix = []
    for i in range(n_runs):
        row = []
        for j in range(n_factors):
            row.append(1 if ((i >> j) & 1) else -1)
        matrix.append(row)
    return matrix


def create_star_points(n_factors, alpha):
    """2·n_factors звёздных точек: для каждой оси — точка +α и −α, остальные 0."""
    points = []
    for j in range(n_factors):
        for sign in (-1, +1):
            row = [0.0] * n_factors
            row[j] = sign * alpha
            points.append(row)
    return points


def create_occd_design(n_factors, n0=1):
    """Полная матрица ОЦКП.
    Возвращает (matrix, n_core, n_star, n0, N, alpha, S)."""
    n_core = 2 ** n_factors
    n_star = 2 * n_factors
    N, alpha, S = compute_occd_params(n_core, n_star, n0)

    core = create_core_design(n_factors)
    stars = create_star_points(n_factors, alpha)
    centers = [[0.0] * n_factors for _ in range(n0)]

    matrix = core + stars + centers
    return matrix, n_core, n_star, n0, N, alpha, S


# ── Фичи (features) для модели 2-го порядка ─────────────────────

def build_features(factor_names):
    """Возвращает список фичей модели 2-го порядка:
        [(), (x1,), (x2,), ..., (x1,x2), ..., ('sq', x1), ('sq', x2), ...]
    Где () — свободный член, (xj,) — линейный, (xj,xu) — парное, ('sq', xj) — квадрат."""
    features = [()]
    # Линейные
    for key in factor_names:
        features.append((key,))
    # Парные
    for k1, k2 in combinations(factor_names, 2):
        features.append((k1, k2))
    # Квадраты (помечены тегом 'sq')
    for key in factor_names:
        features.append(('sq', key))
    return features


def feature_value(row, factor_names, feature, S):
    """Значение фичи в строке (row — список кодированных координат)."""
    if not feature:
        return 1.0
    if feature[0] == 'sq':
        key = feature[1]
        idx = factor_names.index(key)
        return row[idx] ** 2 - S  # центрированный квадрат
    val = 1.0
    for key in feature:
        idx = factor_names.index(key)
        val *= row[idx]
    return val


def feature_label(feature):
    """Текстовая метка фичи."""
    if not feature:
        return '1'
    if feature[0] == 'sq':
        return square_label(feature[1]) + '(центр)'
    return effect_label(feature)


def feature_pretty_label(feature):
    """Более компактная метка для таблиц."""
    if not feature:
        return 'b₀'
    if feature[0] == 'sq':
        idx = FACTOR_KEY_TO_INDEX[feature[1]]
        return f'b(x{idx+1}²)'
    return f'b({effect_label(feature)})'


# ── Вычисление коэффициентов ────────────────────────────────────

def calc_coefficients(matrix, responses, factor_names, features, S):
    """Коэффициенты регрессии через ортогональную форму:
        b_f = Σ(φ_f · y) / Σ(φ_f²)"""
    n_runs = len(matrix)
    coeffs = {}
    denominators = {}
    for f in features:
        num = 0.0
        den = 0.0
        for i in range(n_runs):
            phi = feature_value(matrix[i], factor_names, f, S)
            num += phi * responses[i]
            den += phi * phi
        coeffs[f] = num / den if den > 1e-12 else 0.0
        denominators[f] = den
    return coeffs, denominators


# ── Предсказание ───────────────────────────────────────────────

def predict_centered(coeffs, row, factor_names, S):
    """Предсказание с использованием модели с центрированными квадратами."""
    y = 0.0
    for f, b in coeffs.items():
        y += b * feature_value(row, factor_names, f, S)
    return y


def predict_expanded(expanded_coeffs, row, factor_names):
    """Предсказание по уравнению с раскрытыми скобками.
    expanded_coeffs — словарь, где квадратные фичи имеют уже 'обычный' вид (без S)."""
    y = 0.0
    for f, b in expanded_coeffs.items():
        if not f:
            y += b
        elif f[0] == 'sq':
            key = f[1]
            idx = factor_names.index(key)
            y += b * (row[idx] ** 2)
        else:
            val = b
            for key in f:
                idx = factor_names.index(key)
                val *= row[idx]
            y += val
    return y


def expand_coefficients(coeffs, S):
    """Раскрытие скобок: переход от (zj² − S) к zj².
    b0' = b0 − S·Σbjj, остальные коэффициенты не меняются."""
    expanded = dict(coeffs)
    sum_bjj = 0.0
    for f, b in coeffs.items():
        if f and f[0] == 'sq':
            sum_bjj += b
    # Свободный член корректируется
    expanded[()] = coeffs.get((), 0.0) - S * sum_bjj
    return expanded


# ── Переход к натуральным переменным ────────────────────────────

def calculate_natural_coefficients(expanded_coeffs, factor_names, centers, deltas):
    """Преобразует уравнение в натуральные переменные.

    zj = (Xj - cj) / dj

    Для каждого терма в expanded_coeffs выполняем подстановку и собираем
    одноимённые слагаемые. Натуральные термы представлены как мультимножества
    ключей факторов: 'lambda1' → степень 1, 'mu1'·'mu1' → степень 2 и т.д.
    """
    # term: tuple of (key, power) pairs, sorted; () — константа
    natural = {}

    def add_to_natural(term, coeff):
        if abs(coeff) < 1e-15:
            return
        key = tuple(sorted(term))
        natural[key] = natural.get(key, 0.0) + coeff

    for f, b in expanded_coeffs.items():
        if abs(b) < 1e-15:
            continue
        # Разбираем терм
        if not f:
            add_to_natural((), b)
            continue

        if f[0] == 'sq':
            # (zj)² = ((Xj - cj)/dj)² = (1/dj²)(Xj² − 2cj·Xj + cj²)
            key = f[1]
            c = centers[key]
            d = deltas[key]
            add_to_natural(((key, 2),), b / (d * d))
            add_to_natural(((key, 1),), b * (-2 * c) / (d * d))
            add_to_natural((), b * (c * c) / (d * d))
            continue

        # Иначе это линейный или парный терм: произведение zj по ключам
        # Начинаем с константы, затем для каждого ключа умножаем на (Xj/dj − cj/dj)
        poly = {(): b}
        for key in f:
            c = centers[key]
            d = deltas[key]
            new_poly = {}
            for term, coeff in poly.items():
                # coeff · ( (1/d)·Xj + (−c/d) )
                key_term = tuple(sorted(term + ((key, 1),), key=lambda kv: kv[0]))
                # Слияние одинаковых ключей по степени
                key_term_merged = merge_powers(key_term)
                new_poly[key_term_merged] = new_poly.get(key_term_merged, 0.0) + coeff / d
                new_poly[term] = new_poly.get(term, 0.0) + coeff * (-c / d)
            poly = new_poly

        for term, coeff in poly.items():
            add_to_natural(term, coeff)

    return natural


def merge_powers(term):
    """Объединяет одинаковые ключи в терме, складывая степени."""
    d = {}
    for k, p in term:
        d[k] = d.get(k, 0) + p
    return tuple(sorted(d.items()))


def predict_natural(natural_coeffs, natural_values):
    y = 0.0
    for term, coeff in natural_coeffs.items():
        val = coeff
        for k, p in term:
            val *= natural_values[k] ** p
        y += val
    return y


# ── Форматирование уравнений ────────────────────────────────────

def format_centered_equation(coeffs, S):
    """Уравнение в центрированной форме:
    ŷ = b0 + b1·x1 + ... + b11·(x1² − S) + ..."""
    parts = []
    sorted_features = sort_features(coeffs.keys())
    for f in sorted_features:
        b = coeffs[f]
        if abs(b) < 1e-10:
            continue
        if not f:
            token = f"{b:.6f}"
        elif f[0] == 'sq':
            idx = FACTOR_KEY_TO_INDEX[f[1]]
            token = f"{abs(b):.6f}·(x{idx+1}² − {S:.4f})"
            if b < 0:
                token = '-' + token
        else:
            token = f"{abs(b):.6f}·{effect_label(f)}"
            if b < 0:
                token = '-' + token

        if not parts:
            parts.append(token)
        else:
            if token.startswith('-'):
                parts.append(' − ' + token[1:])
            else:
                parts.append(' + ' + token)
    return 'ŷ = ' + ''.join(parts) if parts else 'ŷ = 0'


def format_expanded_equation(expanded_coeffs):
    """Уравнение в стандартной форме (S подставлено, скобки раскрыты)."""
    parts = []
    sorted_features = sort_features(expanded_coeffs.keys())
    for f in sorted_features:
        b = expanded_coeffs[f]
        if abs(b) < 1e-10:
            continue
        if not f:
            token = f"{b:.6f}"
        elif f[0] == 'sq':
            idx = FACTOR_KEY_TO_INDEX[f[1]]
            token = f"{abs(b):.6f}·x{idx+1}²"
            if b < 0:
                token = '-' + token
        else:
            token = f"{abs(b):.6f}·{effect_label(f)}"
            if b < 0:
                token = '-' + token

        if not parts:
            parts.append(token)
        else:
            if token.startswith('-'):
                parts.append(' − ' + token[1:])
            else:
                parts.append(' + ' + token)
    return 'ŷ = ' + ''.join(parts) if parts else 'ŷ = 0'


def format_natural_equation(natural_coeffs):
    """Уравнение в натуральных переменных."""
    parts = []
    sorted_terms = sorted(natural_coeffs.keys(),
                          key=lambda t: (sum(p for _, p in t), t))
    for term in sorted_terms:
        b = natural_coeffs[term]
        if abs(b) < 1e-10:
            continue
        if not term:
            token = f"{b:.6f}"
        else:
            labels = []
            for k, p in term:
                lbl = natural_label(k)
                if p == 1:
                    labels.append(lbl)
                else:
                    labels.append(f"{lbl}^{p}")
            token = f"{abs(b):.6f}·{'·'.join(labels)}"
            if b < 0:
                token = '-' + token
        if not parts:
            parts.append(token)
        else:
            if token.startswith('-'):
                parts.append(' − ' + token[1:])
            else:
                parts.append(' + ' + token)
    return 'ŷ = ' + ''.join(parts) if parts else 'ŷ = 0'


def sort_features(features):
    """Упорядочивает фичи: сперва свободный член, линейные, парные, квадраты."""
    def key_fn(f):
        if not f:
            return (0, 0)
        if f[0] == 'sq':
            idx = FACTOR_KEY_TO_INDEX[f[1]]
            return (3, idx)
        return (len(f), tuple(FACTOR_KEY_TO_INDEX[k] for k in f))
    return sorted(features, key=key_fn)


# ── Кодирование/декодирование ───────────────────────────────────

def coded_to_natural(coded_row, factor_names, centers, deltas):
    return {factor_names[j]: centers[factor_names[j]] + deltas[factor_names[j]] * coded_row[j]
            for j in range(len(factor_names))}


# ── Основная функция запуска ОЦКП ──────────────────────────────

def run_occd(factor_ranges, sigma1, sigma2, replications, limit_value,
             response_key, n0=1):
    """Основная процедура: строим план, прогоняем симуляции, считаем всё."""
    factor_names = [f['key'] for f in FACTORS]
    n = len(factor_names)

    centers = {k: (factor_ranges[k][0] + factor_ranges[k][1]) / 2 for k in factor_ranges}
    deltas = {k: (factor_ranges[k][1] - factor_ranges[k][0]) / 2 for k in factor_ranges}

    matrix, n_core, n_star, n0_actual, N, alpha, S = create_occd_design(n, n0)

    # Прогон симуляции для каждой точки
    responses = []
    for coded_row in matrix:
        nat = coded_to_natural(coded_row, factor_names, centers, deltas)
        params = {
            'lambda1': nat['lambda1'],
            'sigma1': sigma1,
            'mu1': nat['mu1'],
            'lambda2': nat['lambda2'],
            'sigma2': sigma2,
            'mu2': nat['mu2'],
            'limit_value': limit_value,
        }
        y = run_simulation_averaged(params, replications, response_key)
        responses.append(y)

    # Фичи и коэффициенты
    features = build_features(factor_names)
    coeffs, denominators = calc_coefficients(matrix, responses, factor_names, features, S)
    expanded = expand_coefficients(coeffs, S)
    natural = calculate_natural_coefficients(expanded, factor_names, centers, deltas)

    # Уравнения
    eq_centered = format_centered_equation(coeffs, S)
    eq_expanded = format_expanded_equation(expanded)
    eq_natural = format_natural_equation(natural)

    # Ошибки предсказания
    run_details = []
    total_err = 0.0
    total_rel = 0.0

    for i in range(N):
        y_exp = responses[i]
        y_pred = predict_centered(coeffs, matrix[i], factor_names, S)
        err = abs(y_pred - y_exp)
        rel = (err / y_exp * 100) if y_exp != 0 else 0.0

        nat = coded_to_natural(matrix[i], factor_names, centers, deltas)
        point_type = classify_point(matrix[i], alpha)

        run_details.append({
            'run': i + 1,
            'coded': list(matrix[i]),
            'natural': nat,
            'y_exp': y_exp,
            'y_pred': y_pred,
            'err': err,
            'rel_err': rel,
            'type': point_type,
        })
        total_err += err
        total_rel += rel

    return {
        'type': 'ОЦКП',
        'n_factors': n,
        'factor_names': factor_names,
        'centers': centers,
        'deltas': deltas,
        'matrix': matrix,
        'responses': responses,
        'N': N,
        'n_core': n_core,
        'n_star': n_star,
        'n0': n0_actual,
        'alpha': alpha,
        'S': S,
        'coeffs': coeffs,
        'expanded_coeffs': expanded,
        'natural_coeffs': natural,
        'denominators': denominators,
        'features': features,
        'eq_centered': eq_centered,
        'eq_expanded': eq_expanded,
        'eq_natural': eq_natural,
        'run_details': run_details,
        'avg_err': total_err / N,
        'avg_rel_err': total_rel / N,
    }


def classify_point(row, alpha, tol=1e-9):
    """Классифицирует точку плана: 'ядро' / 'звёздная' / 'центр'."""
    non_zero = [abs(v) for v in row if abs(v) > tol]
    if not non_zero:
        return 'центр'
    if all(abs(abs(v) - 1.0) < tol for v in row):
        return 'ядро'
    # Одна координата = ±α, остальные = 0
    near_alpha = [v for v in non_zero if abs(v - alpha) < tol]
    if len(near_alpha) == 1 and len(non_zero) == 1:
        return 'звёзд.'
    return '?'


# ── Проверка в произвольной точке ──────────────────────────────

def validate_at_point(coded_point, result, sigma1, sigma2,
                      replications, limit_value, response_key):
    factor_names = result['factor_names']
    centers = result['centers']
    deltas = result['deltas']
    S = result['S']

    nat = coded_to_natural(coded_point, factor_names, centers, deltas)
    params = {
        'lambda1': nat['lambda1'],
        'sigma1': sigma1,
        'mu1': nat['mu1'],
        'lambda2': nat['lambda2'],
        'sigma2': sigma2,
        'mu2': nat['mu2'],
        'limit_value': limit_value,
    }
    y_real = run_simulation_averaged(params, replications, response_key)

    y_pred = predict_centered(result['coeffs'], coded_point, factor_names, S)
    y_pred_expanded = predict_expanded(result['expanded_coeffs'], coded_point, factor_names)
    y_pred_natural = predict_natural(result['natural_coeffs'], nat)

    return {
        'coded': coded_point,
        'natural': nat,
        'y_real': y_real,
        'y_pred': y_pred,
        'y_pred_expanded': y_pred_expanded,
        'y_pred_natural': y_pred_natural,
        'err': abs(y_pred - y_real),
        'rel_err': abs(y_pred - y_real) / y_real * 100 if y_real != 0 else 0.0,
    }
