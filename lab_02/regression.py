# -*- coding: utf-8 -*-

"""
ПФЭ 2^6 — полный факторный эксперимент для 6 факторов.

Строит матрицу планирования, вычисляет коэффициенты линейной
и частично нелинейной (с парными взаимодействиями) регрессии.
"""

from simulation import run_simulation_averaged
from constants import FACTORS


def build_design_matrix(n_factors):
    """Матрица планирования ПФЭ 2^n: все комбинации ±1."""
    n_runs = 2 ** n_factors
    matrix = []
    for i in range(n_runs):
        row = []
        for j in range(n_factors):
            level = +1 if (i >> j) & 1 else -1
            row.append(level)
        matrix.append(row)
    return matrix


def coded_to_natural(coded_row, centers, deltas):
    """Перевод кодированных значений ±1 в натуральные."""
    return [centers[j] + deltas[j] * coded_row[j] for j in range(len(coded_row))]


def natural_to_coded(natural_row, centers, deltas):
    """Перевод натуральных значений в кодированные."""
    return [(natural_row[j] - centers[j]) / deltas[j] for j in range(len(natural_row))]


def compute_interaction_terms(coded_row):
    """Парные произведения x_i * x_j для i < j."""
    n = len(coded_row)
    terms = []
    for i in range(n):
        for j in range(i + 1, n):
            terms.append(coded_row[i] * coded_row[j])
    return terms


def interaction_labels(factor_labels):
    """Названия парных взаимодействий."""
    n = len(factor_labels)
    labels = []
    for i in range(n):
        for j in range(i + 1, n):
            labels.append(f"{factor_labels[i]}·{factor_labels[j]}")
    return labels


def calc_coefficients_linear(matrix, responses):
    """
    Коэффициенты линейной модели по формуле МНК для ПФЭ:
    b_j = (1/N) * Σ(x_ij * y_i)
    """
    n_runs = len(matrix)
    n_factors = len(matrix[0])
    b0 = sum(responses) / n_runs
    b = []
    for j in range(n_factors):
        s = sum(matrix[i][j] * responses[i] for i in range(n_runs))
        b.append(s / n_runs)
    return b0, b


def calc_coefficients_nonlinear(matrix, responses):
    """
    Коэффициенты частично нелинейной модели (линейные + парные взаимодействия).
    b_jk = (1/N) * Σ(x_ij * x_ik * y_i)
    """
    n_runs = len(matrix)
    n_factors = len(matrix[0])

    b0, b_linear = calc_coefficients_linear(matrix, responses)

    b_interaction = []
    for j in range(n_factors):
        for k in range(j + 1, n_factors):
            s = sum(matrix[i][j] * matrix[i][k] * responses[i]
                    for i in range(n_runs))
            b_interaction.append(s / n_runs)

    return b0, b_linear, b_interaction


def predict_linear(coded_row, b0, b_linear):
    """Предсказание по линейной модели."""
    return b0 + sum(b_linear[j] * coded_row[j] for j in range(len(b_linear)))


def predict_nonlinear(coded_row, b0, b_linear, b_interaction):
    """Предсказание по частично нелинейной модели."""
    y = predict_linear(coded_row, b0, b_linear)
    terms = compute_interaction_terms(coded_row)
    y += sum(b_interaction[k] * terms[k] for k in range(len(b_interaction)))
    return y


def normalized_equation_str(b0, coeffs, labels):
    """Строковое представление уравнения в нормированных переменных."""
    parts = [f"{b0:.6f}"]
    for c, lbl in zip(coeffs, labels):
        if c >= 0:
            parts.append(f"+ {c:.6f}·{lbl}")
        else:
            parts.append(f"- {abs(c):.6f}·{lbl}")
    return "ŷ = " + " ".join(parts)


def natural_equation_from_normalized(b0, b_linear, b_interaction,
                                      centers, deltas, factor_labels):
    """
    Переводит нормированное уравнение в натуральные переменные.
    x_j = (X_j - center_j) / delta_j  =>  X_j = center_j + delta_j * x_j

    Линейная часть:
    b0 + Σ b_j * x_j = b0 + Σ b_j * (X_j - c_j)/d_j
    = (b0 - Σ b_j*c_j/d_j) + Σ (b_j/d_j) * X_j

    Взаимодействия:
    b_jk * x_j * x_k = b_jk / (d_j * d_k) * (X_j - c_j)(X_k - c_k)
    = b_jk/(d_j*d_k) * (X_j*X_k - c_k*X_j - c_j*X_k + c_j*c_k)
    """
    n = len(b_linear)

    a0 = b0
    a_linear = [0.0] * n
    a_interaction = {}

    # Линейная часть
    for j in range(n):
        a_linear[j] += b_linear[j] / deltas[j]
        a0 -= b_linear[j] * centers[j] / deltas[j]

    # Взаимодействия
    if b_interaction:
        idx = 0
        for j in range(n):
            for k in range(j + 1, n):
                bij = b_interaction[idx]
                dj, dk = deltas[j], deltas[k]
                cj, ck = centers[j], centers[k]

                coeff_jk = bij / (dj * dk)
                a_interaction[(j, k)] = coeff_jk

                a_linear[j] -= bij * ck / (dj * dk)
                a_linear[k] -= bij * cj / (dj * dk)
                a0 += bij * cj * ck / (dj * dk)

                idx += 1

    # Формирование строки
    parts = [f"{a0:.6f}"]
    for j in range(n):
        c = a_linear[j]
        lbl = factor_labels[j]
        if c >= 0:
            parts.append(f"+ {c:.6f}·{lbl}")
        else:
            parts.append(f"- {abs(c):.6f}·{lbl}")

    for (j, k), c in a_interaction.items():
        lbl = f"{factor_labels[j]}·{factor_labels[k]}"
        if c >= 0:
            parts.append(f"+ {c:.6f}·{lbl}")
        else:
            parts.append(f"- {abs(c):.6f}·{lbl}")

    return "ŷ = " + " ".join(parts)


def run_ffe(factor_ranges, response_key='avg_wait', limit_value=10000,
            replications=3):
    """
    Основная функция: проводит ПФЭ 2^6.

    factor_ranges: list of (min_val, max_val) для каждого фактора
    Возвращает словарь со всеми результатами.
    """
    n_factors = len(factor_ranges)
    factor_keys = [f['key'] for f in FACTORS]
    factor_labels = [f['label'] for f in FACTORS]

    centers = [(lo + hi) / 2 for lo, hi in factor_ranges]
    deltas = [(hi - lo) / 2 for lo, hi in factor_ranges]

    matrix = build_design_matrix(n_factors)
    n_runs = len(matrix)

    # Проведение экспериментов
    responses = []
    run_details = []

    for i, coded_row in enumerate(matrix):
        natural = coded_to_natural(coded_row, centers, deltas)
        params = {factor_keys[j]: natural[j] for j in range(n_factors)}
        params['limit_value'] = limit_value

        y = run_simulation_averaged(params, replications, response_key)
        responses.append(y)

        run_details.append({
            'run': i + 1,
            'coded': coded_row,
            'natural': natural,
            'y_experiment': y,
        })

    # Вычисление коэффициентов
    b0_lin, b_lin = calc_coefficients_linear(matrix, responses)
    b0_nl, b_nl, b_inter = calc_coefficients_nonlinear(matrix, responses)

    # Предсказания и погрешности
    for detail in run_details:
        coded = detail['coded']
        y_exp = detail['y_experiment']

        y_lin = predict_linear(coded, b0_lin, b_lin)
        y_nl = predict_nonlinear(coded, b0_nl, b_nl, b_inter)

        detail['y_linear'] = y_lin
        detail['y_nonlinear'] = y_nl
        detail['error_linear'] = abs(y_lin - y_exp)
        detail['error_nonlinear'] = abs(y_nl - y_exp)
        detail['rel_error_linear'] = abs(y_lin - y_exp) / y_exp * 100 if y_exp != 0 else 0
        detail['rel_error_nonlinear'] = abs(y_nl - y_exp) / y_exp * 100 if y_exp != 0 else 0

    # Средние ошибки
    avg_err_lin = sum(d['error_linear'] for d in run_details) / n_runs
    avg_err_nl = sum(d['error_nonlinear'] for d in run_details) / n_runs
    avg_rel_lin = sum(d['rel_error_linear'] for d in run_details) / n_runs
    avg_rel_nl = sum(d['rel_error_nonlinear'] for d in run_details) / n_runs

    # Уравнения в нормированных переменных
    lin_labels = factor_labels
    inter_labels = interaction_labels(factor_labels)

    eq_lin_norm = normalized_equation_str(b0_lin, b_lin, lin_labels)
    eq_nl_norm = normalized_equation_str(
        b0_nl, b_nl + b_inter, lin_labels + inter_labels)

    # Уравнения в натуральных переменных
    eq_lin_nat = natural_equation_from_normalized(
        b0_lin, b_lin, [], centers, deltas, factor_labels)
    eq_nl_nat = natural_equation_from_normalized(
        b0_nl, b_nl, b_inter, centers, deltas, factor_labels)

    # Сравнение в центре плана
    center_params = {factor_keys[j]: centers[j] for j in range(n_factors)}
    center_params['limit_value'] = limit_value
    y_center_real = run_simulation_averaged(center_params, replications, response_key)
    y_center_lin = b0_lin  # при всех x_j = 0 → ŷ = b0
    y_center_nl = b0_nl    # при всех x_j = 0 → ŷ = b0

    return {
        'n_factors': n_factors,
        'n_runs': n_runs,
        'factor_labels': factor_labels,
        'factor_keys': factor_keys,
        'centers': centers,
        'deltas': deltas,
        'factor_ranges': factor_ranges,
        'replications': replications,
        'response_key': response_key,

        'b0_linear': b0_lin,
        'b_linear': b_lin,
        'b0_nonlinear': b0_nl,
        'b_nonlinear': b_nl,
        'b_interaction': b_inter,
        'interaction_labels': inter_labels,

        'eq_linear_norm': eq_lin_norm,
        'eq_nonlinear_norm': eq_nl_norm,
        'eq_linear_nat': eq_lin_nat,
        'eq_nonlinear_nat': eq_nl_nat,

        'run_details': run_details,

        'avg_error_linear': avg_err_lin,
        'avg_error_nonlinear': avg_err_nl,
        'avg_rel_error_linear': avg_rel_lin,
        'avg_rel_error_nonlinear': avg_rel_nl,

        'center_values': centers,
        'center_y_real': y_center_real,
        'center_y_linear': y_center_lin,
        'center_y_nonlinear': y_center_nl,
        'center_error_linear': abs(y_center_lin - y_center_real),
        'center_error_nonlinear': abs(y_center_nl - y_center_real),
    }
