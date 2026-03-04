"""
Question 4: Optimization with Peak Load Minimization - MILP solver.

Same MILP structure as Q2 (optimize.py) with one addition:
  - An auxiliary L_peak variable
  - Peak-bound constraints: base[h] + sum_a p[a,h] <= L_peak
  - Objective: min sum_h price[h]*sum_a p[a,h] + lambda*L_peak
"""

from typing import Dict, List, Tuple
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint


def optimize_with_peak_constraint(
    base_load: List[float],
    prices: List[float],
    appliances: List[dict],
    lambda_: float = 5.0
) -> Tuple[Dict[str, list], List[float], float, float]:
    """
    Find the schedule that minimises cost + lambda * peak_load via MILP.

    Returns:
        (schedule, final_load, total_cost, peak_load)
    """
    n_apps = len(appliances)
    H = 24

    # Variable layout:
    #   p[a,h]  : 0 ... n_apps*24-1        (continuous)
    #   y[a,s]  : n_p ... n_p+n_y-1        (binary)
    #   L_peak  : n_p+n_y                  (continuous)
    n_p = n_apps * H

    y_info = []
    for a, app in enumerate(appliances):
        for s in app['allowed_hours']:
            y_info.append((a, s))
    n_y = len(y_info)

    peak_var = n_p + n_y
    n_vars = n_p + n_y + 1

    def p_idx(a, h):
        return a * H + h

    def y_idx(v):
        return n_p + v

    # Cost vector
    c = np.zeros(n_vars)
    for a in range(n_apps):
        for h in range(H):
            c[p_idx(a, h)] = prices[h]
    c[peak_var] = lambda_

    # Integrality
    integrality = np.zeros(n_vars)
    for v in range(n_y):
        integrality[y_idx(v)] = 1

    # Bounds
    lb = np.zeros(n_vars)
    ub = np.full(n_vars, np.inf)

    for a, app in enumerate(appliances):
        p_max = app.get('p_max', app['energy'] / app['duration'])
        for h in range(H):
            ub[p_idx(a, h)] = p_max

    for v in range(n_y):
        ub[y_idx(v)] = 1.0

    ub[peak_var] = sum(app['energy'] for app in appliances) + max(base_load)

    # Equality constraints
    eq_rows = []
    eq_rhs = []

    # (A) sum_s y[a,s] = 1
    for a in range(n_apps):
        row = np.zeros(n_vars)
        for v, (a2, _) in enumerate(y_info):
            if a2 == a:
                row[y_idx(v)] = 1.0
        eq_rows.append(row)
        eq_rhs.append(1.0)

    # (B) sum_h p[a,h] = E_a
    for a, app in enumerate(appliances):
        row = np.zeros(n_vars)
        for h in range(H):
            row[p_idx(a, h)] = 1.0
        eq_rows.append(row)
        eq_rhs.append(app['energy'])

    A_eq = np.array(eq_rows)
    b_eq = np.array(eq_rhs)

    # Inequality constraints
    ineq_rows = []
    ineq_ub_list = []

    # (C) Linking: p[a,h] - P_max * sum_{y covering h} y[a,s] <= 0
    for a, app in enumerate(appliances):
        p_max = app.get('p_max', app['energy'] / app['duration'])
        dur = app['duration']
        for h in range(H):
            covering = []
            for v, (a2, s) in enumerate(y_info):
                if a2 != a:
                    continue
                block = set((s + d) % H for d in range(dur))
                if h in block:
                    covering.append(v)
            row = np.zeros(n_vars)
            row[p_idx(a, h)] = 1.0
            for v in covering:
                row[y_idx(v)] = -p_max
            ineq_rows.append(row)
            ineq_ub_list.append(0.0)

    # (D) Peak bound: sum_a p[a,h] - L_peak <= -base[h]
    for h in range(H):
        row = np.zeros(n_vars)
        for a in range(n_apps):
            row[p_idx(a, h)] = 1.0
        row[peak_var] = -1.0
        ineq_rows.append(row)
        ineq_ub_list.append(-base_load[h])

    A_ineq = np.array(ineq_rows)
    b_ineq = np.array(ineq_ub_list)

    # Solve
    constraints = [
        LinearConstraint(A_eq, b_eq, b_eq),
        LinearConstraint(A_ineq, -np.inf, b_ineq),
    ]

    result = milp(
        c=c,
        constraints=constraints,
        integrality=integrality,
        bounds=Bounds(lb=lb, ub=ub),
    )

    if not result.success:
        raise RuntimeError(f"MILP solver failed: {result.message}")

    x = result.x

    # Extract results
    schedule = {}
    final_load = list(base_load)

    for a, app in enumerate(appliances):
        profile = [max(0.0, x[p_idx(a, h)]) for h in range(H)]
        profile = [p if p > 1e-6 else 0.0 for p in profile]
        schedule[app['name']] = profile
        for h in range(H):
            final_load[h] += profile[h]

    total_cost = sum(final_load[h] * prices[h] for h in range(H))
    peak_load = max(final_load)

    return schedule, final_load, total_cost, peak_load


def print_q4_comparison(
    q2_schedule, q2_load, q2_cost,
    q4_schedule, q4_load, q4_cost, q4_peak,
    shiftable=None
):
    """Print comparison between Q2 and Q4 results."""
    from helpers import format_schedule

    q2_peak = max(q2_load)

    print("\n" + "=" * 70)
    print("QUESTION 4: COMPARISON WITH QUESTION 2")
    print("=" * 70)

    print("\nQ2 Schedule (Cost Only):")
    print(format_schedule(q2_schedule, shiftable))

    print("\nQ4 Schedule (Cost + Peak Load):")
    print(format_schedule(q4_schedule, shiftable))

    print("\nCost Comparison:")
    print(f"  Q2 cost:  {q2_cost:.2f} NOK/day")
    print(f"  Q4 cost:  {q4_cost:.2f} NOK/day")
    cost_diff = q4_cost - q2_cost
    print(f"  Diff:     {cost_diff:+.2f} NOK/day ({'higher' if cost_diff > 0 else 'lower'} in Q4)")

    print("\nPeak Load Comparison:")
    print(f"  Q2 peak:  {q2_peak:.2f} kWh")
    print(f"  Q4 peak:  {q4_peak:.2f} kWh")
    peak_reduction = q2_peak - q4_peak
    peak_pct = (peak_reduction / q2_peak * 100) if q2_peak > 0 else 0
    print(f"  Reduction: {peak_reduction:.2f} kWh ({peak_pct:.1f}%)")

    print("\nLoad Distribution:")
    print(f"  {'Hour':>6s}  {'Q2 Load':>10s}  {'Q4 Load':>10s}  {'Diff':>10s}")
    print(f"  {'------':6s}  {'----------':10s}  {'----------':10s}  {'----------':10s}")
    for h in range(24):
        diff = q4_load[h] - q2_load[h]
        marker = " <" if abs(diff) > 0.01 else ""
        print(f"  {h:02d}:00   {q2_load[h]:10.3f}  {q4_load[h]:10.3f}  {diff:+10.3f}{marker}")

    print(f"\nKey Insight:")
    print(f"  Q2 minimizes ONLY cost -> concentrates load in cheapest hours")
    print(f"  -> creates peak of {q2_peak:.2f} kWh")
    print(f"  Q4 minimizes cost + peak -> spreads load more evenly")
    print(f"  -> reduces peak to {q4_peak:.2f} kWh ({peak_pct:.1f}% reduction)")
    print(f"  -> trade-off: slightly higher cost ({cost_diff:+.2f} NOK/day)")
    print(f"  -> better for grid stability!")
    print("=" * 70)
