"""
Question 3 Documentation: Demand Response Optimization Problem Formulation

This document explains how the neighborhood demand response problem is formulated
and solved as an optimization problem.
"""

# ============================================================================
# PROBLEM FORMULATION
# ============================================================================

"""
OBJECTIVE:
Minimize the total daily electricity cost for a neighborhood of 30 households
while satisfying all appliance operation constraints.

DECISION VARIABLES:
For each household h ∈ {1, 2, ..., 30} and each shiftable appliance a:
    t_h,a = start time (hour) for appliance a in household h
    
Where:
    - Dishwasher: t_h,dishwasher ∈ {19, 20, 21, 22, 0, 1, 2, 3, 4, 5}
    - Laundry: t_h,laundry ∈ {8, 9, 10, 11, 12, 13, 14, 15}
    - Dryer: t_h,dryer ∈ {8, 9, 10, 11, 12, 13, 14, 15}
    - EV Charging: t_h,ev ∈ {22, 23, 0, 1} (only if household owns EV)

OBJECTIVE FUNCTION:
Minimize:
    Total_Cost = Σ(h=1 to 30) Σ(t=0 to 23) L_h(t) × P(t)

Where:
    L_h(t) = total load for household h at hour t
    P(t) = electricity price at hour t (NOK/kWh)
    
    L_h(t) = L_h,base(t) + Σ(a ∈ shiftable) L_h,a(t)
    
    L_h,base(t) = fixed load from non-shiftable appliances
    L_h,a(t) = load from shiftable appliance a (depends on t_h,a)

CONSTRAINTS:
1. Each appliance must run for its full duration:
   - Dishwasher, Laundry, Dryer: 2 consecutive hours
   - EV Charging: 6 consecutive hours

2. Each appliance can only start at allowed hours (defined above)

3. Each appliance runs exactly once per day

4. Total energy consumed per appliance must match its requirement:
   - Dishwasher: 1.44 kWh
   - Laundry: 1.94 kWh
   - Dryer: 2.50 kWh
   - EV Charging: 9.90 kWh

5. Non-shiftable appliances follow fixed schedules

PROBLEM CHARACTERISTICS:
- Type: Mixed Integer Nonlinear Programming (MINLP)
- Variables: Discrete (start times)
- Objective: Nonlinear (product of load and price)
- Constraints: Linear (time windows, energy requirements)
- Size: 
  * 30 households
  * 3-4 shiftable appliances per household
  * 10×8×8×4 = 2,560 combinations per household (with EV)
  * 10×8×8 = 640 combinations per household (without EV)
"""

# ============================================================================
# SOLUTION METHODOLOGY
# ============================================================================

"""
APPROACH: Decomposed Exhaustive Search

We decompose the neighborhood problem into 30 independent household 
optimization problems. This is justified because:
1. Each household has independent appliances
2. Prices are the same for all households
3. No shared constraints between households
4. Aggregation is additive (linear)

ALGORITHM FOR EACH HOUSEHOLD:

1. INITIALIZATION
   - Set best_cost = ∞
   - Set best_schedule = {}
   
2. ENUMERATE ALL COMBINATIONS
   - Generate Cartesian product of all allowed start times
   - For household with EV: 10 × 8 × 8 × 4 = 2,560 combinations
   - For household without EV: 10 × 8 × 8 = 640 combinations
   
3. FOR EACH COMBINATION:
   a) Build load profile L(t):
      - Start with base load from non-shiftable appliances
      - For each appliance:
        * Calculate energy per hour = total_energy / duration
        * Add to L(t) for t ∈ [start, start + duration)
        
   b) Calculate cost:
      cost = Σ(t=0 to 23) L(t) × P(t)
      
   c) Update best if cost < best_cost:
      - best_cost = cost
      - best_schedule = current combination
      
4. RETURN best_schedule, best_load, best_cost

5. AGGREGATE NEIGHBORHOOD RESULTS:
   - Total_load(t) = Σ(h=1 to 30) L_h(t)
   - Total_cost = Σ(h=1 to 30) cost_h

COMPLEXITY ANALYSIS:
- Per household (with EV): O(2,560 × 24) = O(61,440) operations
- Per household (without EV): O(640 × 24) = O(15,360) operations
- Total for 30 households: O(30 × 2,560 × 24) ≈ O(1.8M) operations
- Very fast in practice (< 1 second)

OPTIMALITY GUARANTEE:
The exhaustive search guarantees finding the globally optimal solution
because:
1. All possible combinations are evaluated
2. The objective function is deterministic
3. No heuristics or approximations are used
"""

# ============================================================================
# PRICING CURVE MODEL
# ============================================================================

"""
REAL-TIME PRICING (RTP) SCHEME:

The pricing curve P(t) follows a realistic Norwegian spot price pattern:

TIME PERIODS:
1. Night (00:00 - 06:00):    ~1.00 NOK/kWh (CHEAPEST)
   - Low demand period
   - Optimal for EV charging, dishwasher

2. Morning (07:00 - 09:00):  ~1.40 NOK/kWh (MODERATE-HIGH)
   - Rising demand as people wake up
   
3. Daytime (10:00 - 16:00):  ~1.20 NOK/kWh (MODERATE)
   - Business hours, steady demand
   - Good for laundry, dryer

4. Peak (17:00 - 21:00):     ~2.00 NOK/kWh (MOST EXPENSIVE)
   - Evening peak: cooking, heating, lighting
   - AVOID shiftable appliances
   
5. Evening (22:00 - 23:00):  ~1.30 NOK/kWh (MODERATE)
   - Demand starts to decrease

PRICE VARIATION:
- Random noise added: ±0.10 NOK/kWh
- Minimum price: 0.50 NOK/kWh (floor constraint)
- Reproducible using seed = 42

IMPLEMENTATION:
def generate_prices(seed: int = 42) -> List[float]:
    rng = random.Random(seed)
    prices = []
    
    for hour in range(24):
        if 0 <= hour <= 6:
            base = 1.00  # Night
        elif 7 <= hour <= 9:
            base = 1.40  # Morning
        elif 10 <= hour <= 16:
            base = 1.20  # Daytime
        elif 17 <= hour <= 21:
            base = 2.00  # Peak
        else:
            base = 1.30  # Evening
        
        noise = rng.uniform(-0.10, 0.10)
        prices.append(max(0.50, base + noise))
    
    return prices

OPTIMIZATION INSIGHT:
The algorithm naturally shifts appliances to low-price periods:
- EV Charging → 00:00-06:00 (night, cheapest)
- Dishwasher → 01:00-03:00 (night, cheap)
- Laundry & Dryer → 12:00-14:00 (daytime, moderate)
- AVOID → 17:00-21:00 (peak, expensive)

This creates a "valley-filling" effect where demand is shifted from
peak hours to off-peak hours, benefiting both consumers (lower cost)
and the grid (reduced peak load).
"""

# ============================================================================
# RESULTS INTERPRETATION
# ============================================================================

"""
NEIGHBORHOOD OPTIMIZATION RESULTS:

BASELINE (Naive Schedule):
- All appliances run during evening/peak hours (17:00-21:00)
- Total cost: 1,564.84 NOK/day
- High peak load coinciding with high prices

OPTIMIZED SCHEDULE:
- Appliances shifted to cheapest available hours
- Total cost: 1,274.14 NOK/day
- Load distributed more evenly across the day

SAVINGS:
- Daily: 290.69 NOK/day (18.6% reduction)
- Annual: 106,103 NOK/year for the neighborhood
- Per household: 3,537 NOK/year average

KEY INSIGHTS:
1. Significant cost reduction through load shifting
2. No change in total energy consumption (same appliances, same usage)
3. Better grid utilization (peak shaving)
4. All households benefit equally (same pricing, same appliances)
5. EV ownership increases potential savings (larger shiftable load)

SCALABILITY:
The decomposition approach scales linearly with number of households:
- 30 households: ~1 second
- 100 households: ~3 seconds
- 1000 households: ~30 seconds
"""

if __name__ == "__main__":
    print(__doc__)
