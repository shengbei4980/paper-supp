"""Compact quantitative comparison; every positive-supply location is retained.

Claim: the NSFC sample has greater overall location-level concentration by Gini.
No claim of strict Lorenz dominance, causal effects, or population inference.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
D, O = ROOT/'data', ROOT/'figures'
PREFIX = 'Figure3_location_supply_lorenz_curves'
# Exact NSF/NSFC ramp endpoints from figure1a_sdg_target_ring.py.
BLUE, RED, GRAY = '#003366', '#8B0000', '#959EA5'
BLUE_LIGHT, RED_LIGHT = '#E4EDF5', '#F6E4E4'
plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'DejaVu Sans'], 'font.size': 7, 'axes.labelsize': 7.5, 'axes.linewidth': .65, 'axes.edgecolor': '#75818B', 'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 6.8, 'legend.frameon': False, 'svg.fonttype': 'none', 'pdf.fonttype': 42, 'ps.fonttype': 42, 'savefig.facecolor': 'white', 'path.simplify': False})

def plot():
    O.mkdir(parents=True, exist_ok=True)
    curves = pd.read_csv(D/'lorenz_curves_all_curve_points.csv')
    summary = pd.read_csv(D/'concentration_summary.csv').set_index('agency')
    # Single-column panel, 89 x 88 mm. The panel letter is assigned at assembly.
    fig = plt.figure(figsize=(3.503937007874, 3.464566929134))
    ax = fig.add_axes([.17, .215, .785, .675])
    ax.set_facecolor('#F3F6F9')
    fig.text(.17, .947, 'Overall geographic concentration', fontsize=8, weight='bold', va='center')
    eq, = ax.plot([0, 100], [0, 100], color=GRAY, lw=.8, ls=(0, (3, 3)), zorder=1)
    eq.set_gid('equal_distribution_reference')
    lines = []
    plotted = []
    for agency, color, style in [('NSF', BLUE, '-'), ('NSFC', RED, (0, (5, 2)))]:
        rows = curves.loc[curves.agency.eq(agency)]
        line, = ax.plot(rows.cumulative_location_pct, rows.cumulative_supply_pct, color=color, lw=1.65, ls=style, zorder=3)
        line.set_gid('lorenz_'+agency)
        lines.append(line)
        for r in rows.itertuples():
            plotted.append({'agency': agency, 'vertex': r.vertex, 'x_pct': r.cumulative_location_pct, 'y_pct': r.cumulative_supply_pct, 'svg_curve_id': 'lorenz_'+agency})
    ax.set(xlim=(0, 100), ylim=(0, 100), xticks=np.arange(0,101,20), yticks=np.arange(0,101,20), xlabel='Cumulative share of locations (%)', ylabel='Cumulative share of research supply (%)')
    ax.tick_params(length=2.5, width=.65, color='#75818B')
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(color='white', linewidth=.85, zorder=0)
    ax.set_axisbelow(True)
    labels = [f'{a} · n = {int(summary.loc[a,"positive_location_n"])} · Gini {summary.loc[a,"gini"]:.3f}' for a in ['NSF', 'NSFC']]
    legend = ax.legend(lines+[eq], labels+['Equal distribution'], loc='upper left', handlelength=2.2, handletextpad=.6, borderaxespad=.65, labelspacing=.65, frameon=True, facecolor='white', edgecolor='none', framealpha=.92, borderpad=.5)
    legend.get_frame().set_boxstyle('round,pad=0.25,rounding_size=0.35')
    fig.text(.17, .097, 'Overall top 10 share', fontsize=7, color='#4B5963')
    for x, width, color, background, agency in [(.17, .36, BLUE, BLUE_LIGHT, 'NSF'), (.57, .385, RED, RED_LIGHT, 'NSFC')]:
        card = FancyBboxPatch((x, .022), width, .060, boxstyle='round,pad=0.007,rounding_size=0.012', transform=fig.transFigure, linewidth=0, facecolor=background, zorder=0)
        fig.add_artist(card)
        fig.text(x+.018, .051, f'{agency}  {summary.loc[agency,"top10_share_pct"]:.2f}%', color=color, fontsize=7.5, weight='bold', va='center')
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    outside = []
    for t in fig.findobj(matplotlib.text.Text):
        if t.get_visible() and t.get_text():
            box = t.get_window_extent(renderer)
            if box.x0 < -.5 or box.y0 < -.5 or box.x1 > fig.bbox.width+.5 or box.y1 > fig.bbox.height+.5:
                outside.append(t.get_text())
    assert not outside, outside
    fig.savefig(O/'Figure3_location_supply_lorenz_curves.svg')
    fig.savefig(O/'Figure3_location_supply_lorenz_curves.pdf')
    fig.savefig(O/'Figure3_location_supply_lorenz_curves.png', dpi=600)
    fig.savefig(O/'Figure3_location_supply_lorenz_curves.tiff', dpi=600, pil_kwargs={'compression': 'tiff_lzw'})
    fig.savefig(O/f'{PREFIX}_preview.png', dpi=300)
    pd.DataFrame(plotted).to_csv(D/'actual_plotted_curve_points.csv', index=False, encoding='utf-8-sig')
    (D/'figure_boundary_check.json').write_text(json.dumps({'text_outside_canvas': outside, 'plotted_vertices': len(plotted), 'path_simplification': False, 'figure_mm': [89,88], 'raster_dpi': 600}, indent=2), encoding='utf-8')
    plt.close(fig)

if __name__ == '__main__':
    plot()
