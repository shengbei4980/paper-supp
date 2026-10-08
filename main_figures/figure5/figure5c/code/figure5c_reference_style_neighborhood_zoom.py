"""Full theme scatter with a reference-style, label-only neighbourhood enlargement.
Reuse verified estimates; the upper label layout is not a quantitative coordinate plot.
"""
import json
import textwrap
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm, to_hex
from matplotlib.patches import Circle
from figure5c import DATA, OUT, QA, AGENCIES
from figure5c_continuous_color_scale_version import CMAP

STEM = 'Figure5c_参考式邻域放大_简洁版'
N = 9  # one focal theme and its eight nearest themes; annotation only
NORM = TwoSlopeNorm(vmin=-8, vcenter=0, vmax=8)


def main():
    d = pd.read_csv(DATA / 'observed_research_theme_estimates_108_items.csv')
    assert len(d) == 108 and not d.duplicated(['agency', 'theme']).any()
    assert np.isfinite(d[['observed_pct', 'standardized_pct', 'delta_pp']]).all().all()
    assert np.allclose(d.standardized_pct - d.observed_pct, d.delta_pp)
    plt.rcParams.update({'font.family': 'Arial', 'font.size': 7,
        'axes.labelsize': 7, 'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5,
        'svg.fonttype': 'none', 'pdf.fonttype': 42, 'axes.linewidth': .6})
    width_mm, height_mm = 183, 180
    fig = plt.figure(figsize=(width_mm / 25.4, height_mm / 25.4), dpi=300)
    fig.text(.025, .982, 'c', va='top', fontweight='bold', fontsize=9)
    fig.text(.535, .981, 'Research themes around the largest share shifts',
             ha='center', va='top', fontsize=9)
    details, regions, labels = [], [], []
    for agency, left in zip(AGENCIES, [.105, .565]):
        t = d[d.agency.eq(agency)].copy()
        assert len(t) == 54 and np.isclose(t.observed_pct.sum(), 100)
        assert np.isclose(t.standardized_pct.sum(), 100)
        focus = t.assign(magnitude=t.delta_pp.abs()).sort_values(
            ['magnitude', 'theme'], ascending=[False, True]).iloc[0]
        t['distance'] = np.hypot(t.observed_pct - focus.observed_pct,
                                t.standardized_pct - focus.standardized_pct)
        selected = t.sort_values(['distance', 'theme']).head(N)
        radius = selected.distance.max() * (1 + 1e-7)
        inside = t[t.distance.le(radius)]
        assert set(inside.theme) == set(selected.theme) and len(inside) == N
        fig.text(left + .2075, .934, agency, ha='center', fontsize=10, fontweight='bold')
        cloud = fig.add_axes([left, .595, .415, .315], facecolor='#F3F3F3')
        cloud.set(xlim=(0, 1), ylim=(0, 1), xticks=[], yticks=[])
        for spine in cloud.spines.values():
            spine.set_visible(False)
        full = fig.add_axes([left, .12, .415, .4219166667])
        full.set_aspect('equal', adjustable='box')
        full.add_patch(Circle((focus.observed_pct, focus.standardized_pct), radius,
            facecolor='#DDDDDD', edgecolor='none', zorder=0))
        selected_keys = set(selected.theme)
        for row in t.itertuples():
            chosen = row.theme in selected_keys
            focal = row.theme == focus.theme
            point = full.scatter(row.observed_pct, row.standardized_pct,
                s=22 if focal else 11 if chosen else 8, marker='o',
                color=CMAP(NORM(row.delta_pp)) if chosen else '#777777',
                alpha=1 if chosen else .72,
                edgecolor='#222222' if focal else 'none', linewidth=.55,
                zorder=4 if focal else 3 if chosen else 2)
            point.set_gid(f'full_point_{agency}_{row.theme}')
        full.plot([0, 16], [0, 16], color='#BBBBBB', lw=.65, ls='--', zorder=1)
        full.set(xlim=(0, 16), ylim=(0, 16), xticks=[0, 4, 8, 12, 16], yticks=[0, 4, 8, 12, 16])
        full.spines[['top', 'right']].set_visible(False)
        full.tick_params(length=2.4, width=.55, pad=3)
        full.set_xlabel('Observed research share (%)', labelpad=4)
        if agency == 'NSF':
            full.set_ylabel('Challenge-standardized share (%)', labelpad=4)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        bounds = cloud.get_window_extent(renderer)
        occupied = []
        slots = [(x, y) for y in [.88, .69, .31, .12] for x in [.235, .765]]
        order = selected.assign(focal=selected.theme.eq(focus.theme)).sort_values(
            ['focal', 'distance'], ascending=[False, True])
        for row in order.itertuples():
            focal = row.theme == focus.theme
            fs = 6.8 + 2.7 * abs(row.delta_pp) / d.delta_pp.abs().max()
            label = textwrap.fill(row.full_theme_name, width=34 if focal else 24,
                                  break_long_words=False, break_on_hyphens=False)
            probe = cloud.text(.5, .5, label, ha='center', va='center', fontsize=fs,
                fontweight='bold' if focal else 'normal', linespacing=1.05,
                color=CMAP(NORM(row.delta_pp)))
            preferred = np.array([.5, .5]) if focal else np.array([
                .5 + .40 * (row.observed_pct - focus.observed_pct) / radius,
                .5 + .40 * (row.standardized_pct - focus.standardized_pct) / radius])
            choices = []
            candidates = [(.5, .5)] if focal else slots
            for x, y in candidates:
                probe.set_position((x, y))
                box = probe.get_window_extent(renderer).expanded(1.04, 1.14)
                if box.x0 < bounds.x0 + 4 or box.x1 > bounds.x1 - 4:
                    continue
                if box.y0 < bounds.y0 + 4 or box.y1 > bounds.y1 - 4:
                    continue
                if any(box.overlaps(other) for other in occupied):
                    continue
                cost = float(np.sum((np.array([x, y]) - preferred) ** 2))
                choices.append((cost, x, y, box))
            assert choices, f'Cannot place full name: {agency}: {row.full_theme_name}'
            _, x, y, box = min(choices, key=lambda c: c[0])
            if not focal:
                slots.remove((x, y))
            probe.set_position((x, y))
            probe.set_gid(f'cloud_label_{agency}_{row.theme}')
            occupied.append(box)
            labels.append(probe)
            details.append(dict(agency=agency, theme=row.theme, full_theme_name=row.full_theme_name,
                focal=focal, observed_pct=row.observed_pct, standardized_pct=row.standardized_pct,
                delta_pp=row.delta_pp, distance_from_focus=row.distance, radius=radius,
                font_size_pt=fs, color=to_hex(CMAP(NORM(row.delta_pp))), label_x=x, label_y=y))
        regions.append(dict(agency=agency, focal_theme=focus.theme,
            center_x=focus.observed_pct, center_y=focus.standardized_pct,
            radius=radius, selected_themes=N, all_themes=54))
        assert np.allclose([cloud.get_position().x0, cloud.get_position().x1],
                           [full.get_position().x0, full.get_position().x1], atol=1e-7)
    fig.text(.535, .564, 'Circled themes enlarged above · All 54 themes below',
             ha='center', fontsize=7, color='#444444')
    cax = fig.add_axes([.255, .046, .535, .010])
    bar = fig.colorbar(plt.cm.ScalarMappable(norm=NORM, cmap=CMAP), cax=cax, orientation='horizontal')
    bar.set_ticks([-8, -4, 0, 4, 8])
    bar.set_ticklabels(['−8', '−4', '0', '+4', '+8'])
    bar.outline.set_visible(False)
    bar.ax.tick_params(length=2, width=.5, pad=2, labelsize=6.5)
    bar.set_label('Standardized − observed research share (percentage points)', fontsize=7, labelpad=3)
    fig.text(.235, .051, 'Decrease', ha='right', va='center', fontsize=7, color='#A73B3B')
    fig.text(.810, .051, 'Increase', ha='left', va='center', fontsize=7, color='#285D96')
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [label.get_window_extent(renderer) for label in labels]
    assert not any(box.overlaps(other) for i, box in enumerate(boxes) for other in boxes[i + 1:])
    for text in fig.findobj(matplotlib.text.Text):
        if text.get_visible() and text.get_text():
            b = text.get_window_extent(renderer)
            assert b.x0 >= -1 and b.y0 >= -1 and b.x1 <= fig.bbox.width + 1 and b.y1 <= fig.bbox.height + 1
    pd.DataFrame(details).to_csv(DATA / 'reference_style_zoom_18_full_theme_labels.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(regions).to_csv(DATA / 'reference_style_zoom_circular_region_mapping.csv', index=False, encoding='utf-8-sig')
    fig.savefig(OUT / f'{STEM}.pdf')
    fig.savefig(OUT / f'{STEM}.svg')
    fig.savefig(OUT / f'{STEM}.png', dpi=600)
    fig.savefig(OUT / f'{STEM}.tiff', dpi=600, pil_kwargs={'compression': 'tiff_lzw'})
    fig.savefig(OUT / f'{STEM}_preview.png', dpi=300)
    plt.close(fig)
    svg = ET.parse(OUT / f'{STEM}.svg')
    ns = '{http://www.w3.org/2000/svg}'
    ids = [element.get('id', '') for element in svg.getroot().iter()]
    assert sum(i.startswith('full_point_') for i in ids) == 108
    assert sum(i.startswith('cloud_label_') for i in ids) == 2 * N
    lookup = {(r.agency, r.theme): r for r in d.itertuples()}
    for element in svg.getroot().iter():
        if element.get('id', '').startswith(('full_point_', 'cloud_label_')):
            _, agency, theme = element.get('id').rsplit('_', 2)
            row = lookup[agency, theme]
            title = ET.Element(ns + 'title')
            title.text = (f'{agency}: {row.full_theme_name}; observed {row.observed_pct:.3f}%; '
                          f'standardized {row.standardized_pct:.3f}%; shift {row.delta_pp:+.3f} pp')
            element.insert(0, title)
    ET.register_namespace('', ns[1:-1])
    svg.write(OUT / f'{STEM}.svg', encoding='utf-8', xml_declaration=True)
    report = dict(size_mm=[width_mm, height_mm], all_scatter_points=108,
        enlarged_names=18, selection='largest absolute shift plus eight nearest themes in the observed/standardized share plane',
        exact_circle_membership=True, estimates_unchanged=True,
        lower_coordinates_unchanged=True, upper_layout='labels rearranged for readability; not a quantitative coordinate plot',
        no_leaders=True, no_upper_axes=True, no_task_codes=True,
        label_overlap=False, canvas_clipping=False,
        label_font_min_pt=min(r['font_size_pt'] for r in details),
        label_font_max_pt=max(r['font_size_pt'] for r in details))
    (QA / 'reference_style_zoom_visual_assertions.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('PASS: 108 unchanged points; 18 complete labels; exact circle membership; no leaders, overlap or clipping.')


if __name__ == '__main__':
    main()
