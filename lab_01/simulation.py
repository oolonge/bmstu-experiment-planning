# -*- coding: utf-8 -*-

import random
import numpy as np
from constants import MAX_RHO, PLOT_STEPS, PLOT_RUNS_PER_POINT


class Request:
    def __init__(self, request_type: int, arrival_time: float):
        self.type = request_type
        self.arrival_time = arrival_time


class Simulation:
    """
    Имитационная модель одноканальной СМО.
    Буфер бесконечный, дисциплина с относительными приоритетами.
    Тип 1 — высокий приоритет, тип 2 — низкий.
    Поступление — нормальный закон, обслуживание — экспоненциальный.
    """

    def __init__(self, lambda1: float, sigma1: float,
                 lambda2: float, sigma2: float,
                 mu1: float, mu2: float,
                 limit_type: str = 'time',
                 limit_value: float = 1000):
        self.lambda1, self.sigma1 = lambda1, sigma1
        self.lambda2, self.sigma2 = lambda2, sigma2
        self.mu1, self.mu2 = mu1, mu2

        self.limit_type = limit_type
        self.limit_value = limit_value

        self.current_time = 0.0
        self.server_busy = False
        self.queue = []
        self.current_request = None

        self.next_arrival1 = self._gen_interarrival_time(lambda1, sigma1)
        self.next_arrival2 = self._gen_interarrival_time(lambda2, sigma2)
        self.service_end = float('inf')

        self.stats = {
            'wait_time_1': 0.0, 'wait_time_2': 0.0,
            'service_time_1': 0.0, 'service_time_2': 0.0,
            'served_1': 0, 'served_2': 0,
            'generated_1': 0, 'generated_2': 0,
            'busy_time': 0.0
        }

    def _gen_interarrival_time(self, lam: float, sigma: float) -> float:
        if lam <= 0:
            return float('inf')
        mean = 1.0 / lam
        val = random.gauss(mean, sigma)
        while val <= 0:
            val = random.gauss(mean, sigma)
        return val

    def _gen_service_time(self, request_type: int) -> float:
        mu = self.mu1 if request_type == 1 else self.mu2
        if mu <= 0:
            return float('inf')
        return random.expovariate(mu)

    def _should_continue(self) -> bool:
        if self.limit_type == 'time':
            return self.current_time < self.limit_value
        elif self.limit_type == 'served':
            total_served = self.stats['served_1'] + self.stats['served_2']
            return total_served < self.limit_value
        else:
            total_generated = self.stats['generated_1'] + self.stats['generated_2']
            if total_generated < self.limit_value:
                return True
            return self.server_busy or len(self.queue) > 0

    def _should_generate(self) -> bool:
        if self.limit_type != 'generated':
            return True
        total_generated = self.stats['generated_1'] + self.stats['generated_2']
        return total_generated < self.limit_value

    def run(self) -> dict:
        while self._should_continue():
            candidates = [self.service_end]

            if self._should_generate():
                candidates.extend([self.next_arrival1, self.next_arrival2])

            next_event = min(candidates)

            if next_event == float('inf'):
                break

            if self.limit_type == 'time' and next_event > self.limit_value:
                if self.server_busy:
                    self.stats['busy_time'] += self.limit_value - self.current_time
                self.current_time = self.limit_value
                break

            if self.server_busy:
                self.stats['busy_time'] += next_event - self.current_time

            self.current_time = next_event

            if self.current_time == self.next_arrival1 and self._should_generate():
                self._handle_arrival(1)
            elif self.current_time == self.next_arrival2 and self._should_generate():
                self._handle_arrival(2)
            elif self.current_time == self.service_end:
                self._handle_service_completion()

        return self._calculate_results()

    def _handle_arrival(self, req_type: int):
        new_request = Request(req_type, self.current_time)

        if req_type == 1:
            self.stats['generated_1'] += 1
        else:
            self.stats['generated_2'] += 1

        if not self.server_busy:
            self.server_busy = True
            self.current_request = new_request
            service_time = self._gen_service_time(req_type)
            self.service_end = self.current_time + service_time

            if req_type == 1:
                self.stats['served_1'] += 1
                self.stats['service_time_1'] += service_time
            else:
                self.stats['served_2'] += 1
                self.stats['service_time_2'] += service_time
        else:
            # Относительный приоритет: тип 1 вставляется перед типом 2
            if req_type == 1:
                insert_pos = 0
                for i, r in enumerate(self.queue):
                    if r.type == 2:
                        insert_pos = i
                        break
                    insert_pos = i + 1
                self.queue.insert(insert_pos, new_request)
            else:
                self.queue.append(new_request)

        if self._should_generate():
            if req_type == 1:
                self.next_arrival1 = self.current_time + self._gen_interarrival_time(
                    self.lambda1, self.sigma1)
            else:
                self.next_arrival2 = self.current_time + self._gen_interarrival_time(
                    self.lambda2, self.sigma2)
        else:
            if req_type == 1:
                self.next_arrival1 = float('inf')
            else:
                self.next_arrival2 = float('inf')

    def _handle_service_completion(self):
        if not self.queue:
            self.server_busy = False
            self.current_request = None
            self.service_end = float('inf')
        else:
            next_request = self.queue.pop(0)
            self.current_request = next_request
            wait_time = self.current_time - next_request.arrival_time
            service_time = self._gen_service_time(next_request.type)
            self.service_end = self.current_time + service_time

            if next_request.type == 1:
                self.stats['wait_time_1'] += wait_time
                self.stats['served_1'] += 1
                self.stats['service_time_1'] += service_time
            else:
                self.stats['wait_time_2'] += wait_time
                self.stats['served_2'] += 1
                self.stats['service_time_2'] += service_time

    def _calculate_results(self) -> dict:
        served1 = self.stats['served_1']
        served2 = self.stats['served_2']

        avg_wait_1 = self.stats['wait_time_1'] / served1 if served1 > 0 else 0
        avg_wait_2 = self.stats['wait_time_2'] / served2 if served2 > 0 else 0
        avg_service_1 = self.stats['service_time_1'] / served1 if served1 > 0 else 0
        avg_service_2 = self.stats['service_time_2'] / served2 if served2 > 0 else 0
        avg_sojourn_1 = avg_wait_1 + avg_service_1
        avg_sojourn_2 = avg_wait_2 + avg_service_2

        actual_load = self.stats['busy_time'] / self.current_time if self.current_time > 0 else 0

        if self.mu1 > 0 and self.mu2 > 0:
            theoretical_load = self.lambda1 / self.mu1 + self.lambda2 / self.mu2
        else:
            theoretical_load = 0.0

        return {
            'served_1': served1, 'served_2': served2,
            'avg_wait_1': avg_wait_1, 'avg_wait_2': avg_wait_2,
            'avg_sojourn_1': avg_sojourn_1, 'avg_sojourn_2': avg_sojourn_2,
            'actual_load': actual_load, 'theoretical_load': theoretical_load,
            'generated_1': self.stats['generated_1'],
            'generated_2': self.stats['generated_2'],
            'total_time': self.current_time,
            'total_served': served1 + served2,
            'total_generated': self.stats['generated_1'] + self.stats['generated_2'],
            'queue_left': len(self.queue)
        }


def calc_rho(lambda1, lambda2, mu1, mu2):
    rho1 = lambda1 / mu1 if mu1 > 0 else float('inf')
    rho2 = lambda2 / mu2 if mu2 > 0 else float('inf')
    return rho1 + rho2


def validate_params(lam: float, sigma: float, type_num: int):
    if lam <= 0:
        return
    mean = 1.0 / lam
    if sigma >= mean / 3:
        raise ValueError(
            f"Тип {type_num}: СКО={sigma:.4f} слишком велико для λ={lam:.4f}\n"
            f"Среднее={mean:.4f}, рекомендуемое макс. СКО: {mean / 3:.4f}"
        )


def build_single_plot(values, params_base, updater_func, x_func, title, xlabel):
    x_vals, y1_vals, y2_vals = [], [], []

    for val in values:
        if val <= 0:
            continue

        params = params_base.copy()
        updater_func(params, val)

        rho_total = calc_rho(params['lambda1'], params['lambda2'],
                             params['mu1'], params['mu2'])
        if rho_total >= 1.0:
            continue

        try:
            validate_params(params['lambda1'], params['sigma1'], 1)
            validate_params(params['lambda2'], params['sigma2'], 2)

            # Усреднение по нескольким прогонам
            w1_runs, w2_runs, x_runs = [], [], []
            for _ in range(PLOT_RUNS_PER_POINT):
                sim = Simulation(
                    lambda1=params['lambda1'], sigma1=params['sigma1'],
                    lambda2=params['lambda2'], sigma2=params['sigma2'],
                    mu1=params['mu1'], mu2=params['mu2'],
                    limit_type=params['limit_type'],
                    limit_value=params['limit_value']
                )
                results = sim.run()
                w1_runs.append(results['avg_wait_1'])
                w2_runs.append(results['avg_wait_2'])
                x_runs.append(x_func(params, results))

            x_vals.append(np.mean(x_runs))
            y1_vals.append(np.mean(w1_runs))
            y2_vals.append(np.mean(w2_runs))
        except ValueError:
            continue

    return {'x': x_vals, 'y1': y1_vals, 'y2': y2_vals,
            'title': title, 'xlabel': xlabel}


def build_all_plots(params_base: dict) -> list:
    plots = []

    lambda1_base = params_base['lambda1']
    lambda2_base = params_base['lambda2']
    mu1_base = params_base['mu1']
    mu2_base = params_base['mu2']
    sigma1_base = params_base['sigma1']
    sigma2_base = params_base['sigma2']

    rho1_base = lambda1_base / mu1_base if mu1_base > 0 else 0
    rho2_base = lambda2_base / mu2_base if mu2_base > 0 else 0

    # 1. От суммарной загрузки R
    def updater_r(p, val):
        rho_base = calc_rho(lambda1_base, lambda2_base, mu1_base, mu2_base)
        if rho_base > 0:
            k = val / rho_base
            p['lambda1'] = lambda1_base * k
            p['lambda2'] = lambda2_base * k
            if k > 0:
                p['sigma1'] = sigma1_base / k
                p['sigma2'] = sigma2_base / k

    plots.append(build_single_plot(
        np.linspace(0.1, MAX_RHO, PLOT_STEPS), params_base, updater_r,
        lambda p, r: r['theoretical_load'],
        "Зависимость от суммарной загрузки R", "Загрузка R"
    ))

    # 2. От ρ₁ = λ₁/μ₁
    max_rho1 = MAX_RHO - rho2_base
    if max_rho1 > 0.05:
        def updater_rho1(p, val):
            new_lambda1 = val * mu1_base
            k = new_lambda1 / lambda1_base if lambda1_base > 0 else 1
            p['lambda1'] = new_lambda1
            if k > 0:
                p['sigma1'] = sigma1_base / k

        plots.append(build_single_plot(
            np.linspace(0.05, max_rho1, PLOT_STEPS), params_base, updater_rho1,
            lambda p, r: p['lambda1'] / p['mu1'],
            f"Зависимость от загрузки ρ₁ = λ₁/μ₁ (ρ₂={rho2_base:.2f} фикс.)",
            "Загрузка ρ₁"
        ))

    # 3. От λ₁
    max_lambda1 = (MAX_RHO - rho2_base) * mu1_base
    if max_lambda1 > 0.1:
        def updater_lambda1(p, val):
            k = val / lambda1_base if lambda1_base > 0 else 1
            p['lambda1'] = val
            if k > 0:
                p['sigma1'] = sigma1_base / k

        plots.append(build_single_plot(
            np.linspace(0.1, max_lambda1, PLOT_STEPS), params_base, updater_lambda1,
            lambda p, r: p['lambda1'],
            "Зависимость от интенсивности λ₁", "Интенсивность λ₁"
        ))

    # 4. От λ₂
    max_lambda2 = (MAX_RHO - rho1_base) * mu2_base
    if max_lambda2 > 0.1:
        def updater_lambda2(p, val):
            k = val / lambda2_base if lambda2_base > 0 else 1
            p['lambda2'] = val
            if k > 0:
                p['sigma2'] = sigma2_base / k

        plots.append(build_single_plot(
            np.linspace(0.1, max_lambda2, PLOT_STEPS), params_base, updater_lambda2,
            lambda p, r: p['lambda2'],
            "Зависимость от интенсивности λ₂", "Интенсивность λ₂"
        ))

    # 5. От μ₁
    min_mu1 = lambda1_base / (MAX_RHO - rho2_base) if (MAX_RHO - rho2_base) > 0 else lambda1_base * 2
    min_mu1 = max(min_mu1 * 1.05, 0.5)

    def updater_mu1(p, val):
        p['mu1'] = val

    plots.append(build_single_plot(
        np.linspace(min_mu1, min_mu1 * 4, PLOT_STEPS), params_base, updater_mu1,
        lambda p, r: p['mu1'],
        "Зависимость от интенсивности μ₁", "Интенсивность μ₁"
    ))

    # 6. От μ₂
    min_mu2 = lambda2_base / (MAX_RHO - rho1_base) if (MAX_RHO - rho1_base) > 0 else lambda2_base * 2
    min_mu2 = max(min_mu2 * 1.05, 0.5)

    def updater_mu2(p, val):
        p['mu2'] = val

    plots.append(build_single_plot(
        np.linspace(min_mu2, min_mu2 * 4, PLOT_STEPS), params_base, updater_mu2,
        lambda p, r: p['mu2'],
        "Зависимость от интенсивности μ₂", "Интенсивность μ₂"
    ))

    return plots
