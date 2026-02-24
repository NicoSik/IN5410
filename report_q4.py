"""Q4 PDF report: Comparison of cost-only vs cost+peak optimization."""
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


def generate_q4_report(
    filename: str,
    prices: List[float],
    q2_schedule: Dict[str, int],
    q2_load: List[float],
    q2_cost: float,
    q4_schedule: Dict[str, int],
    q4_load: List[float],
    q4_cost: float,
    q4_peak: float,
    worst_load: List[float],
    worst_cost: float,
    shiftable: List[dict],
    beta: float = 5.0
):
    """Generate Q4 comparison PDF report."""
    
    if not MATPLOTLIB_AVAILABLE:
        print("matplotlib not available, skipping PDF generation")
        return
    
    from data_setup import calculate_base_load, get_non_shiftable_appliances
    from helpers import add_appliance_to_load
    
    non_shiftable = get_non_shiftable_appliances()
    base_load_only = calculate_base_load(non_shiftable)
    
    hours = list(range(24))
    q2_peak = max(q2_load)
    worst_peak = max(worst_load)
    
    savings_q2 = worst_cost - q2_cost
    savings_q4 = worst_cost - q4_cost
    cost_diff = q4_cost - q2_cost
    peak_reduction = q2_peak - q4_peak
    peak_pct = (peak_reduction / q2_peak * 100) if q2_peak > 0 else 0
    
    # Colors for shiftable appliances
    colors = {
        'Dishwasher': '#C44536',
        'Laundry': '#2A9D8F',
        'Dryer': '#E9C46A',
        'EV Charging': '#457B9D'
    }
    
    # Create output folder for images
    output_folder = filename.replace('.pdf', '_images')
    os.makedirs(output_folder, exist_ok=True)
    
    with PdfPages(filename) as pdf:
        # ── Page 1: Summary ──
        fig = plt.figure(figsize=(8.5, 11))
        plt.clf()
        plt.axis('off')
        
        plt.text(0.5, 0.92, "QUESTION 4: PEAK LOAD OPTIMIZATION", 
                ha='center', fontsize=18, fontweight='bold')
        plt.text(0.5, 0.88, f"{datetime.now().strftime('%B %d, %Y')}",
                ha='center', fontsize=11)
        plt.text(0.5, 0.84, f"Objective: minimize  α×cost + β×peak_load    (β = {beta})",
                ha='center', fontsize=11, style='italic')
        
        summary = f"""
COMPARISON SUMMARY

                         Q2 (Cost Only)    Q4 (Cost + Peak)
  ─────────────────────────────────────────────────────────
  Daily Cost:           {q2_cost:>8.2f} NOK       {q4_cost:>8.2f} NOK
  Peak Load:            {q2_peak:>8.2f} kWh       {q4_peak:>8.2f} kWh
  ─────────────────────────────────────────────────────────
  Cost Difference:      {cost_diff:+.2f} NOK/day ({'higher' if cost_diff > 0 else 'lower'} in Q4)
  Peak Reduction:       {peak_reduction:.2f} kWh ({peak_pct:.1f}%)

SCHEDULES
                         Q2 Start          Q4 Start"""

        app_map = {app['name']: app for app in shiftable}
        for name in sorted(q2_schedule.keys()):
            q2_start = q2_schedule[name]
            q4_start = q4_schedule[name]
            dur = app_map[name]['duration']
            q2_end = (q2_start + dur) % 24
            q4_end = (q4_start + dur) % 24
            changed = " ◄" if q2_start != q4_start else ""
            summary += f"\n  {name:20s}  {q2_start:02d}:00-{q2_end:02d}:00       {q4_start:02d}:00-{q4_end:02d}:00{changed}"
        
        summary += f"""

KEY INSIGHT
  Q2 concentrates loads in cheapest hours → peak {q2_peak:.2f} kWh
  Q4 spreads loads for peak shaving → peak {q4_peak:.2f} kWh ({peak_pct:.1f}% lower)
  Trade-off: {abs(cost_diff):.2f} NOK/day {'extra' if cost_diff > 0 else 'saved'}"""
        
        plt.text(0.05, 0.05, summary, fontsize=10, verticalalignment='bottom',
                family='monospace', bbox=dict(boxstyle='round', facecolor='white'))
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '01_q4_summary.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # ── Page 2: Side-by-side load profiles (stacked bars) ──
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), sharey=True)
        
        # Q2 stacked bar chart
        _plot_stacked_load(ax1, hours, base_load_only, q2_schedule, shiftable, colors,
                           f'Q2: Cost-Only Optimization', q2_peak)
        
        # Q4 stacked bar chart
        _plot_stacked_load(ax2, hours, base_load_only, q4_schedule, shiftable, colors,
                           f'Q4: Cost + Peak Optimization (β={beta})', q4_peak)
        
        fig.suptitle('Load Distribution Comparison', fontsize=16, fontweight='bold', y=1.02)
        fig.tight_layout()
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '02_q4_load_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # ── Page 3: Overlay comparison ──
        fig = plt.figure(figsize=(12, 6))
        plt.clf()
        
        plt.plot(hours, q2_load, 'o-', color='#E76F51', linewidth=2.5, markersize=5,
                label=f'Q2 Cost-Only (peak={q2_peak:.2f} kWh)')
        plt.plot(hours, q4_load, 's-', color='#2A9D8F', linewidth=2.5, markersize=5,
                label=f'Q4 Cost+Peak (peak={q4_peak:.2f} kWh)')
        plt.plot(hours, base_load_only, '--', color='#6C757D', linewidth=1.5, alpha=0.7,
                label='Non-shiftable base load')
        
        # Mark peak hours
        q2_peak_hour = q2_load.index(max(q2_load))
        q4_peak_hour = q4_load.index(max(q4_load))
        plt.annotate(f'Q2 peak\n{q2_peak:.2f} kWh', 
                    xy=(q2_peak_hour, q2_peak), xytext=(q2_peak_hour + 1.5, q2_peak + 0.3),
                    fontsize=9, fontweight='bold', color='#E76F51',
                    arrowprops=dict(arrowstyle='->', color='#E76F51'))
        plt.annotate(f'Q4 peak\n{q4_peak:.2f} kWh',
                    xy=(q4_peak_hour, q4_peak), xytext=(q4_peak_hour + 1.5, q4_peak + 0.5),
                    fontsize=9, fontweight='bold', color='#2A9D8F',
                    arrowprops=dict(arrowstyle='->', color='#2A9D8F'))
        
        plt.xlabel('Hour', fontsize=12, fontweight='bold')
        plt.ylabel('Load (kWh)', fontsize=12, fontweight='bold')
        plt.title('Q2 vs Q4: Load Profile Comparison', fontsize=14, fontweight='bold')
        plt.xticks(hours, [f'{h:02d}:00' for h in hours], rotation=45)
        plt.legend(fontsize=11, loc='upper left')
        plt.grid(axis='both', alpha=0.3, linestyle='--')
        plt.tight_layout()
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '03_q4_overlay.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # ── Page 4: Cost and Peak comparison bars ──
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Cost comparison
        categories = ['Worst', 'Q2\n(Cost Only)', 'Q4\n(Cost+Peak)']
        costs = [worst_cost, q2_cost, q4_cost]
        bar_colors = ['#E76F51', '#5AC768', '#2A9D8F']
        
        bars = ax1.bar(categories, costs, color=bar_colors, alpha=0.85)
        for bar, val in zip(bars, costs):
            ax1.text(bar.get_x() + bar.get_width()/2., val,
                    f'{val:.2f}', ha='center', va='bottom',
                    fontsize=12, fontweight='bold')
        
        ax1.set_xlabel('Schedule', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Cost (NOK/day)', fontsize=12, fontweight='bold')
        ax1.set_title('Daily Cost Comparison', fontsize=13, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)
        
        # Peak load comparison
        peaks = [worst_peak, q2_peak, q4_peak]
        
        bars = ax2.bar(categories, peaks, color=bar_colors, alpha=0.85)
        for bar, val in zip(bars, peaks):
            ax2.text(bar.get_x() + bar.get_width()/2., val,
                    f'{val:.2f}', ha='center', va='bottom',
                    fontsize=12, fontweight='bold')
        
        ax2.set_xlabel('Schedule', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Peak Load (kWh)', fontsize=12, fontweight='bold')
        ax2.set_title('Peak Load Comparison', fontsize=13, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
        
        fig.suptitle('Cost vs Peak Load Trade-off', fontsize=15, fontweight='bold', y=1.02)
        fig.tight_layout()
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '04_q4_cost_peak_bars.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # ── Page 5: Beta sensitivity analysis ──
        fig = plt.figure(figsize=(12, 6))
        plt.clf()
        
        from optimize_peak import optimize_with_peak_constraint
        
        betas = [0, 0.5, 1, 2, 3, 5, 8, 10, 15, 20, 30, 50]
        scan_costs = []
        scan_peaks = []
        
        for b in betas:
            _, load_b, cost_b, peak_b = optimize_with_peak_constraint(
                base_load_only, prices, shiftable, alpha=1.0, beta=b
            )
            scan_costs.append(cost_b)
            scan_peaks.append(peak_b)
        
        ax1 = plt.gca()
        ax2 = ax1.twinx()
        
        line1, = ax1.plot(betas, scan_costs, 'o-', color='#E76F51', linewidth=2.5, 
                         markersize=6, label='Total Cost (NOK)')
        line2, = ax2.plot(betas, scan_peaks, 's-', color='#2A9D8F', linewidth=2.5, 
                         markersize=6, label='Peak Load (kWh)')
        
        ax1.set_xlabel('β (Peak Load Penalty Weight)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Total Cost (NOK/day)', fontsize=12, fontweight='bold', color='#E76F51')
        ax2.set_ylabel('Peak Load (kWh)', fontsize=12, fontweight='bold', color='#2A9D8F')
        ax1.tick_params(axis='y', labelcolor='#E76F51')
        ax2.tick_params(axis='y', labelcolor='#2A9D8F')
        
        # Mark the chosen beta
        ax1.axvline(x=beta, color='gray', linestyle='--', alpha=0.5)
        ax1.text(beta, ax1.get_ylim()[1], f'β={beta}\n(chosen)', 
                ha='center', va='top', fontsize=9, color='gray')
        
        lines = [line1, line2]
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='center right', fontsize=11)
        
        plt.title('Sensitivity Analysis: β Trade-off', fontsize=14, fontweight='bold')
        plt.grid(axis='x', alpha=0.3, linestyle='--')
        fig.tight_layout()
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '05_q4_beta_sensitivity.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Metadata
        d = pdf.infodict()
        d['Title'] = 'Q4: Peak Load Optimization Report'
        d['CreationDate'] = datetime.now()
    
    print(f"✅ PDF saved: {filename}")
    print(f"✅ Images saved in: {output_folder}/")


def _plot_stacked_load(ax, hours, base_load, schedule, shiftable, colors, title, peak):
    """Helper: Draw stacked bar chart on a given axes."""
    from helpers import add_appliance_to_load
    
    # Non-shiftable base
    ax.bar(hours, base_load, label='Non-shiftable', alpha=0.8, color='#6C757D')
    bottom = base_load[:]
    
    for app in shiftable:
        load = [0.0] * 24
        start = schedule.get(app['name'], app['allowed_hours'][0])
        add_appliance_to_load(load, start, app['duration'], app['energy'])
        ax.bar(hours, load, bottom=bottom, label=app['name'], alpha=0.9, color=colors[app['name']])
        bottom = [bottom[h] + load[h] for h in range(24)]
    
    # Peak line
    ax.axhline(y=peak, color='red', linestyle='--', alpha=0.6, linewidth=1.5,
              label=f'Peak: {peak:.2f} kWh')
    
    ax.set_xlabel('Hour', fontsize=11, fontweight='bold')
    ax.set_ylabel('Load (kWh)', fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_xticks(hours)
    ax.set_xticklabels([f'{h:02d}:00' for h in hours], rotation=45, fontsize=7)
    ax.legend(fontsize=8, loc='upper left')
    ax.grid(axis='y', alpha=0.3)
