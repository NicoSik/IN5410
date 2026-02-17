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
        for name, start in sorted(schedule.items()):
            summary += f"\n  {name:20s} → {start:02d}:00"
        
        plt.text(0.1, 0.05, summary, fontsize=11, verticalalignment='bottom',
                family='monospace', bbox=dict(boxstyle='round', facecolor='white'))
        
        pdf.savefig(fig, bbox_inches='tight')
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
        plt.xticks(hours, [f'{h:02d}' for h in hours], rotation=45)
        plt.grid(axis='both', alpha=0.3, linestyle='--')
        plt.tight_layout()
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        # Page 3: Load comparison
        fig = plt.figure(figsize=(10, 5))
        plt.clf()
        
        width = 0.35
        x = [h - width/2 for h in hours]
        x2 = [h + width/2 for h in hours]
        
        plt.bar(x, naive_load, width, label='Naive', alpha=0.7, color='coral')
        plt.bar(x2, optimal_load, width, label='Optimal', alpha=0.7, color='lightblue')
        
        plt.xlabel('Hour', fontsize=12, fontweight='bold')
        plt.ylabel('Load (kWh)', fontsize=12, fontweight='bold')
        plt.title('Load Comparison', fontsize=14, fontweight='bold')
        plt.xticks(hours, [f'{h:02d}' for h in hours], rotation=45)
        plt.legend()
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        # Page 4: Cost comparison
        fig = plt.figure(figsize=(8, 5))
        plt.clf()
        
        categories = ['Naive', 'Optimal', 'Savings']
        values = [naive_cost, optimal_cost, savings]
        colors = ['coral', 'lightgreen', 'gold']
        
        bars = plt.bar(categories, values, color=colors, alpha=0.8)
        
        for bar, val in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width()/2., val,
                    f'{val:.2f} NOK', ha='center', va='bottom', 
                    fontsize=14, fontweight='bold')
        
        plt.ylabel('Cost (NOK)', fontsize=12, fontweight='bold')
        plt.title('Cost Comparison', fontsize=14, fontweight='bold')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        # Metadata
        d = pdf.infodict()
        d['Title'] = 'Energy Optimization Report'
        d['CreationDate'] = datetime.now()
    
    print(f"✅ PDF saved: {filename}")


if __name__ == "__main__":
    print("This module generates PDF reports. Run 'python run.py' instead.")
