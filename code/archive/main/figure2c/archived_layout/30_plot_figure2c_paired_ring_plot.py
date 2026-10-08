"""Figure 2c, adapted from 20260516-环形热图.py (archived in 参考模板).

Retains the source template's polar axes, north origin, counterclockwise
270-degree sweep, meshgrid/pcolormesh rings, radial labels and cell markers.
Changes only data/semantic mapping, grouping geometry, legend and export.
Run this file from any working directory; all inputs are local to the package.
"""
from pathlib import Path
import argparse
import json
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BLUE, RED, INK = '#003366', '#8B0000', '#282D34'
# Figure1a Target ring anchors (figure1a_sdg_target_ring.py).
NSF_RING = ['#E4EDF5', '#7F99B2', BLUE]
NSFC_RING = ['#F6E4E4', '#C57F7F', RED]
ZERO_COLOR = '#ECEFF1'
DOMAINS = ['D01', 'D02', 'D03', 'D04', 'D05', 'D06']
FEATURED = {'N13|P02|O06', 'N13|P03|O06', 'N01|P01|O08', 'N17|P08|O12'}


def load_data(data_dir):
    cells = pd.read_csv(data_dir / 'Figure2c_全量热图单元.csv')
    assert len(cells) == 324 and not cells.duplicated(['path', 'knowledge']).any()
    assert cells.path.nunique() == 54
    assert cells.groupby('path').knowledge.nunique().eq(6).all()
    for col in ['nsf_probability', 'nsfc_probability']:
        assert cells[col].between(0, 1).all()
        assert np.allclose(cells.groupby('path')[col].sum(), 1, atol=1e-12)
    assert np.allclose(cells.delta_pp,
                       100 * (cells.nsf_probability - cells.nsfc_probability), atol=1e-12)
    cells = cells.sort_values(['domain_order', 'path_order_domain', 'knowledge_order'])
    paths = cells.drop_duplicates('path').copy()
    paths['path_display'] = paths.path.str.replace('|', '→', regex=False)
    columns = ['domain', 'path', 'path_display', 'need_label', 'pressure_label',
               'system_label', 'nsf_raw_path_n', 'nsfc_raw_path_n']
    paths[columns].to_csv(data_dir / 'Figure2c_路径编码与支持量索引.csv', index=False,
                         encoding='utf-8-sig')
    return cells, paths


def geometry(paths):
    # Template theta_edges spans 0 .. 1.5*pi. Insert explicit domain gaps.
    gap = np.deg2rad(2.0)
    width = (1.5 * np.pi - 5 * gap) / len(paths)
    angle = 0.0
    sectors, groups = {}, {}
    for domain in DOMAINS:
        subset = paths[paths.domain.eq(domain)]
        edges = angle + np.arange(len(subset) + 1) * width
        groups[domain] = edges
        for j, path in enumerate(subset.path):
            sectors[path] = (float(edges[j]), float(edges[j+1]))
        angle = edges[-1] + gap
    return sectors, groups


def plot_advanced_forest_chart(cells, paths, output_dir, qa_dir, dpi=600):
    # Original function name retained for comparison against archived template.
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 6,
                         'pdf.fonttype': 42, 'ps.fonttype': 42,
                         'svg.fonttype': 'none', 'text.color': INK,
                         'axes.labelcolor': INK, 'savefig.facecolor': 'white'})
    fig = plt.figure(figsize=(183/25.4, 193/25.4), facecolor='white')
    ax_rect = [.02, .07, .96, .96 * 183/193]
    ax = fig.add_axes(ax_rect, projection='polar')
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(1)
    rmax, outer_radius = 86.0, 64.0
    ax.set_ylim(0, rmax)
    ax.set_axis_off()

    cmaps = {
        'NSF': mcolors.LinearSegmentedColormap.from_list('NSF_share', NSF_RING, N=1024),
        'NSFC': mcolors.LinearSegmentedColormap.from_list('NSFC_share', NSFC_RING, N=1024),
        'difference': mcolors.LinearSegmentedColormap.from_list(
            'NSF_minus_NSFC',
            [NSFC_RING[-1], NSFC_RING[1], ZERO_COLOR, NSF_RING[1], NSF_RING[-1]],
            N=1025)
    }
    norms = {'NSF': mcolors.Normalize(0, 100), 'NSFC': mcolors.Normalize(0, 100),
             'difference': mcolors.TwoSlopeNorm(vmin=-60, vcenter=0, vmax=60)}
    sectors, groups = geometry(paths)
    indexed = cells.set_index(['path', 'knowledge'])
    # Use the exact source labels instead of manually shortened task names.
    task_names = cells[['knowledge', 'knowledge_label']].drop_duplicates()
    assert not task_names.knowledge.duplicated().any()
    task_names = task_names.set_index('knowledge').knowledge_label.to_dict()
    rendered, labels, key_text = [], [], []

    # Figure opening labels use the same axes in axes-fraction coordinates.
    def gaptext(x, y, label, **kwargs):
        t = ax.text(.5 + x/(2*rmax), .5 + y/(2*rmax), label,
                    transform=ax.transAxes, va='center', **kwargs)
        key_text.append(t)
        return t

    for k in range(6):
        knowledge = f'K{k+1:02d}'
        top = outer_radius - 6.5*k
        bands = [('NSF', top-2.2, top, 'nsf_probability', 100),
                 ('NSFC', top-4.4, top-2.2, 'nsfc_probability', 100),
                 ('difference', top-5.65, top-4.4, 'delta_pp', 1)]
        for kind, bottom, upper, column, factor in bands:
            # Same meshgrid and pcolormesh ring construction as the source.
            for domain, theta_edges in groups.items():
                group_paths = paths.loc[paths.domain.eq(domain), 'path'].tolist()
                data = np.array([indexed.loc[(p, knowledge), column]*factor for p in group_paths])
                R_ring, Theta_ring = np.meshgrid([bottom, upper], theta_edges)
                mesh = ax.pcolormesh(Theta_ring, R_ring, data.reshape(-1, 1),
                                    cmap=cmaps[kind], norm=norms[kind],
                                    edgecolor='#F3F1EF', linewidth=.16,
                                    shading='flat', antialiased=True)
                mesh.set_gid(f'ring_{knowledge}_{kind}_{domain}')
                for p, value in zip(group_paths, data):
                    lo, hi = sectors[p]
                    row = indexed.loc[(p, knowledge)]
                    marked = bool(row.quality_gate_recomputed) and kind == 'difference'
                    gid = f'gate_{p.replace("|", "_")}_{knowledge}'
                    if marked:
                        marker, = ax.plot([(lo+hi)/2], [(bottom+upper)/2], marker='o',
                                          markersize=1.65, linestyle='none', color=INK,
                                          markeredgecolor='white', markeredgewidth=.3, zorder=5)
                        marker.set_gid(gid)
                    rendered.append({'path':p, 'knowledge':knowledge, 'ring':kind,
                                     'value':float(value), 'theta_start':lo, 'theta_end':hi,
                                     'r_bottom':bottom, 'r_top':upper, 'marked':marked,
                                     'color_hex':mcolors.to_hex(cmaps[kind](norms[kind](value)))})
            # Short opening leaders aligned to the exact band centers.
            center = (bottom+upper)/2
            ax.plot([.5, .5+2/(2*rmax)], [.5+center/(2*rmax)]*2,
                    transform=ax.transAxes, color='#9A9EA3', lw=.4)
            gaptext(3, center, 'Δ' if kind == 'difference' else kind,
                    fontsize=5.1, color=BLUE if kind == 'NSF' else RED if kind == 'NSFC' else INK)
        gaptext(16, top-2.75, f'{knowledge}  {task_names[knowledge]}', fontsize=6.0, fontweight='medium')
        # Fine black frames around each task triplet within each domain.
        # Individual heatmap cells retain thin, off-white separators.
        for domain, edges in groups.items():
            arc = np.linspace(edges[0], edges[-1], 160)
            theta_frame = np.concatenate([arc, [edges[-1]], arc[::-1], [edges[0]]])
            radius_frame = np.concatenate([np.full(len(arc),top), [top-5.65],
                                            np.full(len(arc),top-5.65), [top]])
            frame, = ax.plot(theta_frame, radius_frame, color='#000000',
                             linewidth=.35, zorder=6, solid_joinstyle='miter')
            frame.set_gid(f'frame_{knowledge}_{domain}')

    # Template category strip, now six data-defined domains; neutral shades
    # keep red and blue reserved for funder/comparison meaning.
    for di, (domain, edges) in enumerate(groups.items()):
        theta_centers = (edges[:-1]+edges[1:])/2
        ax.bar(theta_centers, height=.8, width=np.diff(edges), bottom=24.1,
               color=['#E4E7EA', '#F0F1F2'][di % 2], edgecolor='white', linewidth=.2)
        mid = (edges[0]+edges[-1])/2
        text = ax.text(mid, 22.2, domain, ha='center', va='center', fontsize=5.8,
                       fontweight='bold', color='#555B63')
        key_text.append(text)

    # Source radial labels, with upright alignment on the left hemisphere.
    for row in paths.itertuples(index=False):
        theta = sum(sectors[row.path])/2
        display_angle = (np.degrees(theta)+90) % 360
        if 90 < display_angle <= 270:
            rotation, alignment = display_angle-180, 'right'
        else:
            rotation, alignment = display_angle, 'left'
        t = ax.text(theta, outer_radius+.8, row.path_display, rotation=rotation,
                    ha=alignment, va='center', fontsize=5.2,
                    fontweight='bold' if row.path in FEATURED else 'normal',
                    rotation_mode='anchor')
        t.set_gid('pathlabel_'+row.path.replace('|', '_'))
        labels.append(t)

    # Three common scales in the opening, drawn on this same axes, not panels.
    def legend_bar(y, kind, title, ticklabels):
        x0, width, height = 5, 57, 1.9
        gaptext(x0, y+3.3, title, fontsize=5.8)
        for j in range(100):
            xx = .5+(x0+width*j/100)/(2*rmax)
            patch = mpatches.Rectangle((xx, .5+y/(2*rmax)), width/100/(2*rmax),
                                        height/(2*rmax), transform=ax.transAxes,
                                        facecolor=cmaps[kind](j/99), edgecolor=cmaps[kind](j/99),
                                        linewidth=.08, clip_on=False)
            ax.add_patch(patch)
        for fraction, label in zip([0, .5, 1], ticklabels):
            gaptext(x0+width*fraction, y-1.5, label, fontsize=5.2, ha='center')
    legend_bar(20.5, 'NSF', 'NSF conditional task share (%)', ['0', '50', '100'])
    legend_bar(12.3, 'NSFC', 'NSFC conditional task share (%)', ['0', '50', '100'])
    legend_bar(4.1, 'difference', 'Δ share: NSF − NSFC (percentage points)', ['−60', '0', '+60'])
    gaptext(-10, 7, '54 paths', ha='center', fontsize=8, fontweight='bold')
    gaptext(-10, 2.5, '6 tasks per path', ha='center', fontsize=6.6, color='#656C75')
    gaptext(-10, -3, 'Target–year balanced', ha='center', fontsize=5.5, color='#656C75')

    fig.text(.02, .985, 'c', fontsize=11, fontweight='bold', va='top')
    fig.text(.065, .984, 'Task selection within shared problem paths',
             fontsize=10, fontweight='bold', va='top')
    fig.text(.065, .966, 'Dots on Δ rings: bootstrap 95% CI excludes zero and BH q < 0.05.',
             fontsize=6.1, color='#5B626C', va='top')
    fig.text(.03, .062, 'D01 Safety / resilience     D02 Environment / resources     D03 Services / inclusion',
             fontsize=5.9)
    fig.text(.03, .047, 'D04 Low-carbon transition     D05 Health     D06 Governance', fontsize=5.9)
    fig.text(.03, .030, 'Path labels: need → pressure → system. Bold labels identify the four manuscript examples.',
             fontsize=5.6, color='#5B626C')
    fig.text(.03, .015, 'All six tasks retained per path; full intervals and fractional support are supplied in the source tables.',
             fontsize=5.6, color='#5B626C')
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bounds = fig.bbox
    clipped = []
    for t in [*labels, *key_text, *fig.texts]:
        b = t.get_window_extent(renderer)
        if b.x0 < bounds.x0 or b.y0 < bounds.y0 or b.x1 > bounds.x1 or b.y1 > bounds.y1:
            clipped.append(t.get_text())
    overlapping_keys = []
    for i, a in enumerate(key_text):
        for b in key_text[i+1:]:
            if a.get_window_extent(renderer).overlaps(b.get_window_extent(renderer)):
                overlapping_keys.append([a.get_text(), b.get_text()])
    qa = {'size_mm':[183,193], 'axes_count':len(fig.axes), 'paths':len(paths),
          'source_cells':len(cells), 'rendered_cells':len(rendered),
          'markers':sum(r['marked'] for r in rendered), 'group_frames':36,
          'frame_linewidth_pt':.35, 'clipped_text':clipped,
          'overlapping_key_text':overlapping_keys,
          'python':sys.version, 'matplotlib':matplotlib.__version__,
          'share_scale':[0,100], 'difference_scale':[-60,60]}
    pd.DataFrame(rendered).to_csv(qa_dir/'Figure2c_渲染单元核对表.csv', index=False, encoding='utf-8-sig')
    (qa_dir/'Figure2c_绘图检查.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
    stem = output_dir / 'Figure2c_全量路径任务配对圆环图'
    for suffix in ['.pdf', '.svg', '.png', '.tiff']:
        kwargs = {'dpi':dpi} if suffix in ['.png','.tiff'] else {}
        if suffix == '.tiff': kwargs['pil_kwargs']={'compression':'tiff_lzw'}
        fig.savefig(stem.with_suffix(suffix), **kwargs)
    plt.close(fig)
    with Image.open(stem.with_suffix('.png')) as im:
        im.thumbnail((1500,1600))
        im.save(output_dir/'Figure2c_预览.png')
    print(json.dumps(qa,ensure_ascii=False,indent=2))
    return stem


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,default=ROOT/'数据')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'图')
    parser.add_argument('--dpi',type=int,default=600)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (ROOT/'复核').mkdir(exist_ok=True)
    cells, paths = load_data(args.data_dir)
    plot_advanced_forest_chart(cells, paths, args.output_dir, ROOT/'复核',args.dpi)
