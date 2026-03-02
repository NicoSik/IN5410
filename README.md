# IN5410 - Energy Optimization Assignment

## Overview
This project implements household and neighborhood energy optimization to minimize electricity costs using Real-Time Pricing (RTP).

## Questions Implemented

### Question 2: Single Household Optimization
Optimizes the schedule of shiftable appliances for a single household to minimize energy costs.

**Features:**
- Non-shiftable appliances (lighting, heating, refrigerator, stove, TV, computers, small appliances)
- Shiftable appliances (dishwasher, laundry, dryer, EV charging)
- Real-Time Pricing with peak/off-peak hours
- Exhaustive search optimization (guaranteed optimal solution)
- PDF report generation with visualizations

**Run:**
```bash
python3 run.py
```

### Question 3: Neighborhood Optimization (30 Households)
Extends Question 2 to optimize energy usage across 30 households with varying EV ownership.

**Features:**
- 30 households with same appliance configurations
- Configurable EV ownership rate (default 50%)
- Independent optimization per household
- Aggregated neighborhood statistics
- Significant cost savings at scale

**Run:**
```bash
python3 run_neighborhood.py
```

### Question 4: Peak Load Optimization (Demand Response)
Reformulates the optimization to minimize both energy cost AND peak load, introducing a peak load variable L.

**Problem Formulation:**

$$\min_{\{s_a\}, L} \quad \sum_{t=0}^{23} L(t) \cdot P(t) \;+\; \lambda \cdot L$$

where:

$$L(t) = L_{\text{base}}(t) + \sum_{a \in \mathcal{A}} \sum_{\tau=0}^{d_a - 1} \frac{E_a}{d_a} \cdot \mathbf{1}_{[(s_a + \tau) \bmod 24 = t]}$$

**Subject to:**

$$L(t) \leq L \quad \forall \; t \in \{0, 1, \ldots, 23\}$$

$$s_a \in \mathcal{H}_a \quad \forall \; a \in \mathcal{A}$$

| Symbol | Description |
|--------|-------------|
| $s_a$ | Start hour of appliance $a$ (decision variable) |
| $L$ | Peak load variable $= \max_t L(t)$ |
| $L(t)$ | Total load at hour $t$ |
| $L_{\text{base}}(t)$ | Non-shiftable base load at hour $t$ |
| $P(t)$ | Electricity price at hour $t$ |
| $E_a$ | Total energy of appliance $a$ (kWh) |
| $d_a$ | Duration of appliance $a$ (hours) |
| $\mathcal{H}_a$ | Set of allowed start hours for appliance $a$ |
| $\mathcal{A}$ | Set of shiftable appliances |
| $\lambda$ | Peak load penalty weight (cost vs. peak trade-off) |

**Key Difference vs Q2:**
- Q2 minimizes **cost only** → concentrates load in cheapest night hours → creates peak of **4.02 kWh**
- Q4 minimizes **cost + peak** → spreads load across day → reduces peak to **2.20 kWh** (45.2% reduction)
- Trade-off: slightly higher cost (+0.97 NOK/day) but much flatter load curve (better grid stability)

**Run:**
```bash
python3 run_q4.py
```

## Results Summary

### Single Household (Question 2)
- Daily savings: ~13.27 NOK/day (22.0%)
- Annual savings: ~4,843 NOK/year

### Neighborhood (Question 3)
- Total daily savings: ~290.69 NOK/day (18.6%)
- Total annual savings: ~106,103 NOK/year
- Average per household: 9.69 NOK/day or 3,537 NOK/year

### Peak Load Optimization (Question 4)
| Metric | Q2 (Cost Only) | Q4 (Cost + Peak) |
|--------|:-:|:-:|
| Daily Cost | 46.64 NOK | 47.60 NOK |
| Peak Load | 4.02 kWh | 2.20 kWh |
| Peak Reduction | — | 45.2% |

**Schedule Comparison:**
| Appliance | Q2 Start | Q4 Start |
|-----------|:---:|:---:|
| Dishwasher | 01:00 | 11:00 |
| Dryer | 00:00 | 15:00 |
| EV Charging | 00:00 | 00:00 |
| Laundry | 12:00 | 13:00 |

Q2 stacks Dishwasher + Dryer + EV in the night hours (cheapest) creating a 4.02 kWh peak.
Q4 keeps EV at night but spreads Dishwasher, Laundry, and Dryer across daytime to flatten the curve.

## Problem Formulation (Question 3)

### Optimization Problem
The demand response problem is formulated as a Mixed Integer Nonlinear Programming (MINLP) problem:

**Objective:** Minimize total daily electricity cost for the neighborhood

**Decision Variables:** Start time for each shiftable appliance in each household

**Constraints:**
- Each appliance must run for its full duration
- Appliances can only start at allowed hours
- Each appliance runs exactly once per day
- Non-shiftable appliances follow fixed schedules

**Solution Method:** Decomposed exhaustive search
- Each household optimized independently (2,560 combinations per household with EV)
- Guaranteed globally optimal solution
- Very fast in practice (< 1 second for 30 households)

See `problem_formulation.py` for detailed mathematical formulation.

### Real-Time Pricing (RTP) Curve

The pricing follows realistic Norwegian spot prices with peak/off-peak structure:

- **Night (00:00-06:00)**: ~1.00 NOK/kWh (CHEAPEST) - optimal for EV charging, dishwasher
- **Morning (07:00-09:00)**: ~1.40 NOK/kWh - rising demand
- **Daytime (10:00-16:00)**: ~1.20 NOK/kWh - good for laundry, dryer
- **Peak (17:00-21:00)**: ~2.00 NOK/kWh (MOST EXPENSIVE) - avoid shiftable appliances
- **Evening (22:00-23:00)**: ~1.30 NOK/kWh - demand decreasing

Generate pricing curve figures:
```bash
python3 generate_pricing_figures.py
```

Figures saved in `figures/`:
- `pricing_curve_detailed.png` - Detailed RTP curve with time periods
- `optimization_strategy.png` - Optimal appliance scheduling strategy

## File Structure

```
IN5410/
├── run.py                        # Question 2 - Single household
├── run_neighborhood.py           # Question 3 - Neighborhood (30 households)
├── run_q4.py                     # Question 4 - Peak load optimization
├── data_setup.py                 # Appliance and price data
├── neighborhood_data.py          # Neighborhood configuration
├── optimize.py                   # Q2 optimizer (cost only)
├── optimize_neighborhood.py      # Q3 neighborhood optimization
├── optimize_peak.py              # Q4 optimizer (cost + peak load)
├── helpers.py                    # Utility functions
├── report_simple.py              # Q2 PDF report generation
├── report_q4.py                  # Q4 PDF report (Q2 vs Q4 comparison)
├── problem_formulation.py        # Mathematical problem formulation
├── generate_pricing_figures.py   # Generate pricing curve visualizations
├── figures/                      # Generated visualization figures
│   ├── pricing_curve_detailed.png
│   └── optimization_strategy.png
└── README.md                     # This file
```

## Dependencies

```bash
pip install matplotlib
```

## Configuration

### EV Ownership Rate
Modify in `run_neighborhood.py`:
```python
ev_ownership_rate = 0.5  # 50% of households own an EV
```

### Number of Households
Modify in `run_neighborhood.py`:
```python
num_households = 30  # Change to desired number
```

### Pricing Seed
Both questions use seed 42 for reproducibility. Change in respective run files if needed.
