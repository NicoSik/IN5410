"""Simple PDF report generator."""
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from typing import Dict, List
from datetime import datetime
import os


def generate_simple_report(
    filename: str,
    prices: List[float],
    schedule: Dict[str, int],
    optimal_load: List[float],
    optimal_cost: float,
    naive_load: List[float],
    naive_cost: float,
    shiftable: List[dict]
):
    """Generate PDF report with key charts."""
    
    if not MATPLOTLIB_AVAILABLE:
        print("matplotlib not available, skipping PDF generation")
        return
    
    savings = naive_cost - optimal_cost
    savings_pct = (savings / naive_cost * 100) if naive_cost > 0 else 0
    
    # Create output folder for images
    output_folder = filename.replace('.pdf', '_images')
    os.makedirs(output_folder, exist_ok=True)
    
    with PdfPages(filename) as pdf:
        # Page 1: Summary
        fig = plt.figure(figsize=(8.5, 11))
        plt.clf()
        plt.axis('off')
        
        plt.text(0.5, 0.9, "ENERGY OPTIMIZATION REPORT", 
                ha='center', fontsize=20, fontweight='bold')
        
        plt.text(0.5, 0.82, f"{datetime.now().strftime('%B %d, %Y')}", 
                ha='center', fontsize=12)
        
        summary = f"""
RESULTS

Naive Schedule Cost:      {naive_cost:.2f} NOK/day
Optimal Schedule Cost:    {optimal_cost:.2f} NOK/day

Daily Savings:            {savings:.2f} NOK/day
Savings Percentage:       {savings_pct:.1f}%
Annual Savings:           {savings * 365:.2f} NOK/year

OPTIMAL SCHEDULE
"""
        # Create a map of appliance names to their info
        app_map = {app['name']: app for app in shiftable}
        
        for name, start in sorted(schedule.items()):
            if name in app_map:
                duration = app_map[name]['duration']
                end = (start + duration) % 24
                summary += f"\n  {name:20s} → {start:02d}:00 - {end:02d}:00 ({duration}h)"
            else:
                summary += f"\n  {name:20s} → {start:02d}:00"
        
        plt.text(0.1, 0.05, summary, fontsize=11, verticalalignment='bottom',
                family='monospace', bbox=dict(boxstyle='round', facecolor='white'))
        
        # Save to PDF and as image
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '01_summary.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Page 2: Price curve
        fig = plt.figure(figsize=(10, 5))
        plt.clf()
        
        hours = list(range(24))
        
        # Simple line plot with area fill - focus on price values
        plt.plot(hours, prices, linewidth=2.5, color='#2E86AB', marker='o', markersize=4)
        plt.fill_between(hours, prices, alpha=0.3, color='#2E86AB')
        
        # Add price labels on key hours
        for h in [0, 6, 9, 12, 17, 21, 23]:
            plt.text(h, prices[h], f'{prices[h]:.2f}', 
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        plt.xlabel('Time (hour)', fontsize=12, fontweight='bold')
        plt.ylabel('Price (NOK/kWh)', fontsize=12, fontweight='bold')
        plt.title('Electricity Spot Prices', fontsize=14, fontweight='bold')
        plt.xticks(hours, [f'{h:02d}:00' for h in hours], rotation=45)
        plt.grid(axis='both', alpha=0.3, linestyle='--')
        plt.tight_layout()
        
        # Save to PDF and as image
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '02_prices.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Page 3: Naive Load with Stacked Shiftable Appliances
        fig = plt.figure(figsize=(12, 6))
        plt.clf()
        
        # Calculate base load (non-shiftable)
        from data_setup import calculate_worst_schedule, calculate_base_load, get_non_shiftable_appliances
        from helpers import add_appliance_to_load
        
        non_shiftable = get_non_shiftable_appliances()
        base_load_only = calculate_base_load(non_shiftable)
        
        # Naive start times (same as in calculate_naive_schedule)
        naive_times = {
            'Dishwasher': 20,
            'Laundry': 18,
            'Dryer': 20,
            'EV Charging': 18
        }
        
        # Create load profiles for each shiftable appliance (naive schedule)
        shiftable_loads_naive = {}
        for app in shiftable:
            load = [0.0] * 24
            start = naive_times.get(app['name'], app['allowed_hours'][0])
            add_appliance_to_load(load, start, app['duration'], app['energy'])
            shiftable_loads_naive[app['name']] = load
        
        # Define colors for shiftable appliances (darker colors)
        colors = {
            'Dishwasher': '#C44536',      # Dark red
            'Laundry': '#2A9D8F',         # Dark teal
            'Dryer': '#E9C46A',           # Dark yellow/gold
            'EV Charging': '#457B9D'      # Dark blue
        }
        
        # Create stacked bar chart for naive
        bottom = base_load_only[:]
        
        plt.bar(hours, base_load_only, label='Non-shiftable', alpha=0.8, color='#6C757D')
        
        for app in shiftable:
            name = app['name']
            load = shiftable_loads_naive[name]
            plt.bar(hours, load, bottom=bottom, label=name, alpha=0.9, color=colors[name])
            bottom = [bottom[h] + load[h] for h in range(24)]
        
        plt.xlabel('Hour', fontsize=12, fontweight='bold')
        plt.ylabel('Load (kWh)', fontsize=12, fontweight='bold')
        plt.title('Worst Schedule - Load Distribution', fontsize=14, fontweight='bold')
        plt.xticks(hours, [f'{h:02d}:00' for h in hours], rotation=45)
        plt.legend(loc='upper left')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        # Save to PDF and as image
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '03_naive_schedule.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Page 4: Optimal Load with Stacked Shiftable Appliances
        fig = plt.figure(figsize=(12, 6))
        plt.clf()
        
        # Create load profiles for each shiftable appliance (optimal schedule)
        shiftable_loads_optimal = {}
        for app in shiftable:
            load = [0.0] * 24
            start = schedule.get(app['name'], app['allowed_hours'][0])
            add_appliance_to_load(load, start, app['duration'], app['energy'])
            shiftable_loads_optimal[app['name']] = load
        
        # Create stacked bar chart for optimal
        bottom = base_load_only[:]
        
        plt.bar(hours, base_load_only, label='Non-shiftable', alpha=0.8, color='#6C757D')
        
        for app in shiftable:
            name = app['name']
            load = shiftable_loads_optimal[name]
            plt.bar(hours, load, bottom=bottom, label=name, alpha=0.9, color=colors[name])
            bottom = [bottom[h] + load[h] for h in range(24)]
        
        plt.xlabel('Hour', fontsize=12, fontweight='bold')
        plt.ylabel('Load (kWh)', fontsize=12, fontweight='bold')
        plt.title('Optimal Schedule - Load Distribution', fontsize=14, fontweight='bold')
        plt.xticks(hours, [f'{h:02d}:00' for h in hours], rotation=45)
        plt.legend(loc='upper left')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        # Save to PDF and as image
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '04_optimal_schedule.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Page 5: Cost comparison
        fig = plt.figure(figsize=(8, 5))
        plt.clf()
        
        categories = ['Worst', 'Optimal']
        values = [naive_cost, optimal_cost]
        bar_colors = ['#E76F51', "#5AC768"]  # Dark coral and dark teal
        
        bars = plt.bar(categories, values, color=bar_colors, alpha=0.8)
        
        for bar, val in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width()/2., val,
                    f'{val:.2f} NOK', ha='center', va='bottom', 
                    fontsize=14, fontweight='bold')
        
        plt.xlabel('Schedule Type', fontsize=12, fontweight='bold')
        plt.ylabel('Cost (NOK)', fontsize=12, fontweight='bold')
        plt.title('Cost Comparison', fontsize=14, fontweight='bold')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        # Save to PDF and as image
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '05_cost_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Metadata
        d = pdf.infodict()
        d['Title'] = 'Energy Optimization Report'
        d['CreationDate'] = datetime.now()
    
    print(f"✅ PDF saved: {filename}")
    print(f"✅ Images saved in: {output_folder}/")


if __name__ == "__main__":
    print("This module generates PDF reports. Run 'python run.py' instead.")
