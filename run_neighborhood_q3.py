"""Main program for neighborhood optimization (Question 3)."""
from data_setup import generate_prices
from neighborhood_data_q3 import create_neighborhood, print_neighborhood_summary
from optimize_neighborhood_q3 import (
    optimize_neighborhood,
    calculate_naive_neighborhood_cost,
    print_neighborhood_results
)


def main():
    """Run neighborhood energy optimization."""
    
    print("\n🏘️  NEIGHBORHOOD ENERGY OPTIMIZATION (Question 3)")
    
    # 1. Setup neighborhood
    num_households = 30
    ev_ownership_rate = 0.5  # 50% of households own an EV
    
    households = create_neighborhood(
        num_households=num_households,
        ev_ownership_rate=ev_ownership_rate,
        seed=42
    )
    
    # 2. Generate prices (same as Question 2)
    prices = generate_prices(seed=42)
    
    # 3. Print configuration
    print_neighborhood_summary(households, prices)
    
    # 4. Calculate naive cost (no optimization)
    print("\n⏳ Calculating naive schedule cost...")
    naive_load, naive_cost = calculate_naive_neighborhood_cost(households, prices)
    
    # 5. Optimize neighborhood
    print("⚙️  Optimizing neighborhood schedule...")
    schedules, optimal_load, optimal_cost = optimize_neighborhood(households, prices)
    
    # 6. Show results
    print_neighborhood_results(
        households,
        schedules,
        naive_cost,
        optimal_cost,
        show_all_schedules=False  # Set to True to see all household schedules
    )
    
    # 7. Optional: Show first 3 household schedules as examples
    print("\n📋 Example Schedules (first 3 households):")
    for i in range(min(3, len(households))):
        household = households[i]
        household_id = household['id']
        schedule = schedules[household_id]
        ev_marker = "🚗" if household['has_ev'] else "  "
        
        print(f"\n  {ev_marker} Household {household_id}:")
        for name, value in sorted(schedule.items()):
            app = next((a for a in household['shiftable'] if a['name'] == name), None)
            if app:
                duration = app['duration']
                if isinstance(value, (list, tuple)):
                    active = [h for h in range(24) if value[h] > 0.01]
                    if active:
                        start = active[0]
                        end = (active[-1] + 1) % 24
                    else:
                        start, end = 0, 0
                else:
                    start = value
                    end = (start + duration) % 24
                print(f"    {name:15s} → {start:02d}:00 - {end:02d}:00 ({duration}h)")


if __name__ == "__main__":
    main()
