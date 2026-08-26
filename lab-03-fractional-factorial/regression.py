# -*- coding: utf-8 -*-
import re
from itertools import combinations
from simulation import run_simulation_averaged
from constants import FACTORS, FACTOR_INDEX_MAP, FACTOR_KEY_TO_INDEX


# ── Вспомогательные ──────────────────────────────────────────────

def xor_effects(left, right):
    """Симметрическая разность двух эффектов (XOR на множествах факторов)."""
    s = set(left) ^ set(right)
    return tuple(sorted(s, key=lambda k: FACTOR_KEY_TO_INDEX.get(k, 0)))


def get_all_effects(factor_names):
    """Все 2^k подмножеств factor_names (включая пустое = свободный член)."""
    effects = [()]
    for r in range(1, len(factor_names) + 1):
        for combo in combinations(factor_names, r):
            effects.append(combo)
    return effects


def get_feature_value(coded_row, factor_names, effect):
    """Значение фичи (произведение кодированных факторов эффекта)."""
    val = 1.0
    for key in effect:
        idx = factor_names.index(key)
        val *= coded_row[idx]
    return val


def effect_label(effect, use_natural_names=False):
    """Строковое представление эффекта: '' -> '1', ('lambda1',) -> 'x₁'."""
    if not effect:
        return '1'
    parts = []
    for key in effect:
        idx = FACTOR_KEY_TO_INDEX[key]
        if use_natural_names:
            f = next(f for f in FACTORS if f['key'] == key)
            parts.append(f['label'])
        else:
            parts.append(f'x{idx + 1}')
    return ''.join(parts)


# ── Парсинг генераторов ──────────────────────────────────────────

def parse_generators(text):
    """Парсит строку генераторов вида 'x4=x1*x2*x3, x3=x1*x2'.
    Возвращает список {'target': int, 'sources': [(index, sign), ...]}.
    Индексы 0-based."""
    generators = []
    for part in text.split(','):
        part = part.strip()
        if not part or '=' not in part:
            continue
        left, right = part.split('=', 1)
        left = left.strip()
        m = re.match(r'^x(\d+)$', left)
        if not m:
            raise ValueError(f"Некорректный целевой фактор: '{left}'")
        target = int(m.group(1)) - 1

        tokens = re.findall(r'(-?)x(\d+)', right.replace('*', ''))
        if not tokens:
            raise ValueError(f"Некорректное выражение: '{right}'")
        sources = []
        for sign_str, idx_str in tokens:
            sign = -1 if sign_str == '-' else 1
            sources.append((int(idx_str) - 1, sign))
        generators.append({'target': target, 'sources': sources})
    return generators


def validate_generators(text, n_factors, p_value):
    """Проверяет генераторы. Возвращает строку ошибки или ''."""
    try:
        gens = parse_generators(text)
    except ValueError as e:
        return str(e)

    if len(gens) != p_value:
        return f"Ожидается {p_value} генератор(ов), получено {len(gens)}"

    targets = set()
    for g in gens:
        t = g['target']
        if t < 0 or t >= n_factors:
            return f"Целевой индекс x{t + 1} вне диапазона [x1..x{n_factors}]"
        if t in targets:
            return f"Дублирующийся целевой фактор x{t + 1}"
        targets.add(t)

    for g in gens:
        for src_idx, _ in g['sources']:
            if src_idx < 0 or src_idx >= n_factors:
                return f"Индекс источника x{src_idx + 1} вне диапазона"
            if src_idx in targets:
                return f"Источник x{src_idx + 1} сам является генерируемым"
    return ''


# ── Определяющие соотношения и смешивание ────────────────────────

def get_defining_relations(factor_names, generators):
    """Строит определяющие соотношения из генераторов и замыкает под XOR."""
    base_relations = []
    for g in generators:
        target_key = factor_names[g['target']]
        source_keys = tuple(factor_names[idx] for idx, _ in g['sources'])
        relation = xor_effects((target_key,), source_keys)
        base_relations.append(relation)

    # Замыкание: попарный XOR всех имеющихся соотношений
    relations = set(base_relations)
    changed = True
    while changed:
        changed = False
        current = list(relations)
        for i in range(len(current)):
            for j in range(i + 1, len(current)):
                new_rel = xor_effects(current[i], current[j])
                if new_rel and new_rel not in relations:
                    relations.add(new_rel)
                    changed = True

    return sorted(relations, key=lambda r: (len(r), r))


def build_aliases(factor_names, defining_relations):
    """Строит группы смешивания (alias groups)."""
    all_effects = get_all_effects(factor_names)
    visited = set()
    groups = []

    for effect in all_effects:
        if effect in visited:
            continue
        group = {effect}
        for dr in defining_relations:
            alias = xor_effects(effect, dr)
            group.add(alias)
        for e in group:
            visited.add(e)
        groups.append(sorted(group, key=lambda e: (len(e), e)))

    return sorted(groups, key=lambda g: (len(g[0]), g[0]))


def build_alias_map(aliases, computed_effects):
    """Для каждого эффекта, не входящего в computed_effects, находит его alias.
    Возвращает dict: effect -> alias_effect (тот, что был вычислен)."""
    computed_set = set(computed_effects)
    alias_map = {}
    for group in aliases:
        computed_in_group = [e for e in group if e in computed_set]
        if not computed_in_group:
            continue
        representative = computed_in_group[0]
        for e in group:
            if e not in computed_set:
                alias_map[e] = representative
    return alias_map


def build_aliasing_string(factor_names, p_value, defining_relations, aliases):
    """Формирует текстовое описание схемы смешивания."""
    n = len(factor_names)
    lines = [f"ДФЭ 2^({n}-{p_value}) = 2^{n - p_value} = {2 ** (n - p_value)} опытов"]

    # Разрешающая способность
    if defining_relations:
        min_len = min(len(r) for r in defining_relations)
        roman = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V'}
        res = roman.get(min_len, str(min_len))
        lines.append(f"Разрешающая способность: {res}")

    lines.append("")
    lines.append("Определяющие соотношения:")
    for r in defining_relations:
        label = ''.join(f'x{FACTOR_KEY_TO_INDEX[k] + 1}' for k in r)
        lines.append(f"  I = {label}")

    lines.append("")
    lines.append("Схема смешивания:")
    for group in aliases:
        labels = [effect_label(e) for e in group]
        if len(labels) > 1:
            lines.append(f"  {' = '.join(labels)}")

    return '\n'.join(lines)


# ── Матрицы планирования ─────────────────────────────────────────

def create_full_factorial_design(n_factors):
    """Полный факторный план 2^n: матрица из ±1."""
    n_runs = 2 ** n_factors
    matrix = []
    for i in range(n_runs):
        row = []
        for j in range(n_factors):
            row.append(1 if ((i >> j) & 1) else -1)
        matrix.append(row)
    return matrix


def create_fractional_design(factor_names, generators):
    """Дробный факторный план. Базовые факторы — полный план, генерируемые — произведения."""
    n = len(factor_names)
    targets = {g['target'] for g in generators}
    base_indices = [i for i in range(n) if i not in targets]
    base_count = len(base_indices)

    base_matrix = create_full_factorial_design(base_count)
    n_runs = len(base_matrix)

    matrix = []
    for base_row in base_matrix:
        full_row = [0] * n
        for bi, fi in enumerate(base_indices):
            full_row[fi] = base_row[bi]

        for g in generators:
            val = 1
            overall_sign = 1
            for src_idx, sign in g['sources']:
                overall_sign *= sign
                val *= full_row[src_idx]
            full_row[g['target']] = overall_sign * val

        matrix.append(full_row)
    return matrix


# ── Кодирование/декодирование ────────────────────────────────────

def coded_to_natural(coded_row, factor_names, centers, deltas):
    return {factor_names[j]: centers[factor_names[j]] + deltas[factor_names[j]] * coded_row[j]
            for j in range(len(factor_names))}


def natural_to_coded(natural_values, factor_names, centers, deltas):
    return [(natural_values[k] - centers[k]) / deltas[k] for k in factor_names]


# ── Вычисление коэффициентов ─────────────────────────────────────

def calc_coefficients(matrix, responses, factor_names, features):
    """Коэффициенты регрессии: b_feature = (1/N) * sum(y_i * feature_value_i)."""
    n_runs = len(matrix)
    coeffs = {}
    for feature in features:
        s = 0.0
        for i in range(n_runs):
            fv = get_feature_value(matrix[i], factor_names, feature)
            s += responses[i] * fv
        coeffs[feature] = s / n_runs
    return coeffs


def split_coefficients(coefficients):
    """Разделяет на линейные (длина эффекта <= 1) и полные."""
    linear = {k: v for k, v in coefficients.items() if len(k) <= 1}
    return linear, coefficients


# ── Переход к натуральным переменным ─────────────────────────────

def calculate_natural_coefficients(norm_coeffs, factor_names, centers, deltas):
    """Преобразует нормированные коэффициенты в натуральные через раскрытие подстановок."""
    natural = {}

    for effect, b_val in norm_coeffs.items():
        # Полиномиальное расширение: заменяем каждый z_j = (X_j - c_j) / d_j
        # Начинаем с {(): b_val}, затем для каждого фактора в эффекте умножаем
        poly = {(): b_val}

        for key in effect:
            c = centers[key]
            d = deltas[key]
            new_poly = {}
            for term, coeff in poly.items():
                # coeff * (X_key - c) / d  =  (coeff/d) * X_key + (-coeff*c/d) * 1
                # Член с X_key
                new_term = tuple(sorted(term + (key,), key=lambda k: FACTOR_KEY_TO_INDEX.get(k, 0)))
                new_poly[new_term] = new_poly.get(new_term, 0.0) + coeff / d
                # Константный член
                new_poly[term] = new_poly.get(term, 0.0) + (-coeff * c / d)
            poly = new_poly

        for term, coeff in poly.items():
            natural[term] = natural.get(term, 0.0) + coeff

    return natural


def predict_from_coefficients(coefficients, coded_row, factor_names):
    """Предсказание по нормированным коэффициентам."""
    y = 0.0
    for effect, b in coefficients.items():
        y += b * get_feature_value(coded_row, factor_names, effect)
    return y


def predict_natural(natural_coeffs, natural_values):
    """Предсказание по натуральным коэффициентам."""
    y = 0.0
    for term, coeff in natural_coeffs.items():
        val = coeff
        for key in term:
            val *= natural_values[key]
        y += val
    return y


# ── Форматирование уравнений ─────────────────────────────────────

def format_equation(coefficients, factor_names, natural=False):
    """Форматирует уравнение регрессии в строку."""
    sorted_effects = sorted(coefficients.keys(), key=lambda e: (len(e), e))
    parts = []

    for effect in sorted_effects:
        val = coefficients[effect]
        if abs(val) < 1e-10:
            continue
        label = effect_label(effect, use_natural_names=natural)

        if not parts:
            if label == '1':
                parts.append(f"{val:.4f}")
            else:
                parts.append(f"{val:.4f}·{label}")
        else:
            sign = '+' if val >= 0 else '-'
            if label == '1':
                parts.append(f" {sign} {abs(val):.4f}")
            else:
                parts.append(f" {sign} {abs(val):.4f}·{label}")

    return 'ŷ = ' + ''.join(parts) if parts else 'ŷ = 0'


# ── Основные функции запуска ─────────────────────────────────────

def _run_experiments(matrix, factor_names, centers, deltas,
                     sigma1, sigma2, replications, limit_value,
                     features, response_key):
    """Прогоняет эксперименты и вычисляет коэффициенты + ошибки."""
    n_runs = len(matrix)
    responses = []

    for coded_row in matrix:
        nat = coded_to_natural(coded_row, factor_names, centers, deltas)
        params = {
            'lambda1': nat.get('lambda1', 1.0),
            'sigma1': sigma1,
            'mu1': nat.get('mu1', 8.0),
            'lambda2': nat.get('lambda2', 1.0),
            'sigma2': sigma2,
            'mu2': nat.get('mu2', 10.0),
            'limit_value': limit_value,
        }
        y = run_simulation_averaged(params, replications, response_key)
        responses.append(y)

    # Коэффициенты
    all_coeffs = calc_coefficients(matrix, responses, factor_names, features)
    linear_coeffs, full_coeffs = split_coefficients(all_coeffs)

    # Натуральные коэффициенты
    natural_linear = calculate_natural_coefficients(linear_coeffs, factor_names, centers, deltas)
    natural_full = calculate_natural_coefficients(full_coeffs, factor_names, centers, deltas)

    # Уравнения
    eq_lin_norm = format_equation(linear_coeffs, factor_names, natural=False)
    eq_full_norm = format_equation(full_coeffs, factor_names, natural=False)
    eq_lin_nat = format_equation(natural_linear, factor_names, natural=True)
    eq_full_nat = format_equation(natural_full, factor_names, natural=True)

    # Ошибки предсказания
    run_details = []
    total_err_lin = 0.0
    total_err_full = 0.0
    total_rel_lin = 0.0
    total_rel_full = 0.0

    for i in range(n_runs):
        y_exp = responses[i]
        y_lin = predict_from_coefficients(linear_coeffs, matrix[i], factor_names)
        y_full = predict_from_coefficients(full_coeffs, matrix[i], factor_names)
        err_lin = abs(y_lin - y_exp)
        err_full = abs(y_full - y_exp)
        rel_lin = (err_lin / y_exp * 100) if y_exp != 0 else 0
        rel_full = (err_full / y_exp * 100) if y_exp != 0 else 0

        nat = coded_to_natural(matrix[i], factor_names, centers, deltas)

        run_details.append({
            'run': i + 1,
            'coded': list(matrix[i]),
            'natural': nat,
            'y_exp': y_exp,
            'y_linear': y_lin,
            'y_nonlinear': y_full,
            'err_linear': err_lin,
            'err_nonlinear': err_full,
            'rel_err_linear': rel_lin,
            'rel_err_nonlinear': rel_full,
        })
        total_err_lin += err_lin
        total_err_full += err_full
        total_rel_lin += rel_lin
        total_rel_full += rel_full

    return {
        'n_runs': n_runs,
        'responses': responses,
        'linear_coeffs': linear_coeffs,
        'full_coeffs': full_coeffs,
        'natural_linear': natural_linear,
        'natural_full': natural_full,
        'eq_lin_norm': eq_lin_norm,
        'eq_full_norm': eq_full_norm,
        'eq_lin_nat': eq_lin_nat,
        'eq_full_nat': eq_full_nat,
        'run_details': run_details,
        'avg_err_linear': total_err_lin / n_runs,
        'avg_err_nonlinear': total_err_full / n_runs,
        'avg_rel_err_linear': total_rel_lin / n_runs,
        'avg_rel_err_nonlinear': total_rel_full / n_runs,
    }


def run_ffe(factor_ranges, sigma1, sigma2, replications, limit_value, response_key):
    """Запуск ПФЭ 2^4."""
    factor_names = [f['key'] for f in FACTORS]
    n = len(factor_names)
    centers = {k: (factor_ranges[k][0] + factor_ranges[k][1]) / 2 for k in factor_ranges}
    deltas = {k: (factor_ranges[k][1] - factor_ranges[k][0]) / 2 for k in factor_ranges}

    matrix = create_full_factorial_design(n)
    features = get_all_effects(factor_names)

    result = _run_experiments(matrix, factor_names, centers, deltas,
                              sigma1, sigma2, replications, limit_value,
                              features, response_key)
    result['type'] = 'ПФЭ'
    result['n_factors'] = n
    result['factor_names'] = factor_names
    result['centers'] = centers
    result['deltas'] = deltas
    result['features'] = features
    return result


def run_dfe(factor_ranges, sigma1, sigma2, replications, limit_value,
            generators_text, fraction, response_key):
    """Запуск ДФЭ 2^(4-p)."""
    factor_names = [f['key'] for f in FACTORS]
    n = len(factor_names)
    p_value = {'1/2': 1, '1/4': 2}.get(fraction, 1)
    centers = {k: (factor_ranges[k][0] + factor_ranges[k][1]) / 2 for k in factor_ranges}
    deltas = {k: (factor_ranges[k][1] - factor_ranges[k][0]) / 2 for k in factor_ranges}

    generators = parse_generators(generators_text)
    matrix = create_fractional_design(factor_names, generators)

    # Для ДФЭ фичи берём только от базовых факторов
    targets = {g['target'] for g in generators}
    base_names = [factor_names[i] for i in range(n) if i not in targets]
    features = get_all_effects(base_names)

    result = _run_experiments(matrix, factor_names, centers, deltas,
                              sigma1, sigma2, replications, limit_value,
                              features, response_key)

    # Смешивание
    defining_relations = get_defining_relations(factor_names, generators)
    aliases = build_aliases(factor_names, defining_relations)
    aliasing_str = build_aliasing_string(factor_names, p_value, defining_relations, aliases)

    # Маппинг смешанных эффектов
    alias_map = build_alias_map(aliases, list(result['full_coeffs'].keys()))

    result['type'] = 'ДФЭ'
    result['n_factors'] = n
    result['p_value'] = p_value
    result['factor_names'] = factor_names
    result['centers'] = centers
    result['deltas'] = deltas
    result['features'] = features
    result['generators_text'] = generators_text
    result['defining_relations'] = defining_relations
    result['aliases'] = aliases
    result['alias_map'] = alias_map
    result['aliasing_str'] = aliasing_str
    return result


def validate_at_point(coded_point, result, sigma1, sigma2,
                      replications, limit_value, response_key):
    """Проверка модели в произвольной нормированной точке."""
    factor_names = result['factor_names']
    centers = result['centers']
    deltas = result['deltas']

    nat = coded_to_natural(coded_point, factor_names, centers, deltas)
    params = {
        'lambda1': nat.get('lambda1', 1.0),
        'sigma1': sigma1,
        'mu1': nat.get('mu1', 8.0),
        'lambda2': nat.get('lambda2', 1.0),
        'sigma2': sigma2,
        'mu2': nat.get('mu2', 10.0),
        'limit_value': limit_value,
    }
    y_real = run_simulation_averaged(params, replications, response_key)

    y_lin = predict_from_coefficients(result['linear_coeffs'], coded_point, factor_names)
    y_full = predict_from_coefficients(result['full_coeffs'], coded_point, factor_names)

    return {
        'coded': coded_point,
        'natural': nat,
        'y_real': y_real,
        'y_linear': y_lin,
        'y_nonlinear': y_full,
        'err_linear': abs(y_lin - y_real),
        'err_nonlinear': abs(y_full - y_real),
        'rel_err_linear': abs(y_lin - y_real) / y_real * 100 if y_real != 0 else 0,
        'rel_err_nonlinear': abs(y_full - y_real) / y_real * 100 if y_real != 0 else 0,
    }
