"""Question 1 — Bar chart of optimal appliance scheduling.

Shows each appliance's hourly power as stacked bars with peak hours
highlighted in a shaded region.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


def plot_q1_schedule(schedule, appliances, prices, filename="q1_schedule.png"):
    """
    Create a bar chart showing when each appliance runs,
    with the peak-hour region highlighted.

    Args:
        schedule:   {name: [e_0 ... e_23]} from optimize_q1
        appliances: list of {name, energy, p_max}
        prices:     24-element ToU prices
        filename:   output image path
    """
    H = 24
    hours = np.arange(H)
    bar_width = 0.8

    # Colours matching the screenshot style
    colors = {
        'EV Charging':     '#5b9bd5',   # blue
        'Washing Machine': '#70c1a0',   # green
        'Dishwasher':      '#e8a854',   # orange
    }

    fig, ax = plt.subplots(figsize=(14, 6))

    # ── Peak-hour shading (17:00–20:00) ───────────────────────────
    ax.axvspan(16.5, 19.5, color='#ffb3b3', alpha=0.35, zorder=0,
               label='Peak Hours (17:00-20:00)')
    ax.axvline(16.5, color='red', linestyle='--', linewidth=1.0, alpha=0.7)
    ax.axvline(19.5, color='red', linestyle='--', linewidth=1.0, alpha=0.7)

    # ── Stacked bars ──────────────────────────────────────────────
    # Draw in order: EV (bottom), WM, DW (top) — largest first
    draw_order = ['EV Charging', 'Washing Machine', 'Dishwasher']
    bottom = np.zeros(H)

    for name in draw_order:
        if name not in schedule:
            continue
        profile = np.array(schedule[name])
        app = next(a for a in appliances if a['name'] == name)
        color = colors.get(name, '#aaaaaa')
        label = (f"{name} (Total: {app['energy']} kWh, "
                 f"Max: {app['p_max']} kW)")
        ax.bar(hours, profile, width=bar_width, bottom=bottom,
               color=color, edgecolor='white', linewidth=0.5,
               label=label, zorder=2)
        bottom += profile

    # ── Formatting ────────────────────────────────────────────────
    ax.set_xlabel('Hour of Day', fontsize=12)
    ax.set_ylabel('Power (kW)', fontsize=12)
    ax.set_title('Hourly Electricity Consumption — EV, WM, and DW\n'
                 'with Peak Hours Highlighted', fontsize=14, fontweight='bold')

    ax.set_xticks(hours)
    ax.set_xticklabels([f'{h:02d}:00' for h in hours], rotation=45,
                       ha='right', fontsize=8)
    ax.set_xlim(-0.6, 23.6)
    ax.set_ylim(0, max(bottom) * 1.15)

    # y-axis nice ticks
    y_max = max(bottom)
    if y_max <= 5:
        ax.set_yticks(np.arange(0, y_max + 0.5, 0.5))
    else:
        ax.set_yticks(np.arange(0, y_max + 1.0, 1.0))

    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    fig.tight_layout()
    fig.savefig(filename, dpi=200)
    plt.close(fig)
    print(f"  📈 Saved plot: {filename}")


if __name__ == "__main__":
    from optimize_q1 import get_q1_prices, get_q1_appliances, optimize_q1

    prices = get_q1_prices()
    appliances = get_q1_appliances()
    schedule, total_load, total_cost = optimize_q1(prices, appliances)

    plot_q1_schedule(schedule, appliances, prices, filename="q1_schedule.png")
    print(f"  Total cost: {total_cost:.2f} NOK")
