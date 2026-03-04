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
    """Format schedule for display — handles both start-hour and power-profile formats."""
    lines = []
    
    for name, value in sorted(schedule.items()):
        # Check if value is a power profile (list) or a start hour (int)
        if isinstance(value, (list, tuple)):
            # Continuous LP: value is a 24-hour power profile
            active = [(h, value[h]) for h in range(24) if value[h] > 0.01]
            if active:
                hours_str = ", ".join(f"{h:02d}:00 ({p:.2f} kW)" for h, p in active)
                total_e = sum(value)
                lines.append(f"  {name:20s} → {total_e:.2f} kWh across {len(active)}h: {hours_str}")
            else:
                lines.append(f"  {name:20s} → (no load)")
        else:
            # ILP / legacy: value is a start hour (int)
            start = value
            if appliances:
                app_map = {app['name']: app for app in appliances}
                if name in app_map:
                    duration = app_map[name]['duration']
                    end = (start + duration) % 24
                    lines.append(f"  {name:20s} → {start:02d}:00 - {end:02d}:00 ({duration}h)")
                    continue
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
