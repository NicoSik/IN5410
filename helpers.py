"""Helper utilities for calculations and formatting."""
from typing import List


def calculate_cost(load: List[float], prices: List[float]) -> float:
    """Calculate total daily cost."""
    return sum(load[h] * prices[h] for h in range(24))


def add_appliance_to_load(
    load: List[float],
    start_hour: int,
    duration: int,
    total_energy: float
) -> None:
    """Add appliance consumption to load profile."""
    energy_per_hour = total_energy / duration
    
    for hour in range(duration):
        h = (start_hour + hour) % 24
        load[h] += energy_per_hour


def format_schedule(schedule: dict, appliances: List[dict] = None) -> str:
    """Format schedule for display with duration and end time."""
    lines = []
    
    if appliances:
        # Create a map of appliance names to their info
        app_map = {app['name']: app for app in appliances}
        
        for name, start in sorted(schedule.items()):
            if name in app_map:
                duration = app_map[name]['duration']
                end = (start + duration) % 24
                lines.append(f"  {name:20s} → {start:02d}:00 - {end:02d}:00 ({duration}h)")
            else:
                lines.append(f"  {name:20s} → {start:02d}:00")
    else:
        for name, start in sorted(schedule.items()):
            lines.append(f"  {name:20s} → {start:02d}:00")
    
    return "\n".join(lines)


def format_hourly_table(load: List[float], prices: List[float]) -> str:
    """Format hourly load and cost table."""
    lines = []
    for h in range(24):
        cost = load[h] * prices[h]
        lines.append(f"  {h:02d}:00  Load: {load[h]:.3f} kWh  "
                    f"Price: {prices[h]:.2f} NOK  Cost: {cost:.2f} NOK")
    return "\n".join(lines)


def print_summary(
    naive_cost: float,
    optimal_cost: float,
    schedule: dict,
    shiftable: List[dict] = None
) -> None:
    """Print optimization results summary."""
    savings = naive_cost - optimal_cost
    savings_pct = (savings / naive_cost * 100) if naive_cost > 0 else 0
    
    print("\n" + "="*60)
    print("OPTIMIZATION RESULTS")
    print("="*60)
    
    print("\nOptimal Schedule:")
    print(format_schedule(schedule, shiftable))
    
    print(f"\nCosts:")
    print(f"  Naive schedule:     {naive_cost:.2f} NOK/day")
    print(f"  Optimal schedule:   {optimal_cost:.2f} NOK/day")
    print(f"  Daily savings:      {savings:.2f} NOK/day ({savings_pct:.1f}%)")
    print(f"  Annual savings:     {savings * 365:.2f} NOK/year")
    print("="*60)
