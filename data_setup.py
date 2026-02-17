"""Data setup - Generate prices and appliance configurations."""
import random
from typing import List


def generate_prices(seed: int = 42) -> List[float]:
    """
    Generate 24-hour electricity prices (NOK/kWh).
    
    Based on realistic Norwegian spot prices (winter 2026):
    - Night (0-6): Cheap ~1.00 NOK/kWh
    - Morning (7-9): Rising ~1.40 NOK/kWh
    - Day (10-16): Moderate ~1.20 NOK/kWh
    - Peak (17-21): Expensive ~2.00 NOK/kWh
    - Evening (22-23): Moderate ~1.30 NOK/kWh
    """
    rng = random.Random(seed)
    prices = []
    
    for hour in range(24):
        if 0 <= hour <= 6:
            base = 1.00  # Night - cheapest
        elif 7 <= hour <= 9:
            base = 1.40  # Morning rush
        elif 10 <= hour <= 16:
            base = 1.20  # Daytime
        elif 17 <= hour <= 21:
            base = 2.00  # Peak hours - most expensive
        else:
            base = 1.30  # Late evening
        
        # Add realistic price variation (±0.10 NOK)
        noise = rng.uniform(-0.10, 0.10)
        prices.append(max(0.50, base + noise))
    
    return prices


def get_non_shiftable_appliances() -> List[dict]:
    """
    Define non-shiftable appliances (fixed schedules).
    
    Returns list of: {name, energy, profile}
    where profile is 24-hour consumption pattern.
    """
    appliances = []
    
    # Lighting: 1.5 kWh/day, 10:00-20:00
    lighting = [0.0] * 24
    for h in range(10, 21):
        lighting[h] = 1.5 / 11
    appliances.append({'name': 'Lighting', 'energy': 1.5, 'profile': lighting})
    
    # Heating: 8.0 kWh/day, heavier morning/evening
    heating = [0.0] * 24
    weights = [0.7] * 24
    for h in range(6, 10):
        weights[h] = 1.4
    for h in range(17, 23):
        weights[h] = 1.6
    total_weight = sum(weights)
    for h in range(24):
        heating[h] = 8.0 * (weights[h] / total_weight)
    appliances.append({'name': 'Heating', 'energy': 8.0, 'profile': heating})
    
    # Refrigerator: 2.64 kWh/day, constant
    fridge = [2.64 / 24.0] * 24
    appliances.append({'name': 'Refrigerator', 'energy': 2.64, 'profile': fridge})
    
    # Stove: 3.9 kWh/day, 17:00-19:00
    stove = [0.0] * 24
    for h in range(17, 20):
        stove[h] = 3.9 / 3
    appliances.append({'name': 'Stove', 'energy': 3.9, 'profile': stove})
    
    # TV: 0.4 kWh/day, 19:00-23:00
    tv = [0.0] * 24
    for h in range(19, 24):
        tv[h] = 0.4 / 5
    appliances.append({'name': 'TV', 'energy': 0.4, 'profile': tv})
    
    # Computers: 1.2 kWh/day, 9:00-17:00
    computers = [0.0] * 24
    for h in range(9, 17):
        computers[h] = 1.2 / 8
    appliances.append({'name': 'Computers', 'energy': 1.2, 'profile': computers})
    
    # Small appliances (router, charger, microwave, etc.)
    small = [0.0] * 24
    small[7] = 0.24   # Toaster
    small[8] = 0.25   # Hair dryer
    small[12] = 0.60  # Microwave
    for h in range(20, 23):
        small[h] = 0.015 / 3  # Phone charger
    small[21] = 0.275  # Iron
    for h in range(24):
        small[h] += 0.144 / 24  # Router (constant)
        small[h] += 1.32 / 24   # Freezer (constant)
    appliances.append({'name': 'Small Appliances', 'energy': 3.0, 'profile': small})
    
    return appliances


def get_shiftable_appliances() -> List[dict]:
    """
    Define shiftable appliances (can be scheduled).
    
    Returns list of: {name, energy, duration, allowed_hours}
    """
    return [
        {
            'name': 'Dishwasher',
            'energy': 1.44,  # kWh
            'duration': 2,   # hours
            'allowed_hours': [19, 20, 21, 22, 0, 1, 2, 3, 4, 5]  # Overnight
        },
        {
            'name': 'Laundry',
            'energy': 1.94,
            'duration': 2,
            'allowed_hours': [8, 9, 10, 11, 12, 13, 14, 15]  # Daytime
        },
        {
            'name': 'Dryer',
            'energy': 2.50,
            'duration': 2,
            'allowed_hours': [8, 9, 10, 11, 12, 13, 14, 15]  # Daytime
        },
        {
            'name': 'EV Charging',
            'energy': 9.90,
            'duration': 6,
            'allowed_hours': [22, 23, 0, 1]  # Overnight
        }
    ]


def calculate_base_load(non_shiftable: List[dict]) -> List[float]:
    """Calculate total base load from non-shiftable appliances."""
    base_load = [0.0] * 24
    
    for appliance in non_shiftable:
        for h in range(24):
            base_load[h] += appliance['profile'][h]
    
    return base_load


def calculate_naive_schedule(
    base_load: List[float],
    shiftable: List[dict]
) -> List[float]:
    """
    Calculate load for naive schedule (everything in evening).
    This is what happens without optimization.
    """
    from helpers import add_appliance_to_load
    
    load = base_load[:]
    
    # Naive start times (all in evening/peak hours)
    naive_times = {
        'Dishwasher': 20,
        'Laundry': 18,
        'Dryer': 20,
        'EV Charging': 18
    }
    
    for app in shiftable:
        start = naive_times.get(app['name'], app['allowed_hours'][0])
        add_appliance_to_load(load, start, app['duration'], app['energy'])
    
    return load


def print_data_summary(prices: List[float], non_shiftable: List[dict], 
                      shiftable: List[dict]) -> None:
    """Print summary of input data."""
    print("\n" + "="*60)
    print("INPUT DATA SUMMARY")
    print("="*60)
    
    print("\n📊 Price Range:")
    print(f"  Min: {min(prices):.2f} NOK/kWh")
    print(f"  Max: {max(prices):.2f} NOK/kWh")
    print(f"  Avg: {sum(prices)/len(prices):.2f} NOK/kWh")
    
    print("\n📌 Non-Shiftable Appliances:")
    total_fixed = sum(app['energy'] for app in non_shiftable)
    for app in non_shiftable:
        print(f"  {app['name']:20s} {app['energy']:6.2f} kWh/day")
    print(f"  {'TOTAL':20s} {total_fixed:6.2f} kWh/day")
    
    print("\n⚡ Shiftable Appliances:")
    total_flex = sum(app['energy'] for app in shiftable)
    for app in shiftable:
        print(f"  {app['name']:20s} {app['energy']:6.2f} kWh/day  "
              f"({app['duration']}h, {len(app['allowed_hours'])} options)")
    print(f"  {'TOTAL':20s} {total_flex:6.2f} kWh/day")
    
    print(f"\n📈 Total Daily Energy: {total_fixed + total_flex:.2f} kWh/day")
    print("="*60)
