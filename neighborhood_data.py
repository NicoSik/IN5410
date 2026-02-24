"""Data setup for neighborhood (Question 3)."""
import random
from typing import List, Dict
from data_setup import get_non_shiftable_appliances, get_shiftable_appliances, calculate_base_load


def create_household(household_id: int, has_ev: bool = True) -> Dict:
    """
    Create a household with appliances.
    
    Args:
        household_id: Unique identifier for the household
        has_ev: Whether this household owns an EV
    
    Returns:
        Dictionary with household configuration
    """
    non_shiftable = get_non_shiftable_appliances()
    shiftable = get_shiftable_appliances()
    
    # Remove EV if household doesn't own one
    if not has_ev:
        shiftable = [app for app in shiftable if app['name'] != 'EV Charging']
    
    base_load = calculate_base_load(non_shiftable)
    
    return {
        'id': household_id,
        'has_ev': has_ev,
        'non_shiftable': non_shiftable,
        'shiftable': shiftable,
        'base_load': base_load
    }


def create_neighborhood(num_households: int = 30, ev_ownership_rate: float = 0.5, seed: int = 42) -> List[Dict]:
    """
    Create a neighborhood with multiple households.
    
    Args:
        num_households: Number of households in the neighborhood
        ev_ownership_rate: Fraction of households that own an EV (0.0 to 1.0)
        seed: Random seed for reproducibility
    
    Returns:
        List of household configurations
    """
    rng = random.Random(seed)
    households = []
    
    for i in range(num_households):
        # Randomly assign EV ownership based on the rate
        has_ev = rng.random() < ev_ownership_rate
        household = create_household(i + 1, has_ev)
        households.append(household)
    
    return households


def print_neighborhood_summary(households: List[Dict], prices: List[float]) -> None:
    """Print summary of neighborhood configuration."""
    num_with_ev = sum(1 for h in households if h['has_ev'])
    num_without_ev = len(households) - num_with_ev
    
    print("\n" + "="*60)
    print("NEIGHBORHOOD CONFIGURATION")
    print("="*60)
    
    print(f"\n🏘️  Total Households: {len(households)}")
    print(f"  With EV:    {num_with_ev} ({num_with_ev/len(households)*100:.1f}%)")
    print(f"  Without EV: {num_without_ev} ({num_without_ev/len(households)*100:.1f}%)")
    
    # Calculate total energy
    total_base_energy = 0
    total_shiftable_energy = 0
    
    for household in households:
        total_base_energy += sum(household['base_load'])
        for app in household['shiftable']:
            total_shiftable_energy += app['energy']
    
    print(f"\n📊 Total Daily Energy Consumption:")
    print(f"  Non-shiftable: {total_base_energy:.2f} kWh/day")
    print(f"  Shiftable:     {total_shiftable_energy:.2f} kWh/day")
    print(f"  TOTAL:         {total_base_energy + total_shiftable_energy:.2f} kWh/day")
    
    print(f"\n💰 Price Range:")
    print(f"  Min: {min(prices):.2f} NOK/kWh")
    print(f"  Max: {max(prices):.2f} NOK/kWh")
    print(f"  Avg: {sum(prices)/len(prices):.2f} NOK/kWh")
    
    print("="*60)
