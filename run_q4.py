"""
Question 4: Run peak load optimization and compare with Q2.

Compares two optimization strategies:
  Q2: Minimize total energy cost only
  Q4: Minimize energy cost + peak load (weighted combination)

The β parameter controls the trade-off:
  β = 0  → same as Q2 (cost only)
  β ↑    → more peak shaving, flatter load curve, possibly higher cost
"""

from data_setup import (
    generate_prices,
    get_non_shiftable_appliances,
    get_shiftable_appliances,
    calculate_base_load,
    calculate_worst_schedule,
    print_data_summary
)
from optimize import optimize
from optimize_peak import optimize_with_peak_constraint, print_q4_comparison
from helpers import calculate_cost


def main():
    """Run Q2 and Q4 optimization and compare results."""
    
    # 1. Setup data
    print("\n🔌 Question 4: Peak Load Optimization")
    print("="*60)
    
    prices = generate_prices(seed=42)
    non_shiftable = get_non_shiftable_appliances()
    shiftable = get_shiftable_appliances()
    
    print_data_summary(prices, non_shiftable, shiftable)
    
    # 2. Calculate base load
    base_load = calculate_base_load(non_shiftable)
    
    # 3. Calculate worst (naive) schedule
    worst_load = calculate_worst_schedule(base_load, shiftable)
    worst_cost = calculate_cost(worst_load, prices)
    
    # 4. Q2: Optimize for cost only
    print("\n⚙️  Q2: Optimizing for minimum cost...")
    q2_schedule, q2_load, q2_cost = optimize(base_load, prices, shiftable)
    
    # 5. Q4: Optimize for cost + peak load
    beta = 5.0  # Peak load penalty weight
    print(f"\n⚙️  Q4: Optimizing for minimum cost + peak load (β={beta})...")
    q4_schedule, q4_load, q4_cost, q4_peak = optimize_with_peak_constraint(
        base_load, prices, shiftable, alpha=1.0, beta=beta
    )
    
    # 6. Print comparison
    print_q4_comparison(
        q2_schedule, q2_load, q2_cost,
        q4_schedule, q4_load, q4_cost, q4_peak,
        shiftable
    )
    
    # 7. Generate PDF report
    try:
        from report_q4 import generate_q4_report
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"q4_peak_report_{timestamp}.pdf"
        
        print(f"\n📊 Generating Q4 PDF report: {pdf_filename}")
        generate_q4_report(
            filename=pdf_filename,
            prices=prices,
            q2_schedule=q2_schedule,
            q2_load=q2_load,
            q2_cost=q2_cost,
            q4_schedule=q4_schedule,
            q4_load=q4_load,
            q4_cost=q4_cost,
            q4_peak=q4_peak,
            worst_load=worst_load,
            worst_cost=worst_cost,
            shiftable=shiftable,
            beta=beta
        )
    except ImportError:
        print("\n💡 Install matplotlib to generate PDF reports: pip install matplotlib")
    except Exception as e:
        print(f"\n⚠️  Could not generate PDF: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
