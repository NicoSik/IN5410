"""Main program - Energy optimization."""
from data_setup import (
    generate_prices,
    get_non_shiftable_appliances,
    get_shiftable_appliances,
    calculate_base_load,
    calculate_naive_schedule,
    print_data_summary
)
from optimize import optimize
from helpers import calculate_cost, print_summary


def main():
    """Run energy optimization."""
    
    # 1. Setup data
    print("\n🔌 Energy Optimization System")
    
    prices = generate_prices(seed=42)
    non_shiftable = get_non_shiftable_appliances()
    shiftable = get_shiftable_appliances()
    
    print_data_summary(prices, non_shiftable, shiftable)
    
    # 2. Calculate base load (fixed consumption)
    base_load = calculate_base_load(non_shiftable)
    
    # 3. Calculate naive cost (no optimization)
    naive_load = calculate_naive_schedule(base_load, shiftable)
    naive_cost = calculate_cost(naive_load, prices)
    
    # 4. Optimize
    print("\n⚙️  Optimizing schedule...")
    schedule, optimal_load, optimal_cost = optimize(base_load, prices, shiftable)
    
    # 5. Show results
    print_summary(naive_cost, optimal_cost, schedule)
    
    # 6. Generate PDF report (optional)
    try:
        from report_simple import generate_simple_report
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"energy_report_{timestamp}.pdf"
        
        print(f"\n📊 Generating PDF report: {pdf_filename}")
        generate_simple_report(
            filename=pdf_filename,
            prices=prices,
            schedule=schedule,
            optimal_load=optimal_load,
            optimal_cost=optimal_cost,
            naive_load=naive_load,
            naive_cost=naive_cost,
            shiftable=shiftable
        )
    except ImportError:
        print("\n💡 Install matplotlib to generate PDF reports: pip install matplotlib")
    except Exception as e:
        print(f"\n⚠️  Could not generate PDF: {e}")


if __name__ == "__main__":
    main()
