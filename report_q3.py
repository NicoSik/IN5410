"""Q3 PDF report: Neighborhood optimization with scheduling strategy visualization."""
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from typing import Dict, List
from datetime import datetime
import os


# ── Colour palette ──────────────────────────────────────────────────
COLORS = {
    'Dishwasher':   '#C44536',
    'Laundry':      '#2A9D8F',
    'Dryer':        '#E9C46A',
    'EV Charging':  '#457B9D',
}
ABBREV = {
    'Dishwasher':  'DW',
    'Laundry':     'LN',
    'Dryer':       'DR',
    'EV Charging': 'EV',
}
BASE_COLOR = '#6C757D'


def _schedule_to_block(value, app):
    """Convert a schedule value (list or int) to (start, end) hours."""
    if isinstance(value, (list, tuple)):
        active = [h for h in range(24) if value[h] > 0.01]
        if active:
            return active[0], (active[-1] + 1) % 24
        return 0, 0
    else:
        return value, (value + app['duration']) % 24


def _load_from_schedule_value(value, app):
    """Return a 24-element load list from a schedule value."""
    if isinstance(value, (list, tuple)):
        return list(value)
    else:
        from helpers import add_appliance_to_load
        load = [0.0] * 24
        add_appliance_to_load(load, value, app['duration'], app['energy'])
        return load


# =====================================================================
def generate_q3_report(
    filename: str,
    prices: List[float],
    households: List[dict],
    schedules: Dict[int, dict],
    worst_load: List[float],
    worst_cost: float,
    optimal_load: List[float],
    optimal_cost: float,
):
    """Generate a multi-page Q3 PDF report."""
    if not MATPLOTLIB_AVAILABLE:
        print("matplotlib not available, skipping PDF generation")
        return

    from data_setup import calculate_base_load, get_non_shiftable_appliances

    hours = list(range(24))
    num_hh = len(households)
    num_ev = sum(1 for h in households if h['has_ev'])
    savings = worst_cost - optimal_cost
    savings_pct = (savings / worst_cost * 100) if worst_cost > 0 else 0
    worst_peak = max(worst_load)
    optimal_peak = max(optimal_load)

    output_folder = filename.replace('.pdf', '_images')
    os.makedirs(output_folder, exist_ok=True)

    with PdfPages(filename) as pdf:

        # ── PAGE 1 — Summary ────────────────────────────────────────
        fig = plt.figure(figsize=(8.5, 11))
        plt.axis('off')
        plt.text(0.5, 0.92, "QUESTION 3: NEIGHBORHOOD OPTIMIZATION",
                 ha='center', fontsize=18, fontweight='bold')
        plt.text(0.5, 0.88, datetime.now().strftime('%B %d, %Y'),
                 ha='center', fontsize=11)
        plt.text(0.5, 0.84,
                 f"{num_hh} households  ·  {num_ev} with EV ({num_ev/num_hh*100:.0f}%)",
                 ha='center', fontsize=11, style='italic')

        summary = f"""
NEIGHBORHOOD SUMMARY
  Households:           {num_hh}
  With EV:              {num_ev} ({num_ev/num_hh*100:.1f}%)
  Without EV:           {num_hh - num_ev} ({(num_hh-num_ev)/num_hh*100:.1f}%)

COST RESULTS
                         Worst           Optimal
  ─────────────────────────────────────────────────
  Total Cost:           {worst_cost:>10.2f} kr    {optimal_cost:>10.2f} kr
  Per Household (avg):  {worst_cost/num_hh:>10.2f} kr    {optimal_cost/num_hh:>10.2f} kr
  ─────────────────────────────────────────────────
  Daily Savings:        {savings:.2f} kr/day ({savings_pct:.1f}%)
  Annual Savings:       {savings*365:.2f} kr/year

PEAK LOAD
  Worst Peak:           {worst_peak:.2f} kWh
  Optimal Peak:         {optimal_peak:.2f} kWh
  Reduction:            {worst_peak - optimal_peak:.2f} kWh ({(worst_peak-optimal_peak)/worst_peak*100:.1f}%)

METHOD
  Each household is optimized independently using
  the MILP solver from Question 2.  Shiftable loads
  are shifted to the cheapest available hours."""

        plt.text(0.05, 0.05, summary, fontsize=10, verticalalignment='bottom',
                 family='monospace',
                 bbox=dict(boxstyle='round', facecolor='white'))

        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '01_q3_summary.png'),
                    dpi=300, bbox_inches='tight')
        plt.close()

        # ── PAGE 2 — Pricing Curve + Scheduling Strategy ────────────
        # (Matching the Q2 colour scheme from generate_pricing_figures.py)

        # Time-period zone definitions (same as Q2)
        periods = [
            {'name': 'Night\n(Cheapest)',  'start': 0,  'end': 7,  'color': '#4CAF50', 'alpha': 0.15},
            {'name': 'Morning\n(Rising)',   'start': 7,  'end': 10, 'color': '#FFC107', 'alpha': 0.15},
            {'name': 'Daytime\n(Moderate)', 'start': 10, 'end': 17, 'color': '#2196F3', 'alpha': 0.15},
            {'name': 'Peak\n(Expensive)',   'start': 17, 'end': 22, 'color': '#F44336', 'alpha': 0.20},
            {'name': 'Evening\n(Moderate)', 'start': 22, 'end': 23, 'color': '#9C27B0', 'alpha': 0.15},
        ]

        fig, axes = plt.subplots(3, 1, figsize=(14, 14),
                                 gridspec_kw={'height_ratios': [3, 1.2, 1.2]},
                                 sharex=True)

        ax_price, ax_ev, ax_noev = axes

        # --- Top: Pricing curve with all 5 coloured zones ---
        for p in periods:
            ax_price.axvspan(p['start'], p['end'], alpha=p['alpha'],
                             color=p['color'], zorder=0)
            # Period label at top of chart
            mid = (p['start'] + p['end']) / 2
            ax_price.text(mid, ax_price.get_ylim()[1] if ax_price.get_ylim()[1] > 0 else 2.35,
                          p['name'], ha='center', va='top', fontsize=8, fontweight='bold',
                          color=p['color'],
                          bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                    edgecolor=p['color'], alpha=0.8))

        ax_price.plot(hours, prices, linewidth=3, color='#1976D2',
                      marker='o', markersize=6, markerfacecolor='white',
                      markeredgewidth=2, markeredgecolor='#1976D2',
                      label='Electricity Price', zorder=5)
        ax_price.fill_between(hours, prices, alpha=0.20, color='#1976D2')

        for h in hours:
            ax_price.text(h, prices[h] + 0.06, f'{prices[h]:.2f}',
                          ha='center', va='bottom', fontsize=7,
                          fontweight='bold', color='#333')

        # Reference lines
        ax_price.axhline(y=1.0, color='green', linestyle='--', lw=1.5, alpha=0.5,
                         label='~1.00 NOK (Night baseline)')
        ax_price.axhline(y=2.0, color='red', linestyle='--', lw=1.5, alpha=0.5,
                         label='~2.00 NOK (Peak baseline)')

        ax_price.set_ylabel('Price (NOK/kWh)', fontsize=12, fontweight='bold')
        ax_price.set_title(
            'Pricing Curve and Optimal Appliance Scheduling Strategy\n'
            '(Example Household Schedules)', fontsize=14, fontweight='bold')
        ax_price.set_ylim(0, 2.5)
        ax_price.grid(True, alpha=0.3, linestyle=':')
        ax_price.legend(loc='upper right', fontsize=9)

        # Re-draw period labels now that ylim is set
        for p in periods:
            mid = (p['start'] + p['end']) / 2
            ax_price.text(mid, 2.38, p['name'], ha='center', va='top',
                          fontsize=8, fontweight='bold', color=p['color'],
                          bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                    edgecolor=p['color'], alpha=0.8))

        # --- Helper: draw Gantt bars for one household ---
        def _draw_gantt(ax, household, label_bg_color):
            hh_id = household['id']
            schedule = schedules[hh_id]
            app_map = {a['name']: a for a in household['shiftable']}

            # Coloured zone backgrounds on Gantt rows too
            for p in periods:
                ax.axvspan(p['start'], p['end'], alpha=p['alpha'] * 0.6,
                           color=p['color'], zorder=0)

            # Non-shiftable bar (full width, at bottom)
            ax.barh(0, 24, left=-0.5, height=0.4, color=BASE_COLOR, alpha=0.5,
                    edgecolor='black', linewidth=1.0)
            ax.text(12, 0, 'Non-shiftable (base load)', ha='center', va='center',
                    fontsize=8, color='white', fontweight='bold')

            row = 1
            for name in ['EV Charging', 'Dishwasher', 'Laundry', 'Dryer']:
                if name not in schedule:
                    continue
                app = app_map[name]
                start, end = _schedule_to_block(schedule[name], app)
                if end <= start:
                    width = (24 - start) + end
                else:
                    width = end - start
                ax.barh(row, width, left=start, height=0.4,
                        color=COLORS[name], alpha=0.85,
                        edgecolor='black', linewidth=1.5)
                label_text = ABBREV[name] if name != 'EV Charging' else 'EV Charging'
                ax.text(start + width / 2, row, label_text,
                        ha='center', va='center', fontsize=8,
                        fontweight='bold', color='white')
                row += 1

            ax.set_yticks([])
            ax.set_xlim(-2, 24)
            ax.set_ylim(-0.5, row + 0.1)
            ax.invert_yaxis()
            ax.grid(axis='x', alpha=0.3, linestyle=':')

            # Label on left (matching Q2 style)
            ev_str = "With EV" if household['has_ev'] else "No EV"
            pct_str = f"{num_ev/num_hh*100:.1f}%" if household['has_ev'] else f"{(num_hh-num_ev)/num_hh*100:.1f}%"
            ax.text(-1.5, row / 2, f"Household {hh_id}\n({ev_str})\n{pct_str} of\nhouseholds",
                    ha='right', va='center', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor=label_bg_color, alpha=0.7))

        # Pick one household WITH EV and one WITHOUT
        hh_with_ev = next((h for h in households if h['has_ev']), None)
        hh_no_ev   = next((h for h in households if not h['has_ev']), None)

        if hh_with_ev:
            _draw_gantt(ax_ev, hh_with_ev, 'lightgreen')
        if hh_no_ev:
            _draw_gantt(ax_noev, hh_no_ev, 'lightblue')

        ax_noev.set_xlabel('Hour of Day', fontsize=12, fontweight='bold')
        ax_noev.set_xticks(hours)
        ax_noev.set_xticklabels([f'{h:02d}:00' for h in hours], rotation=45, fontsize=8)

        fig.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '02_q3_scheduling_strategy.png'),
                    dpi=300, bbox_inches='tight')
        plt.close()

        # ── PAGE 3 — Aggregated Neighborhood Load: Worst vs Optimal ─
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), sharey=True)

        # Helper to build stacked neighbourhood load
        def _plot_neighborhood_stacked(ax, households, schedules_or_worst, title, is_worst=False):
            from data_setup import calculate_base_load, get_non_shiftable_appliances
            from helpers import add_appliance_to_load

            # Aggregate base load
            total_base = [0.0] * 24
            for hh in households:
                for h in range(24):
                    total_base[h] += hh['base_load'][h]

            ax.bar(hours, total_base, label='Non-shiftable', alpha=0.8, color=BASE_COLOR)
            bottom = total_base[:]

            # Aggregate each appliance type across all households
            for app_name in ['Dishwasher', 'Laundry', 'Dryer', 'EV Charging']:
                agg = [0.0] * 24
                for hh in households:
                    app = next((a for a in hh['shiftable'] if a['name'] == app_name), None)
                    if app is None:
                        continue
                    if is_worst:
                        worst_times = {
                            'Dishwasher': 20, 'Laundry': 18,
                            'Dryer': 20, 'EV Charging': 18
                        }
                        load = [0.0] * 24
                        add_appliance_to_load(load, worst_times[app_name],
                                              app['duration'], app['energy'])
                    else:
                        schedule = schedules_or_worst[hh['id']]
                        value = schedule.get(app_name)
                        if value is None:
                            continue
                        load = _load_from_schedule_value(value, app)
                    for h in range(24):
                        agg[h] += load[h]

                ax.bar(hours, agg, bottom=bottom, label=app_name,
                       alpha=0.9, color=COLORS[app_name])
                bottom = [bottom[h] + agg[h] for h in range(24)]

            peak = max(bottom)
            ax.axhline(y=peak, color='red', linestyle='--', alpha=0.6, lw=1.5,
                       label=f'Peak: {peak:.1f} kWh')

            ax.set_xlabel('Hour', fontsize=11, fontweight='bold')
            ax.set_ylabel('Neighborhood Load (kWh)', fontsize=11, fontweight='bold')
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.set_xticks(hours)
            ax.set_xticklabels([f'{h:02d}' for h in hours], rotation=45, fontsize=8)
            ax.legend(fontsize=8, loc='upper left')
            ax.grid(axis='y', alpha=0.3)

        _plot_neighborhood_stacked(ax1, households, None,
                                   f'Worst Schedule ({num_hh} households)', is_worst=True)
        _plot_neighborhood_stacked(ax2, households, schedules,
                                   f'Optimal Schedule ({num_hh} households)', is_worst=False)

        fig.suptitle('Neighborhood Load Distribution — Worst vs Optimal',
                     fontsize=15, fontweight='bold', y=1.02)
        fig.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '03_q3_load_comparison.png'),
                    dpi=300, bbox_inches='tight')
        plt.close()

        # ── PAGE 4 — Load Overlay (line chart) ──────────────────────
        fig = plt.figure(figsize=(14, 6))
        plt.plot(hours, worst_load, 'o-', color='#E76F51', lw=2.5, ms=5,
                 label=f'Worst (peak {worst_peak:.1f} kWh)')
        plt.plot(hours, optimal_load, 's-', color='#2A9D8F', lw=2.5, ms=5,
                 label=f'Optimal (peak {optimal_peak:.1f} kWh)')

        # Base-load reference
        total_base = [0.0] * 24
        for hh in households:
            for h in range(24):
                total_base[h] += hh['base_load'][h]
        plt.plot(hours, total_base, '--', color=BASE_COLOR, lw=1.5, alpha=0.7,
                 label='Non-shiftable base')

        plt.xlabel('Hour', fontsize=12, fontweight='bold')
        plt.ylabel('Neighborhood Load (kWh)', fontsize=12, fontweight='bold')
        plt.title('Worst vs Optimal — Aggregate Load Profile', fontsize=14, fontweight='bold')
        plt.xticks(hours, [f'{h:02d}:00' for h in hours], rotation=45)
        plt.legend(fontsize=11, loc='upper left')
        plt.grid(axis='both', alpha=0.3, linestyle='--')
        plt.tight_layout()

        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '04_q3_load_overlay.png'),
                    dpi=300, bbox_inches='tight')
        plt.close()

        # ── PAGE 5 — Combined: Price + Optimal Load + Hourly Cost ───
        fig, ax_load = plt.subplots(figsize=(14, 7))
        ax_price = ax_load.twinx()

        hourly_costs = [optimal_load[h] * prices[h] for h in range(24)]

        # Stacked bars
        total_base = [0.0] * 24
        for hh in households:
            for h in range(24):
                total_base[h] += hh['base_load'][h]

        ax_load.bar(hours, total_base, width=0.7, label='Non-shiftable',
                    alpha=0.8, color=BASE_COLOR)
        bottom = total_base[:]
        for app_name in ['Dishwasher', 'Laundry', 'Dryer', 'EV Charging']:
            agg = [0.0] * 24
            for hh in households:
                app = next((a for a in hh['shiftable'] if a['name'] == app_name), None)
                if app is None:
                    continue
                schedule = schedules[hh['id']]
                value = schedule.get(app_name)
                if value is None:
                    continue
                load = _load_from_schedule_value(value, app)
                for h in range(24):
                    agg[h] += load[h]
            ax_load.bar(hours, agg, width=0.7, bottom=bottom,
                        label=app_name, alpha=0.9, color=COLORS[app_name])
            bottom = [bottom[h] + agg[h] for h in range(24)]

        # Hourly cost labels
        for h in hours:
            if hourly_costs[h] > 0.1:
                ax_load.text(h, optimal_load[h] + 0.3, f'{hourly_costs[h]:.1f} kr',
                             ha='center', va='bottom', fontsize=6.5,
                             fontweight='bold', color='#333333')

        # Price line
        line = ax_price.plot(hours, prices, lw=2.5, color='#E76F51',
                             marker='o', ms=5, label='Spot Price', zorder=5)
        for h in hours:
            ax_price.text(h, prices[h] + 0.02, f'{prices[h]:.2f}',
                          ha='center', va='bottom', fontsize=6.5,
                          color='#E76F51', fontweight='bold')

        ax_load.set_xlabel('Hour', fontsize=12, fontweight='bold')
        ax_load.set_ylabel('Neighborhood Load (kWh)', fontsize=12, fontweight='bold')
        ax_price.set_ylabel('Spot Price (NOK/kWh)', fontsize=12, fontweight='bold',
                            color='#E76F51')
        ax_price.tick_params(axis='y', labelcolor='#E76F51')
        ax_load.set_xticks(hours)
        ax_load.set_xticklabels([f'{h:02d}:00' for h in hours], rotation=45)
        ax_load.grid(axis='y', alpha=0.2, linestyle='--')
        ax_load.set_title('Neighborhood Optimal Schedule — Price, Load & Hourly Cost',
                          fontsize=14, fontweight='bold', pad=12)
        y_max = max(optimal_load) * 1.25
        ax_load.set_ylim(0, y_max)
        ax_price.set_ylim(0, max(prices) * 1.30)

        h_load, l_load = ax_load.get_legend_handles_labels()
        h_price, l_price = ax_price.get_legend_handles_labels()
        ax_load.legend(h_load + h_price, l_load + l_price,
                       loc='upper right', fontsize=9)

        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '05_q3_combined_overview.png'),
                    dpi=300, bbox_inches='tight')
        plt.close()

        # ── PAGE 6 — Cost Comparison Bar Chart ──────────────────────
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Total cost
        cats = ['Worst', 'Optimal']
        vals = [worst_cost, optimal_cost]
        bar_c = ['#E76F51', '#5AC768']
        bars = ax1.bar(cats, vals, color=bar_c, alpha=0.85)
        for bar, val in zip(bars, vals):
            ax1.text(bar.get_x() + bar.get_width()/2., val,
                     f'{val:.2f} kr', ha='center', va='bottom',
                     fontsize=12, fontweight='bold')
        ax1.set_ylabel('Cost (kr/day)', fontsize=12, fontweight='bold')
        ax1.set_title(f'Neighborhood Total Cost ({num_hh} households)',
                      fontsize=13, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)

        # Peak load
        peaks = [worst_peak, optimal_peak]
        bars = ax2.bar(cats, peaks, color=bar_c, alpha=0.85)
        for bar, val in zip(bars, peaks):
            ax2.text(bar.get_x() + bar.get_width()/2., val,
                     f'{val:.1f} kWh', ha='center', va='bottom',
                     fontsize=12, fontweight='bold')
        ax2.set_ylabel('Peak Load (kWh)', fontsize=12, fontweight='bold')
        ax2.set_title('Neighborhood Peak Load', fontsize=13, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)

        fig.suptitle('Worst vs Optimal — Cost & Peak Comparison',
                     fontsize=15, fontweight='bold', y=1.02)
        fig.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, '06_q3_cost_peak_bars.png'),
                    dpi=300, bbox_inches='tight')
        plt.close()

        # Metadata
        d = pdf.infodict()
        d['Title'] = 'Q3: Neighborhood Optimization Report'
        d['CreationDate'] = datetime.now()

    print(f"✅ PDF saved: {filename}")
    print(f"✅ Images saved in: {output_folder}/")
