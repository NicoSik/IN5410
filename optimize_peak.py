"""
Question 4: Optimization with Peak Load Minimization.

PROBLEM FORMULATION:
    
    Objective: Minimize  α × Σ(t=0..23) L(t)×P(t)  +  β × L_peak
    
    Where:
        L(t)    = total load at hour t
        P(t)    = price at hour t
        L_peak  = peak load variable (maximum load across all hours)
        α, β    = weighting factors (trade-off between cost and peak)
    
    Subject to:
        1. L(t) ≤ L_peak  for all t ∈ {0, ..., 23}
        2. Each appliance starts within its allowed hours
        3. Each appliance runs for its full duration
        4. Each appliance runs exactly once per day
    
    SOLUTION METHOD:
        Exhaustive search over all possible start time combinations.
        For each combination, compute:
          - total cost = Σ L(t) × P(t)
          - peak load  = max(L(t)) over all t
          - objective  = α × cost + β × peak load
        Select the combination with minimum objective.
    
    COMPARISON WITH Q2:
        Q2 minimizes ONLY cost → may create high peaks in cheap hours
        Q4 minimizes cost + peak → spreads load more evenly (peak shaving)
"""

from typing import Dict, List, Tuple
from itertools import product


def optimize_with_peak_constraint(
    base_load: List[float],
    prices: List[float],
    appliances: List[dict],
    alpha: float = 1.0,
    beta: float = 5.0
) -> Tuple[Dict[str, int], List[float], float, float]:
    """
    Find the schedule that minimizes both energy cost AND peak load.
    
    Objective: minimize  α × total_cost + β × peak_load
    Constraint: L(t) ≤ L_peak for all t
    
    Args:
        base_load: Fixed hourly load from non-shiftable appliances (24 hours)
        prices: Hourly electricity prices (24 hours)
        appliances: List of {name, energy, duration, allowed_hours}
        alpha: Weight for energy cost (default 1.0)
        beta: Weight for peak load penalty (default 5.0)
              Higher β → more peak shaving, potentially higher cost
              Lower β  → less peak shaving, closer to Q2 result
    
    Returns:
        (schedule, final_load, total_cost, peak_load)
        - schedule: {appliance_name: start_hour}
        - final_load: hourly consumption profile (24 hours)
        - total_cost: total daily energy cost (NOK)
        - peak_load: maximum hourly load (kWh)
    """
    best_objective = float('inf')
    best_cost = float('inf')
    best_peak = float('inf')
    best_schedule = {}
    best_load = []
    
    # Get all allowed start times for each appliance
    options = [app['allowed_hours'] for app in appliances]
    
    # Try every combination
    for combination in product(*options):
        # Build load profile for this combination
        load = base_load[:]
        
        for appliance, start_hour in zip(appliances, combination):
            energy_per_hour = appliance['energy'] / appliance['duration']
            
            for hour in range(appliance['duration']):
                h = (start_hour + hour) % 24
                load[h] += energy_per_hour
        
        # Calculate cost and peak load
        cost = sum(load[h] * prices[h] for h in range(24))
        peak = max(load)
        
        # Combined objective: minimize cost AND peak load
        objective = alpha * cost + beta * peak
        
        # Keep if best
        if objective < best_objective:
            best_objective = objective
            best_cost = cost
            best_peak = peak
            best_schedule = {app['name']: start for app, start in zip(appliances, combination)}
            best_load = load
    
    return best_schedule, best_load, best_cost, best_peak


def print_q4_comparison(
    q2_schedule: Dict[str, int],
    q2_load: List[float],
    q2_cost: float,
    q4_schedule: Dict[str, int],
    q4_load: List[float],
    q4_cost: float,
    q4_peak: float,
    shiftable: List[dict] = None
) -> None:
    """Print comparison between Q2 and Q4 results."""
    from helpers import format_schedule
    
    q2_peak = max(q2_load)
    
    print("\n" + "="*70)
    print("QUESTION 4: COMPARISON WITH QUESTION 2")
    print("="*70)
    
    print("\n📋 Q2 Schedule (Cost Only):")
    print(format_schedule(q2_schedule, shiftable))
    
    print(f"\n📋 Q4 Schedule (Cost + Peak Load):")
    print(format_schedule(q4_schedule, shiftable))
    
    print(f"\n📊 Cost Comparison:")
    print(f"  Q2 cost:  {q2_cost:.2f} NOK/day")
    print(f"  Q4 cost:  {q4_cost:.2f} NOK/day")
    cost_diff = q4_cost - q2_cost
    print(f"  Diff:     {cost_diff:+.2f} NOK/day ({'higher' if cost_diff > 0 else 'lower'} in Q4)")
    
    print(f"\n⚡ Peak Load Comparison:")
    print(f"  Q2 peak:  {q2_peak:.2f} kWh")
    print(f"  Q4 peak:  {q4_peak:.2f} kWh")
    peak_reduction = q2_peak - q4_peak
    peak_pct = (peak_reduction / q2_peak * 100) if q2_peak > 0 else 0
    print(f"  Reduction: {peak_reduction:.2f} kWh ({peak_pct:.1f}%)")
    
    print(f"\n📈 Load Distribution:")
    print(f"  {'Hour':>6s}  {'Q2 Load':>10s}  {'Q4 Load':>10s}  {'Diff':>10s}")
    print(f"  {'-'*6}  {'-'*10}  {'-'*10}  {'-'*10}")
    for h in range(24):
        diff = q4_load[h] - q2_load[h]
        marker = " ◄" if abs(diff) > 0.01 else ""
        print(f"  {h:02d}:00   {q2_load[h]:10.3f}  {q4_load[h]:10.3f}  {diff:+10.3f}{marker}")
    
    print(f"\n💡 Key Insight:")
    print(f"  Q2 minimizes ONLY cost → concentrates load in cheapest hours")
    print(f"  → creates peak of {q2_peak:.2f} kWh")
    print(f"  Q4 minimizes cost + peak → spreads load more evenly")
    print(f"  → reduces peak to {q4_peak:.2f} kWh ({peak_pct:.1f}% reduction)")
    if cost_diff > 0:
        print(f"  → trade-off: slightly higher cost (+{cost_diff:.2f} NOK/day)")
    print(f"  → better for grid stability!")
    print("="*70)
