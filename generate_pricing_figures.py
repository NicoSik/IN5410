"""
Generate pricing curve visualization for documentation.
This creates a standalone figure showing the Real-Time Pricing (RTP) scheme.
"""

import matplotlib.pyplot as plt
from data_setup import generate_prices

def plot_pricing_curve_detailed():
    """Create detailed pricing curve visualization with annotations."""
    
    prices = generate_prices(seed=42)
    hours = list(range(24))
    
    # Create figure - wide to fill the page
    fig, ax = plt.subplots(figsize=(18, 8))
    
    # Define time periods with colors (start/end are boundary points)
    periods = [
        {'name': 'Night\n(Cheapest)', 'start': 0, 'end': 7, 'color': '#4CAF50', 'alpha': 0.15},
        {'name': 'Morning\n(Rising)', 'start': 7, 'end': 10, 'color': '#FFC107', 'alpha': 0.15},
        {'name': 'Daytime\n(Moderate)', 'start': 10, 'end': 17, 'color': '#2196F3', 'alpha': 0.15},
        {'name': 'Peak\n(Expensive)', 'start': 17, 'end': 22, 'color': '#F44336', 'alpha': 0.2},
        {'name': 'Evening\n(Moderate)', 'start': 22, 'end': 23, 'color': '#9C27B0', 'alpha': 0.15},
    ]
    
    # Shade time periods
    for period in periods:
        ax.axvspan(period['start'], period['end'], 
                  alpha=period['alpha'], color=period['color'])
        
        # Add text label in the middle of each period
        mid_point = (period['start'] + period['end']) / 2
        ax.text(mid_point, 2.35, period['name'], 
               ha='center', va='top', fontsize=10, fontweight='bold',
               color=period['color'].replace('0.15', '1').replace('0.2', '1'),
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                        edgecolor=period['color'], alpha=0.8))
    
    # Plot price curve
    ax.plot(hours, prices, linewidth=3, color='#1976D2', marker='o', 
           markersize=8, markerfacecolor='white', markeredgewidth=2,
           markeredgecolor='#1976D2', label='Spot Price', zorder=5)
    
    # Add price labels for each hour
    for h in hours:
        ax.text(h, prices[h] + 0.08, f'{prices[h]:.2f}', 
               ha='center', va='bottom', fontsize=8, fontweight='bold',
               color='#333')
    
    # Add horizontal lines for reference
    ax.axhline(y=1.0, color='green', linestyle='--', linewidth=1.5, alpha=0.5, label='~1.00 NOK (Night baseline)')
    ax.axhline(y=2.0, color='red', linestyle='--', linewidth=1.5, alpha=0.5, label='~2.00 NOK (Peak baseline)')
    
    # Formatting
    ax.set_xlabel('Hour of Day', fontsize=14, fontweight='bold')
    ax.set_ylabel('Price (NOK/kWh)', fontsize=14, fontweight='bold')
    ax.set_title('Real-Time Pricing (RTP) Curve\nNorwegian Spot Prices - Winter 2026', 
                fontsize=16, fontweight='bold', pad=20)
    
    ax.set_xticks(hours)
    ax.set_xticklabels([f'{h:02d}:00' for h in hours], rotation=45, ha='right')
    ax.set_xlim(0, 23)
    ax.set_ylim(0.5, 2.5)
    ax.margins(x=0)
    
    ax.grid(True, alpha=0.3, linestyle=':', linewidth=1)
    
    # Create legend in lower left to avoid overlap with time period labels
    ax.legend(loc='lower left', fontsize=10, framealpha=0.95)
    
    # Add statistics box
    stats_text = f"""Statistics:
Min: {min(prices):.2f} NOK/kWh
Max: {max(prices):.2f} NOK/kWh
Avg: {sum(prices)/len(prices):.2f} NOK/kWh
Range: {max(prices) - min(prices):.2f} NOK/kWh"""
    
    ax.text(0.98, 0.02, stats_text, transform=ax.transAxes,
           fontsize=11, verticalalignment='bottom', horizontalalignment='right',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
           family='monospace')
    
    plt.tight_layout()
    return fig


def plot_optimization_strategy():
    """Show optimal appliance scheduling strategy based on pricing."""
    
    prices = generate_prices(seed=42)
    hours = list(range(24))
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12), sharex=True)
    
    # Top plot: Pricing curve
    ax1.plot(hours, prices, linewidth=3, color='#1976D2', marker='o', 
            markersize=6, label='Electricity Price')
    ax1.fill_between(hours, prices, alpha=0.3, color='#1976D2')
    
    # Highlight peak hours
    ax1.axvspan(17, 22, alpha=0.2, color='red', label='Peak Hours (AVOID)')
    ax1.axvspan(0, 7, alpha=0.15, color='green', label='Night (CHEAP)')
    
    ax1.set_ylabel('Price (NOK/kWh)', fontsize=12, fontweight='bold')
    ax1.set_title('Pricing Curve and Optimal Appliance Scheduling Strategy\n(Example Household Schedules)', 
                 fontsize=14, fontweight='bold', pad=15)
    ax1.legend(loc='upper right', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Bottom plot: Scheduling examples for different household types
    
    # Household 1: Without EV (3 appliances)
    household1_schedules = {
        'H1: Non-shiftable (base load)': {'start': 0, 'duration': 24, 'color': '#6C757D', 'height': 0.4},
        'H1: Dishwasher': {'start': 1, 'duration': 2, 'color': '#C44536', 'height': 0.4},
        'H1: Laundry': {'start': 12, 'duration': 2, 'color': '#2A9D8F', 'height': 0.4},
        'H1: Dryer': {'start': 12, 'duration': 2, 'color': '#E9C46A', 'height': 0.4},
    }
    
    # Household 2: With EV (4 appliances)
    household2_schedules = {
        'H2: Non-shiftable (base load)': {'start': 0, 'duration': 24, 'color': '#6C757D', 'height': 0.4},
        'H2: EV Charging': {'start': 0, 'duration': 6, 'color': '#457B9D', 'height': 0.4},
        'H2: Dishwasher': {'start': 1, 'duration': 2, 'color': '#C44536', 'height': 0.4},
        'H2: Laundry': {'start': 12, 'duration': 2, 'color': '#2A9D8F', 'height': 0.4},
        'H2: Dryer': {'start': 12, 'duration': 2, 'color': '#E9C46A', 'height': 0.4},
    }
    
    # Abbreviations for labels inside bars
    abbrev = {
        'Non-shiftable (base load)': 'Non-shiftable (base load)',
        'Dishwasher': 'DW',
        'Laundry': 'LN',
        'Dryer': 'DR',
        'EV Charging': 'EV Charging',
    }
    
    y_pos = 0
    
    # Plot Household 1 (without EV)
    for name, info in household1_schedules.items():
        ax2.barh(y_pos, info['duration'], left=info['start'], 
                height=info['height'], color=info['color'], alpha=0.85, 
                edgecolor='black', linewidth=1.5)
        
        # Add label inside bar
        short_name = name.split(': ')[1]
        label = abbrev.get(short_name, short_name)
        mid_point = info['start'] + info['duration']/2
        ax2.text(mid_point, y_pos, label, 
                ha='center', va='center', fontweight='bold', 
                fontsize=8, color='white')
        y_pos += 0.6
    
    # Add separator
    y_pos += 0.3
    
    # Plot Household 2 (with EV)
    for name, info in household2_schedules.items():
        ax2.barh(y_pos, info['duration'], left=info['start'], 
                height=info['height'], color=info['color'], alpha=0.85, 
                edgecolor='black', linewidth=1.5)
        
        # Add label inside bar
        short_name = name.split(': ')[1]
        label = abbrev.get(short_name, short_name)
        mid_point = info['start'] + info['duration']/2
        ax2.text(mid_point, y_pos, label, 
                ha='center', va='center', fontweight='bold', 
                fontsize=8, color='white')
        y_pos += 0.6
    
    # Add household labels on the left
    ax2.text(-1.5, 1.0, 'Household 1\n(No EV)\n46.7% of\nhouseholds', 
            ha='right', va='center', fontsize=10, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.7))
    
    ax2.text(-1.5, 3.3, 'Household 2\n(With EV)\n53.3% of\nhouseholds', 
            ha='right', va='center', fontsize=10, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.7))
    
    ax2.set_xlabel('Hour of Day', fontsize=12, fontweight='bold')
    ax2.set_ylabel('', fontsize=12, fontweight='bold')
    ax2.set_yticks([])
    ax2.set_xticks(hours)
    ax2.set_xticklabels([f'{h:02d}:00' for h in hours], rotation=45, ha='right')
    ax2.set_xlim(-2, 24)
    ax2.axvspan(17, 22, alpha=0.1, color='red')  # Show peak hours
    ax2.axvspan(0, 7, alpha=0.1, color='green')  # Show night hours
    ax2.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    return fig


def main():
    """Generate all pricing visualizations."""
    
    print("📊 Generating pricing curve visualizations...")
    
    # Create output directory
    import os
    os.makedirs('figures', exist_ok=True)
    
    # Generate detailed pricing curve
    print("  1. Creating detailed pricing curve...")
    fig1 = plot_pricing_curve_detailed()
    fig1.savefig('figures/pricing_curve_detailed.png', dpi=300, bbox_inches='tight')
    plt.close(fig1)
    print("     ✅ Saved: figures/pricing_curve_detailed.png")
    
    # Generate optimization strategy visualization
    print("  2. Creating optimization strategy visualization...")
    fig2 = plot_optimization_strategy()
    fig2.savefig('figures/optimization_strategy.png', dpi=300, bbox_inches='tight')
    plt.close(fig2)
    print("     ✅ Saved: figures/optimization_strategy.png")
    
    print("\n✅ All figures generated successfully!")
    print("\nFigures created:")
    print("  - figures/pricing_curve_detailed.png")
    print("  - figures/optimization_strategy.png")


if __name__ == "__main__":
    main()
