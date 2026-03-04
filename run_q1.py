"""Main program for Question 1 — Simple LP scheduling.

Three appliances (Dishwasher, Washing Machine, EV) with ToU pricing.
Only two constraints: energy equality and power bounds.
"""
from optimize_q1 import get_q1_prices, get_q1_appliances, optimize_q1


def main():
    """Run Q1 energy optimization and print strategy."""

    print("\n" + "=" * 65)
    print("  QUESTION 1 — Minimum Energy Cost with ToU Pricing (LP)")
    print("=" * 65)

    # ── Setup ─────────────────────────────────────────────────────
    prices = get_q1_prices()
    appliances = get_q1_appliances()

    print("\n📊 Time-of-Use Pricing:")
    print("  Off-peak (00–16, 20–23): 0.50 NOK/kWh")
    print("  Peak     (17–19):        1.00 NOK/kWh")

    print("\n⚡ Appliances:")
    for app in appliances:
        print(f"  {app['name']:20s}  E = {app['energy']:5.2f} kWh   "
              f"P_max = {app['p_max']:.2f} kW")
    total_energy = sum(a['energy'] for a in appliances)
    print(f"  {'TOTAL':20s}  E = {total_energy:5.2f} kWh")

    # ── Solve ─────────────────────────────────────────────────────
    print("\n⚙️  Solving LP ...")
    schedule, total_load, total_cost = optimize_q1(prices, appliances)

    # ── Results ───────────────────────────────────────────────────
    print(f"\n✅ Optimal daily cost: {total_cost:.2f} NOK")

    # Worst-case cost: all energy at peak price
    worst_cost = total_energy * 1.0
    best_possible = total_energy * 0.5
    print(f"   Worst-case cost (all peak):     {worst_cost:.2f} NOK")
    print(f"   Best-possible cost (all off-peak): {best_possible:.2f} NOK")

    # ── Strategy summary per appliance ────────────────────────────
    print("\n" + "-" * 65)
    print("  OPTIMAL SCHEDULING STRATEGY")
    print("-" * 65)

    for app in appliances:
        name = app['name']
        profile = schedule[name]
        print(f"\n  {name}  (E = {app['energy']} kWh, P_max = {app['p_max']} kW)")

        active_hours = [(h, profile[h]) for h in range(24) if profile[h] > 1e-6]
        if active_hours:
            for h, p in active_hours:
                tag = " ← PEAK" if 17 <= h <= 19 else ""
                print(f"    Hour {h:2d}:00  →  {p:.4f} kW{tag}")
        else:
            print("    (not scheduled)")

        energy_check = sum(profile)
        peak_energy = sum(profile[h] for h in range(17, 20))
        offpeak_energy = energy_check - peak_energy
        print(f"    Total energy: {energy_check:.2f} kWh  "
              f"(off-peak: {offpeak_energy:.2f}, peak: {peak_energy:.2f})")

    # ── Hourly load table ─────────────────────────────────────────
    print("\n" + "-" * 65)
    print("  HOURLY LOAD PROFILE (kW)")
    print("-" * 65)
    print(f"  {'Hour':>5s}  {'Price':>6s}  ", end="")
    for app in appliances:
        print(f"{app['name'][:6]:>8s}  ", end="")
    print(f"{'Total':>8s}  {'Cost':>7s}")
    print("  " + "-" * 60)

    total_cost_check = 0.0
    for h in range(24):
        p = prices[h]
        row_cost = p * total_load[h]
        total_cost_check += row_cost
        tag = " *" if 17 <= h <= 19 else "  "
        print(f"  {h:5d}{tag} {p:6.2f}  ", end="")
        for app in appliances:
            print(f"{schedule[app['name']][h]:8.4f}  ", end="")
        print(f"{total_load[h]:8.4f}  {row_cost:7.4f}")

    print("  " + "-" * 60)
    print(f"  {'TOTAL':>7s} {' ':>6s}  ", end="")
    for app in appliances:
        e = sum(schedule[app['name']])
        print(f"{e:8.2f}  ", end="")
    print(f"{sum(total_load):8.2f}  {total_cost_check:7.2f} NOK")

    # ── Discussion ────────────────────────────────────────────────
    print("\n" + "-" * 65)
    print("  STRATEGY DISCUSSION")
    print("-" * 65)

    # Check if any energy is scheduled during peak
    peak_total = sum(total_load[h] for h in range(17, 20))
    if peak_total < 1e-6:
        print("\n  ✅ All energy is scheduled during off-peak hours.")
        print("     The LP avoids peak hours entirely since off-peak price")
        print("     (0.50 NOK/kWh) is strictly cheaper than peak (1.00 NOK/kWh).")
    else:
        print(f"\n  ⚠️  {peak_total:.2f} kWh scheduled during peak hours.")
        print("     This happens when off-peak capacity is insufficient.")

    # Check load distribution
    max_load = max(total_load)
    print(f"\n  Peak combined load: {max_load:.2f} kW")
    combined_pmax = sum(a['p_max'] for a in appliances)
    print(f"  Sum of P_max:       {combined_pmax:.2f} kW")

    off_peak_hours = 21  # hours 0-16, 20-23
    capacity_offpeak = combined_pmax * off_peak_hours
    print(f"\n  Off-peak capacity:  {combined_pmax:.1f} kW × {off_peak_hours}h "
          f"= {capacity_offpeak:.1f} kWh")
    print(f"  Total energy need:  {total_energy:.2f} kWh")

    if total_energy <= capacity_offpeak:
        print("  → Enough off-peak capacity: no need to run during peak.")
    else:
        overflow = total_energy - capacity_offpeak
        print(f"  → {overflow:.2f} kWh must spill into peak hours.")

    print(f"\n  Is it reasonable to run all 3 appliances at the same time?")
    print(f"  → With only power-bound constraints (no contiguity), the LP")
    print(f"    distributes load freely. Running all 3 at once is fine as")
    print(f"    long as each stays within its P_max. The LP naturally")
    print(f"    spreads energy across the cheapest hours to minimise cost.")

    print("\n" + "=" * 65)

    # ── Generate plot ─────────────────────────────────────────────
    try:
        from plot_q1 import plot_q1_schedule
        plot_q1_schedule(schedule, appliances, prices, filename="q1_schedule.png")
    except Exception as e:
        print(f"\n⚠️  Could not generate plot: {e}")


if __name__ == "__main__":
    main()
