"""Core optimization algorithms - Simple and clear."""
from typing import Dict, List, Tuple


def optimize(
    base_load: List[float],
    prices: List[float],
    appliances: List[dict]
) -> Tuple[Dict[str, int], List[float], float]:
    """
    Find the cheapest schedule for shiftable appliances.
    
    Args:
        base_load: Fixed hourly load (24 hours)
        prices: Hourly prices (24 hours)
        appliances: List of {name, energy, duration, allowed_hours}
    
    Returns:
        (schedule, final_load, total_cost)
        - schedule: {appliance_name: start_hour}
        - final_load: hourly consumption (24 hours)
        - total_cost: total daily cost ($)
    """
    from itertools import product
    
    best_cost = float('inf')
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
                h = (start_hour + hour) % 24  # Wrap around midnight
                load[h] += energy_per_hour
        
        # Calculate cost
        cost = sum(load[h] * prices[h] for h in range(24))
        
        # Keep if best
        if cost < best_cost:
            best_cost = cost
            best_schedule = {app['name']: start for app, start in zip(appliances, combination)}
            best_load = load
    
    return best_schedule, best_load, best_cost
