"""Generate a flowchart showing the code architecture across all questions."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(18, 13))
ax.set_xlim(0, 18)
ax.set_ylim(0, 13)
ax.axis('off')
fig.patch.set_facecolor('#FAFAFA')

# ── Colour palette ────────────────────────────────────────────
C_RUNNER   = '#4A90D9'   # blue  – runner scripts
C_OPT      = '#E07B54'   # coral – optimizers
C_DATA     = '#5AC768'   # green – data / helpers
C_REPORT   = '#B07CD8'   # purple – reports / plots
C_OUTPUT   = '#F5C242'   # gold  – outputs
C_SHARED   = '#78909C'   # grey  – shared modules
C_ARROW    = '#333333'
TXT        = 'white'

def box(x, y, w, h, label, color, fontsize=9, sublabel=None, alpha=0.92):
    """Draw a rounded box with centred label."""
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.15",
                          facecolor=color, edgecolor='#222222',
                          linewidth=1.2, alpha=alpha, zorder=2)
    ax.add_patch(rect)
    if sublabel:
        ax.text(x + w/2, y + h/2 + 0.15, label,
                ha='center', va='center', fontsize=fontsize,
                fontweight='bold', color=TXT, zorder=3)
        ax.text(x + w/2, y + h/2 - 0.2, sublabel,
                ha='center', va='center', fontsize=fontsize - 2,
                color=TXT, style='italic', zorder=3)
    else:
        ax.text(x + w/2, y + h/2, label,
                ha='center', va='center', fontsize=fontsize,
                fontweight='bold', color=TXT, zorder=3)

def arrow(x1, y1, x2, y2, color=C_ARROW, style='->', lw=1.5):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color,
                                lw=lw, connectionstyle='arc3,rad=0.0'),
                zorder=1)

def arrow_curved(x1, y1, x2, y2, color=C_ARROW, rad=0.15, lw=1.3):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color,
                                lw=lw, connectionstyle=f'arc3,rad={rad}'),
                zorder=1)

# ── Title ─────────────────────────────────────────────────────
ax.text(9, 12.6, 'IN5410 — Code Architecture Flowchart',
        ha='center', va='center', fontsize=18, fontweight='bold',
        color='#222222')
ax.text(9, 12.2, 'Dependency flow between Question 1 – 4',
        ha='center', va='center', fontsize=11, color='#555555')

# ── Column positions  (Q1=2, Q2=6, Q3=10, Q4=14) ────────────
BW = 2.6   # box width
BH = 0.65  # box height

# ===================== SHARED MODULES (bottom row) ============
# data_setup.py
box(5.7, 0.5, BW, BH, 'data_setup.py', C_DATA, sublabel='prices, appliances, base load')
# helpers.py
box(9.7, 0.5, BW, BH, 'helpers.py', C_DATA, sublabel='calculate_cost, format_schedule')
# scipy
box(2.0, 0.5, BW, BH, 'scipy.optimize', C_SHARED, sublabel='linprog / milp (HiGHS)')

ax.text(9, 0.05, '── Shared Modules ──', ha='center', fontsize=9,
        color='#888888', style='italic')

# ===================== Q1 (leftmost column, x≈1.5) ===========
Q1X = 0.7
ax.text(Q1X + BW/2, 11.5, 'Question 1', ha='center', fontsize=13,
        fontweight='bold', color=C_RUNNER)
ax.text(Q1X + BW/2, 11.15, 'LP · ToU · 3 appliances', ha='center',
        fontsize=8, color='#666666')

box(Q1X, 10.0, BW, BH, 'run_q1.py', C_RUNNER, sublabel='entry point')
box(Q1X, 8.6, BW, BH, 'optimize_q1.py', C_OPT, sublabel='LP  (linprog)')
box(Q1X, 7.2, BW, BH, 'plot_q1.py', C_REPORT, sublabel='bar chart + peak zone')
box(Q1X, 5.8, BW, BH, 'q1_schedule.png', C_OUTPUT, sublabel='output image')

arrow(Q1X + BW/2, 10.0, Q1X + BW/2, 8.6 + BH)   # run → optimize
arrow(Q1X + BW/2, 8.6, Q1X + BW/2, 7.2 + BH)     # optimize → plot (via run)
arrow(Q1X + BW/2, 7.2, Q1X + BW/2, 5.8 + BH)      # plot → png
# optimize_q1 → scipy
arrow_curved(Q1X + BW/2, 8.6, 3.3, 0.5 + BH, color='#999999', rad=0.2)

# ===================== Q2 (x≈5) ==============================
Q2X = 4.6
ax.text(Q2X + BW/2, 11.5, 'Question 2', ha='center', fontsize=13,
        fontweight='bold', color=C_RUNNER)
ax.text(Q2X + BW/2, 11.15, 'MILP · RTP · 4 appliances', ha='center',
        fontsize=8, color='#666666')

box(Q2X, 10.0, BW, BH, 'run_q2.py', C_RUNNER, sublabel='entry point')
box(Q2X, 8.6, BW, BH, 'optimize.py', C_OPT, sublabel='MILP  (milp/HiGHS)')
box(Q2X, 7.2, BW, BH, 'report_q2.py', C_REPORT, sublabel='6-page PDF report')
box(Q2X, 5.8, BW, BH, 'q2_energy_report.pdf', C_OUTPUT, sublabel='PDF + images/')

arrow(Q2X + BW/2, 10.0, Q2X + BW/2, 8.6 + BH)
arrow(Q2X + BW/2, 8.6, Q2X + BW/2, 7.2 + BH)
arrow(Q2X + BW/2, 7.2, Q2X + BW/2, 5.8 + BH)
# run_q2 → data_setup
arrow_curved(Q2X + BW/2, 10.0, 7.0, 0.5 + BH, color='#999999', rad=0.15)
# run_q2 → helpers
arrow_curved(Q2X + BW + 0.1, 10.3, 9.7, 0.5 + BH, color='#999999', rad=0.2)
# optimize → scipy
arrow_curved(Q2X, 8.9, 4.6, 0.5 + BH, color='#999999', rad=0.15)
# run_q2 saves prices_q2.json (dashed to Q4)
ax.annotate('', xy=(14.9, 10.0), xytext=(Q2X + BW, 10.3),
            arrowprops=dict(arrowstyle='->', color='#D4A017',
                            lw=1.5, linestyle='dashed',
                            connectionstyle='arc3,rad=-0.12'),
            zorder=1)
ax.text(10.0, 10.7, 'prices_q2.json', fontsize=7, color='#D4A017',
        style='italic', ha='center')

# ===================== Q3 (x≈9) ==============================
Q3X = 8.7
ax.text(Q3X + BW/2, 11.5, 'Question 3', ha='center', fontsize=13,
        fontweight='bold', color=C_RUNNER)
ax.text(Q3X + BW/2, 11.15, 'Neighborhood · 30 houses', ha='center',
        fontsize=8, color='#666666')

box(Q3X, 10.0, BW, BH, 'run_q3.py', C_RUNNER, sublabel='entry point')
box(Q3X, 8.6, BW, BH, 'optimize_nbh_q3.py', C_OPT, sublabel='per-household MILP')
box(Q3X, 7.2, BW, BH, 'neighborhood_data_q3.py', C_DATA, sublabel='30 households, 50% EV')
box(Q3X, 5.8, BW, BH, 'report_q3.py', C_REPORT, sublabel='6-page PDF report')
box(Q3X, 4.4, BW, BH, 'q3_nbh_report.pdf', C_OUTPUT, sublabel='PDF + images/')

arrow(Q3X + BW/2, 10.0, Q3X + BW/2, 8.6 + BH)
arrow(Q3X + BW/2, 10.0, Q3X + BW/2 + 0.0, 7.2 + BH)  # run → nbh_data
arrow(Q3X + BW/2, 8.6, Q3X + BW/2, 5.8 + BH)           # optimize → report (via run)
arrow(Q3X + BW/2, 5.8, Q3X + BW/2, 4.4 + BH)

# optimize_nbh_q3 → optimize.py (reuses Q2 MILP)
ax.annotate('', xy=(Q2X + BW, 8.9), xytext=(Q3X, 8.9),
            arrowprops=dict(arrowstyle='->', color=C_OPT,
                            lw=2.0, connectionstyle='arc3,rad=0.0'),
            zorder=1)
ax.text((Q3X + Q2X + BW) / 2, 9.15, 'calls optimize()', fontsize=7,
        color=C_OPT, ha='center', style='italic')

# ===================== Q4 (x≈13) =============================
Q4X = 12.8
ax.text(Q4X + BW/2, 11.5, 'Question 4', ha='center', fontsize=13,
        fontweight='bold', color=C_RUNNER)
ax.text(Q4X + BW/2, 11.15, 'MILP + peak penalty λ', ha='center',
        fontsize=8, color='#666666')

box(Q4X, 10.0, BW, BH, 'run_q4.py', C_RUNNER, sublabel='entry point')
box(Q4X, 8.6, BW, BH, 'optimize_peak_q4.py', C_OPT, sublabel='MILP + L_peak')
box(Q4X, 7.2, BW, BH, 'report_q4.py', C_REPORT, sublabel='5-page PDF + λ sweep')
box(Q4X, 5.8, BW, BH, 'q4_peak_report.pdf', C_OUTPUT, sublabel='PDF + images/')

arrow(Q4X + BW/2, 10.0, Q4X + BW/2, 8.6 + BH)
arrow(Q4X + BW/2, 8.6, Q4X + BW/2, 7.2 + BH)
arrow(Q4X + BW/2, 7.2, Q4X + BW/2, 5.8 + BH)

# run_q4 also calls optimize.py (Q2 baseline)
ax.annotate('', xy=(Q2X + BW, 8.7), xytext=(Q4X, 8.7),
            arrowprops=dict(arrowstyle='->', color=C_OPT,
                            lw=1.5, linestyle='dotted',
                            connectionstyle='arc3,rad=-0.08'),
            zorder=1)
ax.text(11.0, 8.35, 'Q2 baseline via optimize()', fontsize=7,
        color=C_OPT, ha='center', style='italic')

# optimize_peak_q4 → scipy
arrow_curved(Q4X + BW/2, 8.6, 3.3, 0.5 + BH, color='#999999', rad=-0.15)

# ── Legend ────────────────────────────────────────────────────
legend_items = [
    (C_RUNNER, 'Runner (entry point)'),
    (C_OPT,    'Optimizer'),
    (C_DATA,   'Data / helpers'),
    (C_REPORT, 'Report / plot'),
    (C_OUTPUT, 'Output file'),
    (C_SHARED, 'External library'),
]
for i, (c, label) in enumerate(legend_items):
    yy = 4.4 - i * 0.45
    rect = FancyBboxPatch((0.3, yy), 0.4, 0.3,
                          boxstyle="round,pad=0.05",
                          facecolor=c, edgecolor='#222222',
                          linewidth=0.8, alpha=0.9, zorder=2)
    ax.add_patch(rect)
    ax.text(0.9, yy + 0.15, label, fontsize=8, va='center', color='#333333')

fig.tight_layout(pad=1.0)
fig.savefig('code_flowchart.png', dpi=200, bbox_inches='tight',
            facecolor='#FAFAFA')
plt.close(fig)
print("✅ Saved: code_flowchart.png")
