# -*- coding: utf-8 -*-

import random


class Request:
    def __init__(self, request_type: int, arrival_time: float):
        self.type = request_type
        self.arrival_time = arrival_time


class Simulation:
    """
    Одноканальная СМО с двумя типами заявок.
    Относительные приоритеты, нормальное поступление, экспоненциальное обслуживание.
    """

    def __init__(self, lambda1, sigma1, lambda2, sigma2, mu1, mu2,
                 limit_value=10000):
        self.lambda1, self.sigma1 = lambda1, sigma1
        self.lambda2, self.sigma2 = lambda2, sigma2
        self.mu1, self.mu2 = mu1, mu2
        self.limit_value = limit_value

        self.current_time = 0.0
        self.server_busy = False
        self.queue = []
        self.current_request = None

        self.next_arrival1 = self._gen_interarrival(lambda1, sigma1)
        self.next_arrival2 = self._gen_interarrival(lambda2, sigma2)
        self.service_end = float('inf')

        self.stats = {
            'wait_time_1': 0.0, 'wait_time_2': 0.0,
            'service_time_1': 0.0, 'service_time_2': 0.0,
            'served_1': 0, 'served_2': 0,
            'generated_1': 0, 'generated_2': 0,
            'busy_time': 0.0
        }

    def _gen_interarrival(self, lam, sigma):
        if lam <= 0:
            return float('inf')
        mean = 1.0 / lam
        val = random.gauss(mean, sigma)
        while val <= 0:
            val = random.gauss(mean, sigma)
        return val

    def _gen_service_time(self, req_type):
        mu = self.mu1 if req_type == 1 else self.mu2
        if mu <= 0:
            return float('inf')
        return random.expovariate(mu)

    def run(self):
        while self.stats['served_1'] + self.stats['served_2'] < self.limit_value:
            candidates = [self.service_end, self.next_arrival1, self.next_arrival2]
            next_event = min(candidates)

            if next_event == float('inf'):
                break

            if self.server_busy:
                self.stats['busy_time'] += next_event - self.current_time
            self.current_time = next_event

            if self.current_time == self.next_arrival1:
                self._handle_arrival(1)
            elif self.current_time == self.next_arrival2:
                self._handle_arrival(2)
            elif self.current_time == self.service_end:
                self._handle_service_completion()

        return self._calculate_results()

    def _handle_arrival(self, req_type):
        req = Request(req_type, self.current_time)
        if req_type == 1:
            self.stats['generated_1'] += 1
        else:
            self.stats['generated_2'] += 1

        if not self.server_busy:
            self.server_busy = True
            self.current_request = req
            st = self._gen_service_time(req_type)
            self.service_end = self.current_time + st
            if req_type == 1:
                self.stats['served_1'] += 1
                self.stats['service_time_1'] += st
            else:
                self.stats['served_2'] += 1
                self.stats['service_time_2'] += st
        else:
            if req_type == 1:
                pos = 0
                for i, r in enumerate(self.queue):
                    if r.type == 2:
                        pos = i
                        break
                    pos = i + 1
                self.queue.insert(pos, req)
            else:
                self.queue.append(req)

        if req_type == 1:
            self.next_arrival1 = self.current_time + self._gen_interarrival(
                self.lambda1, self.sigma1)
        else:
            self.next_arrival2 = self.current_time + self._gen_interarrival(
                self.lambda2, self.sigma2)

    def _handle_service_completion(self):
        if not self.queue:
            self.server_busy = False
            self.current_request = None
            self.service_end = float('inf')
        else:
            req = self.queue.pop(0)
            self.current_request = req
            wt = self.current_time - req.arrival_time
            st = self._gen_service_time(req.type)
            self.service_end = self.current_time + st
            if req.type == 1:
                self.stats['wait_time_1'] += wt
                self.stats['served_1'] += 1
                self.stats['service_time_1'] += st
            else:
                self.stats['wait_time_2'] += wt
                self.stats['served_2'] += 1
                self.stats['service_time_2'] += st

    def _calculate_results(self):
        s1 = self.stats['served_1']
        s2 = self.stats['served_2']
        total = s1 + s2

        avg_w1 = self.stats['wait_time_1'] / s1 if s1 else 0
        avg_w2 = self.stats['wait_time_2'] / s2 if s2 else 0
        avg_s1 = self.stats['service_time_1'] / s1 if s1 else 0
        avg_s2 = self.stats['service_time_2'] / s2 if s2 else 0

        total_wait = self.stats['wait_time_1'] + self.stats['wait_time_2']
        total_service = self.stats['service_time_1'] + self.stats['service_time_2']

        avg_wait = total_wait / total if total else 0
        avg_sojourn = (total_wait + total_service) / total if total else 0

        return {
            'avg_wait': avg_wait,
            'avg_sojourn': avg_sojourn,
            'avg_wait_1': avg_w1, 'avg_wait_2': avg_w2,
            'avg_sojourn_1': avg_w1 + avg_s1, 'avg_sojourn_2': avg_w2 + avg_s2,
            'served_1': s1, 'served_2': s2, 'total_served': total,
            'actual_load': self.stats['busy_time'] / self.current_time if self.current_time > 0 else 0,
        }


def run_simulation_averaged(params, replications=3, response_key='avg_wait'):
    results = []
    for _ in range(replications):
        sim = Simulation(**params)
        r = sim.run()
        results.append(r[response_key])
    return sum(results) / len(results)
