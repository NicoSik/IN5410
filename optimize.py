"""Core optimization — MILP solver (Mixed-Integer Linear Program).

Combines continuous power variables with binary start-time selectors
to enforce contiguous operation of each appliance.
"""
from typing import Dict, List, Tuple
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint


def optimize(
    base_load: List[float],
    prices: List[float],
    appliances: List[dict]
) -> Tuple[Dict[str, list], List[float], float]:
    """
    Find the cheapest schedule for shiftable appliances using MILP.

    Formulation (Mixed-Integer Linear Program):

    Decision variables:
        p[a,h] ≥ 0  (continuous) — power drawn by appliance a at hour h
        y[a,s] ∈ {0,1} (binary) — 1 if appliance a starts at hour s

    Constraints:
        1. Exactly one start time per appliance:
           ∑_s y[a,s] = 1

        2. Energy requirement:
           ∑_h p[a,h] = E_a

        3. Power bounds (links p to y — contiguous operation):
           p[a,h] ≤ P_max_a · ∑_{s : h ∈ block(s)} y[a,s]

           i.e. power at hour h can only be nonzero if h falls inside
           the active block of a selected start time.

    Objective:
        min ∑_a ∑_h price[h] · p[a,h]

    This gives continuous power modulation within a forced contiguous
    block of 'duration' hours, solved with scipy.optimize.milp.

    Args:
        base_load: Fixed hourly load (24 hours)
        prices: Hourly spot prices (24 hours)
        appliances: List of {name, energy, duration, p_max, allowed_hours}

    Returns:
        (schedule, final_load, total_cost)
        - schedule: {name: [p_0 … p_23]} power profile per appliance
        - final_load: total hourly consumption (24 hours)
        - total_cost: total daily cost
    """
    n_apps = len(appliances)
    H = 24

    # ── Variable layout ───────────────────────────────────────────
    # p[a,h]: continuous — n_apps * 24 variables (indices 0 .. n_apps*24 - 1)
    # y[a,s]: binary     — one per (appliance, allowed_start)
    #
    n_p = n_apps * H
    # Build list of (appliance_idx, start_hour) for y variables
    y_info: list[tuple[int, int]] = []
    for a, app in enumerate(appliances):
        for s in app['allowed_hours']:
            y_info.append((a, s))
    n_y = len(y_info)
    n_vars = n_p + n_y

    def p_idx(a: int, h: int) -> int:
        return a * H + h

    def y_idx(v: int) -> int:
        return n_p + v

    # ── Cost vector ───────────────────────────────────────────────
    # Only p variables contribute to cost; y variables have zero cost
    c = np.zeros(n_vars)
    for a in range(n_apps):
        for h in range(H):
            c[p_idx(a, h)] = prices[h]

    # ── Integrality: p = continuous (0), y = integer (1) ──────────
    integrality = np.zeros(n_vars)
    for v in range(n_y):
        integrality[y_idx(v)] = 1

    # ── Bounds ────────────────────────────────────────────────────
    lb = np.zeros(n_vars)
    ub = np.zeros(n_vars)

    # p[a,h]: upper bound = p_max (will be tightened by linking constraints)
    for a, app in enumerate(appliances):
        p_max = app.get('p_max', app['energy'] / app['duration'])
        for h in range(H):
            ub[p_idx(a, h)] = p_max

    # y[a,s]: binary 0/1
    for v in range(n_y):
        ub[y_idx(v)] = 1.0

    # ── Equality constraints ──────────────────────────────────────
    eq_rows = []
    eq_rhs = []

    # (A) ∑_s y[a,s] = 1 for each appliance
    for a, app in enumerate(appliances):
        row = np.zeros(n_vars)
        for v, (a2, s) in enumerate(y_info):
            if a2 == a:
                row[y_idx(v)] = 1.0
        eq_rows.append(row)
        eq_rhs.append(1.0)

    # (B) ∑_h p[a,h] = E_a for each appliance
    for a, app in enumerate(appliances):
        row = np.zeros(n_vars)
        for h in range(H):
            row[p_idx(a, h)] = 1.0
        eq_rows.append(row)
        eq_rhs.append(app['energy'])

    A_eq = np.array(eq_rows)
    b_eq = np.array(eq_rhs)

    # ── Inequality constraints: p[a,h] ≤ P_max · ∑ y[a,s] where h ∈ block(s)
    # Rewritten as: p[a,h] - P_max · ∑ y[a,s:{h in block}] ≤ 0
    ineq_rows = []
    ineq_ub = []

    for a, app in enumerate(appliances):
        p_max = app.get('p_max', app['energy'] / app['duration'])
        dur = app['duration']
        allowed_set = set(app['allowed_hours'])

        for h in range(H):
            # Find all y[a,s] whose block covers hour h
            # block(s) = {s, s+1, ..., s+dur-1} mod 24
            covering_y = []
            for v, (a2, s) in enumerate(y_info):
                if a2 != a:
                    continue
                block = set((s + d) % H for d in range(dur))
                if h in block:
                    covering_y.append(v)

            # If no y covers this hour → p[a,h] must be 0
            # (already handled: ub will effectively be 0 from constraint)
            row = np.zeros(n_vars)
            row[p_idx(a, h)] = 1.0
            for v in covering_y:
                row[y_idx(v)] = -p_max
            ineq_rows.append(row)
            ineq_ub.append(0.0)

    A_ineq = np.array(ineq_rows)
    b_ineq = np.array(ineq_ub)

    # ── Combine constraints ───────────────────────────────────────
    constraints = [
        LinearConstraint(A_eq, b_eq, b_eq),          # equalities
        LinearConstraint(A_ineq, -np.inf, b_ineq),   # p ≤ P_max·y
    ]

    # ── Solve ─────────────────────────────────────────────────────
    result = milp(
        c=c,
        constraints=constraints,
        integrality=integrality,
        bounds=Bounds(lb=lb, ub=ub),
    )

    if not result.success:
        raise RuntimeError(f"MILP solver failed: {result.message}")

    x = result.x

    # ── Extract results ───────────────────────────────────────────
    schedule: Dict[str, list] = {}
    final_load = list(base_load)

    for a, app in enumerate(appliances):
        power_profile = [max(0.0, x[p_idx(a, h)]) for h in range(H)]
        # Zero out negligible values
        power_profile = [p if p > 1e-6 else 0.0 for p in power_profile]
        schedule[app['name']] = power_profile
        for h in range(H):
            final_load[h] += power_profile[h]

    total_cost = sum(final_load[h] * prices[h] for h in range(H))

    return schedule, final_load, total_cost
