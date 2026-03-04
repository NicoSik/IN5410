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

Worst Schedule Cost:      {naive_cost:.2f} kr/day
Optimal Schedule Cost:    {optimal_cost:.2f} kr/day

Daily Savings:            {savings:.2f} kr/day
Savings Percentage:       {savings_pct:.1f}%
Annual Savings:           {savings * 365:.2f} kr/year

OPTIMAL SCHEDULE
"""
        # Create a map of appliance names to their info
        app_map = {app['name']: app for app in shiftable}
        
        for name, value in sorted(schedule.items()):
            if isinstance(value, (list, tuple)):
                # Continuous LP: power profile
                active = [(h, value[h]) for h in range(24) if value[h] > 0.01]
                if active:
                    h_start = active[0][0]
                    h_end = (active[-1][0] + 1) % 24
                    total_e = sum(value)
                    summary += f"\n  {name:20s} → {h_start:02d}:00-{h_end:02d}:00 ({total_e:.2f} kWh, {len(active)}h)"
            elif name in app_map:
                start = value
                duration = app_map[name]['duration']
                end = (start + duration) % 24
                summary += f"\n  {name:20s} → {start:02d}:00 - {end:02d}:00 ({duration}h)"
            else:
                summary += f"\n  {name:20s} → {value:02d}:00"
        
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
        plt.ylabel('Price (NOK/kr per kWh)', fontsize=12, fontweight='bold')
        plt.title('Electricity Spot Prices', fontsize=14, fontweight='bold')
        plt.xticks(hours, [f'{h:02d}:00' for h in hours], rotation=45)
        plt.grid(axis='both', alpha=0.3, linestyle='--')
        plt.tight_layout()
        
        # Save to PDF and as image
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '02_prices.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Page 3: Naive Load with Stacked Shiftable Appliances
        fig, ax = plt.subplots(figsize=(14, 6))
        
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
        
        ax.bar(hours, base_load_only, label='Non-shiftable', alpha=0.8, color='#6C757D')
        
        for app in shiftable:
            name = app['name']
            load = shiftable_loads_naive[name]
            ax.bar(hours, load, bottom=bottom, label=name, alpha=0.9, color=colors[name])
            bottom = [bottom[h] + load[h] for h in range(24)]
        
        # Add hourly cost labels on top of each bar
        total_load_naive = [base_load_only[h] + sum(shiftable_loads_naive[app['name']][h] for app in shiftable) for h in range(24)]
        for h in hours:
            hourly_cost = total_load_naive[h] * prices[h]
            if hourly_cost > 0.01:
                ax.text(h, total_load_naive[h] + 0.05, f'{hourly_cost:.2f} kr',
                       ha='center', va='bottom', fontsize=7, fontweight='bold')
        
        # Adjust y-axis to make room for cost labels
        y_max = max(total_load_naive) * 1.18
        ax.set_ylim(0, y_max)
        
        ax.set_xlabel('Hour', fontsize=12, fontweight='bold')
        ax.set_ylabel('Load (kWh)', fontsize=12, fontweight='bold')
        ax.set_title('Worst Schedule - Load Distribution (cost per hour in NOK/kr)', fontsize=14, fontweight='bold')
        ax.set_xticks(hours)
        ax.set_xticklabels([f'{h:02d}:00' for h in hours], rotation=45)
        ax.legend(loc='upper right')
        ax.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        # Save to PDF and as image
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '03_worst_schedule.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Page 4: Optimal Load with Stacked Shiftable Appliances
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Create load profiles for each shiftable appliance (optimal schedule)
        shiftable_loads_optimal = {}
        for app in shiftable:
            name = app['name']
            value = schedule.get(name)
            if isinstance(value, (list, tuple)):
                # Continuous LP: value is already the 24h power profile
                shiftable_loads_optimal[name] = list(value)
            else:
                # ILP / legacy: value is a start hour
                load = [0.0] * 24
                start = value if value is not None else app['allowed_hours'][0]
                add_appliance_to_load(load, start, app['duration'], app['energy'])
                shiftable_loads_optimal[name] = load
        
        # Create stacked bar chart for optimal
        bottom = base_load_only[:]
        
        ax.bar(hours, base_load_only, label='Non-shiftable', alpha=0.8, color='#6C757D')
        
        for app in shiftable:
            name = app['name']
            load = shiftable_loads_optimal[name]
            ax.bar(hours, load, bottom=bottom, label=name, alpha=0.9, color=colors[name])
            bottom = [bottom[h] + load[h] for h in range(24)]
        
        # Add hourly cost labels on top of each bar
        total_load = [base_load_only[h] + sum(shiftable_loads_optimal[app['name']][h] for app in shiftable) for h in range(24)]
        for h in hours:
            hourly_cost = total_load[h] * prices[h]
            if hourly_cost > 0.01:
                ax.text(h, total_load[h] + 0.05, f'{hourly_cost:.2f} kr',
                       ha='center', va='bottom', fontsize=7, fontweight='bold')
        
        # Adjust y-axis to make room for cost labels
        y_max = max(total_load) * 1.18
        ax.set_ylim(0, y_max)
        
        ax.set_xlabel('Hour', fontsize=12, fontweight='bold')
        ax.set_ylabel('Load (kWh)', fontsize=12, fontweight='bold')
        ax.set_title('Optimal Schedule - Load Distribution (cost per hour in NOK/kr)', fontsize=14, fontweight='bold')
        ax.set_xticks(hours)
        ax.set_xticklabels([f'{h:02d}:00' for h in hours], rotation=45)
        ax.legend(loc='upper right')
        ax.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        # Save to PDF and as image
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '04_optimal_schedule.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Page 5: Combined – Spot Price, Load & Hourly Cost (single graph)
        fig, ax_load = plt.subplots(figsize=(14, 7))
        ax_price = ax_load.twinx()
        
        bar_width = 0.7
        
        # Compute total optimal load per hour
        total_load_opt = [base_load_only[h] + sum(shiftable_loads_optimal[app['name']][h] for app in shiftable) for h in range(24)]
        hourly_costs = [total_load_opt[h] * prices[h] for h in range(24)]
        
        # --- Stacked bars for energy load (left y-axis) ---
        bottom_stack = base_load_only[:]
        ax_load.bar(hours, base_load_only, width=bar_width, label='Non-shiftable', alpha=0.8, color='#6C757D')
        for app in shiftable:
            name = app['name']
            load = shiftable_loads_optimal[name]
            ax_load.bar(hours, load, width=bar_width, bottom=bottom_stack, label=name, alpha=0.9, color=colors[name])
            bottom_stack = [bottom_stack[h] + load[h] for h in range(24)]
        
        # --- Cost labels on top of each bar ---
        for h in hours:
            if hourly_costs[h] > 0.01:
                ax_load.text(h, total_load_opt[h] + 0.08, f'{hourly_costs[h]:.2f} kr',
                            ha='center', va='bottom', fontsize=7, fontweight='bold',
                            color='#333333')
        
        # --- Spot price line (right y-axis) ---
        line = ax_price.plot(hours, prices, linewidth=2.5, color='#E76F51', marker='o',
                            markersize=5, label='Spot Price', zorder=5)
        
        # Price value labels along the line
        for h in hours:
            ax_price.text(h, prices[h] + 0.03, f'{prices[h]:.2f}',
                         ha='center', va='bottom', fontsize=7, color='#E76F51', fontweight='bold')
        
        # --- Axes formatting ---
        y_max_load = max(total_load_opt) * 1.25
        ax_load.set_ylim(0, y_max_load)
        ax_price.set_ylim(0, max(prices) * 1.30)
        
        ax_load.set_xlabel('Hour', fontsize=12, fontweight='bold')
        ax_load.set_ylabel('Energy Load (kWh)', fontsize=12, fontweight='bold')
        ax_price.set_ylabel('Spot Price (NOK/kr per kWh)', fontsize=12, fontweight='bold', color='#E76F51')
        ax_price.tick_params(axis='y', labelcolor='#E76F51')
        
        ax_load.set_xticks(hours)
        ax_load.set_xticklabels([f'{h:02d}:00' for h in hours], rotation=45)
        ax_load.grid(axis='y', alpha=0.2, linestyle='--')
        
        ax_load.set_title('Optimal Schedule — Spot Price, Energy Load & Hourly Cost',
                         fontsize=14, fontweight='bold', pad=12)
        
        # Combined legend (bars from left axis + line from right axis)
        handles_load, labels_load = ax_load.get_legend_handles_labels()
        handles_price, labels_price = ax_price.get_legend_handles_labels()
        ax_load.legend(handles_load + handles_price, labels_load + labels_price,
                      loc='upper right', fontsize=9)
        
        plt.tight_layout()
        
        # Save to PDF and as image
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '05_combined_overview.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Page 6: Cost comparison
        fig = plt.figure(figsize=(8, 5))
        plt.clf()
        
        categories = ['Worst', 'Optimal']
        values = [naive_cost, optimal_cost]
        bar_colors = ['#E76F51', "#5AC768"]  # Dark coral and dark teal
        
        bars = plt.bar(categories, values, color=bar_colors, alpha=0.8)
        
        for bar, val in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width()/2., val,
                    f'{val:.2f} kr', ha='center', va='bottom', 
                    fontsize=14, fontweight='bold')
        
        plt.xlabel('Schedule Type', fontsize=12, fontweight='bold')
        plt.ylabel('Cost (NOK/kr)', fontsize=12, fontweight='bold')
        plt.title('Cost Comparison', fontsize=14, fontweight='bold')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        # Save to PDF and as image
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '06_cost_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Metadata
        d = pdf.infodict()
        d['Title'] = 'Energy Optimization Report'
        d['CreationDate'] = datetime.now()
    
    print(f"✅ PDF saved: {filename}")
    print(f"✅ Images saved in: {output_folder}/")


if __name__ == "__main__":
    print("This module generates PDF reports. Run 'python run.py' instead.")
