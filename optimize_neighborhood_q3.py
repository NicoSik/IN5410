"""Neighborhood optimization (Question 3)."""
from typing import List, Dict, Tuple
from optimize import optimize
from helpers import calculate_cost


def optimize_neighborhood(
    households: List[Dict],
    prices: List[float]
) -> Tuple[Dict[int, Dict], List[float], float]:
    """
    Optimize all households in the neighborhood.
    
    This approach optimizes each household independently.
    
    Args:
        households: List of household configurations
        prices: Hourly electricity prices
    
    Returns:
        (schedules, total_load, total_cost)
        - schedules: {household_id: {appliance_name: start_hour}}
        - total_load: aggregated hourly load for entire neighborhood
        - total_cost: total daily cost for the neighborhood
    """
    all_schedules = {}
    neighborhood_load = [0.0] * 24
    total_cost = 0.0
    
    # Optimize each household independently
    for household in households:
        household_id = household['id']
        base_load = household['base_load']
        shiftable = household['shiftable']
        
        # Optimize this household
        schedule, optimal_load, cost = optimize(base_load, prices, shiftable)
        
        all_schedules[household_id] = schedule
        
        # Add to neighborhood total
        for h in range(24):
            neighborhood_load[h] += optimal_load[h]
        
        total_cost += cost
    
    return all_schedules, neighborhood_load, total_cost


def calculate_worst_neighborhood_cost(
    households: List[Dict],
    prices: List[float]
) -> Tuple[List[float], float]:
    """
    Calculate neighborhood cost with worst scheduling.
    
    Args:
        households: List of household configurations
        prices: Hourly electricity prices
    
    Returns:
        (total_load, total_cost)
    """
    from data_setup import calculate_worst_schedule
    
    neighborhood_load = [0.0] * 24
    
    for household in households:
        base_load = household['base_load']
        shiftable = household['shiftable']
        
        # Calculate worst schedule for this household
        worst_load = calculate_worst_schedule(base_load, shiftable)
        
        # Add to neighborhood total
        for h in range(24):
            neighborhood_load[h] += worst_load[h]
    
    total_cost = calculate_cost(neighborhood_load, prices)
    
    return neighborhood_load, total_cost


def print_neighborhood_results(
    households: List[Dict],
    schedules: Dict[int, Dict],
    worst_cost: float,
    optimal_cost: float,
    show_all_schedules: bool = False
) -> None:
    """Print optimization results for the neighborhood."""
    savings = worst_cost - optimal_cost
    savings_pct = (savings / worst_cost * 100) if worst_cost > 0 else 0
    
    print("\n" + "="*60)
    print("NEIGHBORHOOD OPTIMIZATION RESULTS")
    print("="*60)
    
    print(f"\n💰 Costs:")
    print(f"  Worst schedule:     {worst_cost:.2f} NOK/day")
    print(f"  Optimal schedule:   {optimal_cost:.2f} NOK/day")
    print(f"  Daily savings:      {savings:.2f} NOK/day ({savings_pct:.1f}%)")
    print(f"  Annual savings:     {savings * 365:.2f} NOK/year")
    
    # Calculate per-household averages
    num_households = len(households)
    avg_worst = worst_cost / num_households
    avg_optimal = optimal_cost / num_households
    avg_savings = savings / num_households
    
    print(f"\n📊 Per Household (average):")
    print(f"  Worst cost:     {avg_worst:.2f} NOK/day")
    print(f"  Optimal cost:   {avg_optimal:.2f} NOK/day")
    print(f"  Savings:        {avg_savings:.2f} NOK/day")
    print(f"  Annual savings: {avg_savings * 365:.2f} NOK/year")
    
    # Show EV statistics
    num_with_ev = sum(1 for h in households if h['has_ev'])
    print(f"\n🚗 EV Ownership: {num_with_ev}/{num_households} households ({num_with_ev/num_households*100:.1f}%)")
    
    if show_all_schedules:
        print(f"\n📅 Individual Household Schedules:")
        for household_id, schedule in sorted(schedules.items()):
            household = next(h for h in households if h['id'] == household_id)
            ev_marker = "🚗" if household['has_ev'] else "  "
            print(f"\n  {ev_marker} Household {household_id}:")
            for name, start in sorted(schedule.items()):
                # Find duration
                app = next((a for a in household['shiftable'] if a['name'] == name), None)
                if app:
                    duration = app['duration']
                    end = (start + duration) % 24
                    print(f"    {name:15s} → {start:02d}:00 - {end:02d}:00 ({duration}h)")
                else:
                    print(f"    {name:15s} → {start:02d}:00")
    
    print("="*60)
