"""Question 1 optimizer — Pure Linear Program (LP).

Only three appliances: Washing Machine (Laundry), EV, Dishwasher.
ToU pricing: 0.5 NOK/kWh off-peak, 1.0 NOK/kWh peak (17:00-20:00).

Only two constraints per appliance:
    1. Energy equality:   sum_i e_{j,i} = E_j
    2. Power bounds:      0 <= e_{j,i} <= P_j^max

No contiguous-block / binary start-time constraints — appliances
may spread their energy freely across any hours.
"""
from typing import Dict, List, Tuple
import numpy as np
from scipy.optimize import linprog


def get_q1_prices() -> List[float]:
    """
    Time-of-Use pricing for Question 1.
    
    Peak hours (17:00-20:00): 1.0 NOK/kWh
    Off-peak (all other hours): 0.5 NOK/kWh
    """
    prices = []
    for h in range(24):
        if 17 <= h <= 19:  # 17:00, 18:00, 19:00 (i.e. 17:00-20:00)
            prices.append(1.0)
        else:
            prices.append(0.5)
    return prices


def get_q1_appliances() -> List[dict]:
    """
    Three shiftable appliances for Question 1.
    
    Uses the same energy and p_max values as in data_setup.py.
    Allowed hours: all 24 hours (no time-window restriction in Q1).
    """
    return [
        {
            'name': 'Dishwasher',
            'energy': 1.44,   # kWh total
            'p_max': 0.8,     # kW max power per hour
        },
        {
            'name': 'Washing Machine',
            'energy': 1.94,   # kWh total
            'p_max': 1.1,     # kW max power per hour
        },
        {
            'name': 'EV Charging',
            'energy': 9.90,   # kWh total
            'p_max': 3.0,     # kW max power per hour
        },
    ]


def optimize_q1(
    prices: List[float],
    appliances: List[dict],
) -> Tuple[Dict[str, list], List[float], float]:
    """
    Find the cheapest schedule using a continuous LP.

    Decision variables:
        e[j, i] >= 0  — energy (power) drawn by appliance j at hour i

    Constraints:
        (1) Energy equality:  sum_{i=0}^{23} e[j,i] = E_j   for each j
        (2) Power bounds:     0 <= e[j,i] <= P_j^max         for each j, i

    Objective:
        min  sum_j sum_i  price[i] * e[j,i]

    Args:
        prices:     24-element list of hourly prices (NOK/kWh)
        appliances: list of {name, energy, p_max}

    Returns:
        (schedule, total_load, total_cost)
        - schedule:   {name: [e_0 ... e_23]}  power profile per appliance
        - total_load: 24-element combined load
        - total_cost: total daily cost (NOK)
    """
    n_apps = len(appliances)
    H = 24

    # Variable layout: e[j,i] at index j*24 + i
    n_vars = n_apps * H

    def idx(j: int, i: int) -> int:
        return j * H + i

    # ── Cost vector ───────────────────────────────────────────────
    c = np.zeros(n_vars)
    for j in range(n_apps):
        for i in range(H):
            c[idx(j, i)] = prices[i]

    # ── Bounds: 0 <= e[j,i] <= P_j^max  (Constraint 2) ──────────
    bounds = []
    for j in range(n_apps):
        p_max = appliances[j]['p_max']
        for i in range(H):
            bounds.append((0.0, p_max))

    # ── Equality constraints: sum_i e[j,i] = E_j  (Constraint 1) ─
    A_eq = np.zeros((n_apps, n_vars))
    b_eq = np.zeros(n_apps)
    for j in range(n_apps):
        for i in range(H):
            A_eq[j, idx(j, i)] = 1.0
        b_eq[j] = appliances[j]['energy']

    # ── Solve LP ──────────────────────────────────────────────────
    result = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')

    if not result.success:
        raise RuntimeError(f"LP solver failed: {result.message}")

    x = result.x

    # ── Extract results ───────────────────────────────────────────
    schedule: Dict[str, list] = {}
    total_load = np.zeros(H)

    for j, app in enumerate(appliances):
        profile = [x[idx(j, i)] for i in range(H)]
        schedule[app['name']] = profile
        total_load += np.array(profile)

    total_cost = sum(prices[i] * total_load[i] for i in range(H))

    return schedule, total_load.tolist(), total_cost
