"""Theme-level structural differences: signed annotations above the complete scatter.
Reuses verified fixed-profile estimates and SDG contributions without rerunning bootstrap.
"""
import hashlib
import json
import textwrap
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm, to_hex
from figure5c import DATA, OUT, QA, AGENCIES
from figure5c_连续色带版 import CMAP

STEM = 'Figure5c_双向结构偏离_主题文字与全量散点'
NORM = TwoSlopeNorm(vmin=-8, vcenter=0, vmax=8)
GROUPS = [(-1, 'Observed > benchmark', .739), (1, 'Observed < benchmark', .551)]


def main():
    paths = [DATA / '实际研究主题估计_108项.csv', DATA / '研究主题_SDG贡献_1296项.csv']
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    d, contribution = [pd.read_csv(p) for p in paths]
    assert len(d) == 108 and not d.duplicated(['agency', 'theme']).any()
    assert len(contribution) == 1296
    assert not contribution.duplicated(['agency', 'theme', 'sdg']).any()
    assert np.isfinite(d[['observed_pct', 'standardized_pct', 'delta_pp']]).all().all()
    assert np.allclose(d.standardized_pct - d.observed_pct, d.delta_pp)
    sums = contribution.groupby(['agency', 'theme']).contribution_pp.sum()
    indexed = d.set_index(['agency', 'theme'])
    assert np.allclose(sums.reindex(indexed.index), indexed.delta_pp)
    assert d.observed_pct.between(0, 16).all() and d.standardized_pct.between(0, 16).all()
    plt.rcParams.update({'font.family': 'Arial', 'font.size': 7,
        'axes.labelsize': 7, 'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5,
        'svg.fonttype': 'none', 'pdf.fonttype': 42, 'axes.linewidth': .6})
    width_mm, height_mm = 183, 193
    fig = plt.figure(figsize=(width_mm / 25.4, height_mm / 25.4), dpi=300)
    fig.text(.025, .982, 'c', va='top', fontweight='bold', fontsize=9)
    fig.text(.535, .981, 'Research-theme differences under national SDG challenge weights',
             ha='center', va='top', fontsize=8.8)
    details, labels, mappings, text_axes, full_axes = [], [], [], [], []
    for agency, left in zip(AGENCIES, [.105, .565]):
        t = d[d.agency.eq(agency)].copy()
        assert len(t) == 54 and np.isclose(t.observed_pct.sum(), 100)
        assert np.isclose(t.standardized_pct.sum(), 100) and np.isclose(t.delta_pp.sum(), 0)
        fig.text(left + .2075, .945, agency, ha='center', fontsize=10, fontweight='bold')
        selected_keys = set()
        for sign, heading, bottom in GROUPS:
            selected = t[t.delta_pp * sign > 0].assign(magnitude=lambda x: x.delta_pp.abs())
            selected = selected.sort_values(['magnitude', 'theme'], ascending=[False, True]).head(4)
            assert len(selected) == 4 and (selected.delta_pp * sign > 0).all()
            selected_keys.update(selected.theme)
            cloud = fig.add_axes([left, bottom, .415, .177], facecolor='#F5F5F4')
            cloud.set(xlim=(0, 1), ylim=(0, 1), xticks=[], yticks=[])
            for spine in cloud.spines.values():
                spine.set_visible(False)
            cloud.text(.5, .929, heading, ha='center', va='center', fontsize=7.1, color='#222222')
            slots = [(.25, .665), (.75, .665), (.25, .235), (.75, .235)]
            for rank, ((_, row), (x, y)) in enumerate(zip(selected.iterrows(), slots), 1):
                fs = 6.8 + 2.7 * abs(row.delta_pp) / d.delta_pp.abs().max()
                label = textwrap.fill(row.full_theme_name, width=22,
                                      break_long_words=False, break_on_hyphens=False)
                text = cloud.text(x, y, label, ha='center', va='center', fontsize=fs,
                    linespacing=1.04, fontweight='bold' if rank == 1 else 'normal',
                    color=CMAP(NORM(row.delta_pp)))
                text.set_gid(f'theme_label_{agency}_{row.theme}')
                labels.append(text)
                z = contribution[contribution.agency.eq(agency) & contribution.theme.eq(row.theme)]
                drivers = z.assign(magnitude=z.contribution_pp.abs()).sort_values('magnitude', ascending=False).head(2)
                record = {key: value for key, value in row.to_dict().items() if key != 'magnitude'}
                record.update(direction=heading, rank_in_direction=rank, font_size_pt=fs,
                    color=to_hex(CMAP(NORM(row.delta_pp))), label_x=x, label_y=y,
                    main_sdg_drivers=','.join(drivers.sdg))
                details.append(record)
            assert not cloud.collections and not cloud.lines and not cloud.patches
            text_axes.append(cloud)
        assert len(selected_keys) == 8
        full = fig.add_axes([left, .105, .415, .415 * width_mm / height_mm])
        full.set_aspect('equal', adjustable='box')
        for row in t.itertuples():
            chosen = row.theme in selected_keys
            point = full.scatter(row.observed_pct, row.standardized_pct,
                s=19 if chosen else 9, marker='o', color=CMAP(NORM(row.delta_pp)),
                edgecolor='#333333' if chosen else 'none', linewidth=.45,
                zorder=3 if chosen else 2)
            point.set_gid(f'full_point_{agency}_{row.theme}')
        full.plot([0, 16], [0, 16], color='#BBBBBB', lw=.65, ls='--', zorder=1)
        full.set(xlim=(0, 16), ylim=(0, 16), xticks=[0, 4, 8, 12, 16], yticks=[0, 4, 8, 12, 16])
        full.spines[['top', 'right']].set_visible(False)
        full.tick_params(length=2.4, width=.55, pad=3)
        full.set_xlabel('Observed research share (%)', labelpad=4)
        if agency == 'NSF':
            full.set_ylabel('Challenge-standardized share (%)', labelpad=4)
        assert len(full.collections) == 54 and len(full.lines) == 1 and not full.patches
        full_axes.append(full)
        mappings.append(dict(agency=agency, full_theme_count=54, annotated_theme_count=8,
            observed_above=int(t.delta_pp.lt(0).sum()), observed_below=int(t.delta_pp.gt(0).sum()),
            selected_absolute_shift_pct=100 * t[t.theme.isin(selected_keys)].delta_pp.abs().sum() / t.delta_pp.abs().sum()))
    fig.text(.535, .521, 'All 54 themes per agency · Outlined points match the names above',
             ha='center', fontsize=7, color='#444444')
    cax = fig.add_axes([.255, .038, .535, .010])
    bar = fig.colorbar(plt.cm.ScalarMappable(norm=NORM, cmap=CMAP), cax=cax, orientation='horizontal')
    bar.set_ticks([-8, -4, 0, 4, 8])
    bar.set_ticklabels(['−8', '−4', '0', '+4', '+8'])
    bar.outline.set_visible(False)
    bar.ax.tick_params(length=2, width=.5, pad=2, labelsize=6.5)
    bar.set_label('Challenge-standardized − observed research share (pp)', fontsize=7, labelpad=3)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for ax in text_axes:
        bounds = ax.get_window_extent(renderer)
        boxes = [text.get_window_extent(renderer).expanded(1.02, 1.08) for text in ax.texts]
        for text, box in zip(ax.texts, boxes):
            assert bounds.contains(box.x0, box.y0) and bounds.contains(box.x1, box.y1), f'Text outside its group: {text.get_text()}'
        assert not any(box.overlaps(other) for i, box in enumerate(boxes) for other in boxes[i + 1:]), 'Text overlap'
    for cloud, full in zip(text_axes[::2], full_axes):
        assert np.allclose([cloud.get_position().x0, cloud.get_position().x1],
                           [full.get_position().x0, full.get_position().x1])
    for text in fig.findobj(matplotlib.text.Text):
        if text.get_visible() and text.get_text():
            b = text.get_window_extent(renderer)
            assert b.x0 >= -1 and b.y0 >= -1 and b.x1 <= fig.bbox.width + 1 and b.y1 <= fig.bbox.height + 1, text.get_text()
    pd.DataFrame(details).to_csv(DATA / '双向偏离_16个完整主题标注.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(mappings).to_csv(DATA / '双向偏离_全量与标注范围.csv', index=False, encoding='utf-8-sig')
    fig.savefig(OUT / f'{STEM}.pdf')
    fig.savefig(OUT / f'{STEM}.svg')
    fig.savefig(OUT / f'{STEM}.png', dpi=600)
    fig.savefig(OUT / f'{STEM}.tiff', dpi=600, pil_kwargs={'compression': 'tiff_lzw'})
    fig.savefig(OUT / f'{STEM}_预览.png', dpi=300)
    plt.close(fig)
    svg = ET.parse(OUT / f'{STEM}.svg')
    ns = '{http://www.w3.org/2000/svg}'
    ids = [element.get('id', '') for element in svg.getroot().iter()]
    point_keys = {i.removeprefix('full_point_') for i in ids if i.startswith('full_point_')}
    label_keys = {i.removeprefix('theme_label_') for i in ids if i.startswith('theme_label_')}
    assert len(point_keys) == 108 and len(label_keys) == 16
    assert label_keys == {f"{r['agency']}_{r['theme']}" for r in details} <= point_keys
    lookup = {(r.agency, r.theme): r for r in d.itertuples()}
    for element in svg.getroot().iter():
        if element.get('id', '').startswith(('full_point_', 'theme_label_')):
            _, agency, theme = element.get('id').rsplit('_', 2)
            row = lookup[agency, theme]
            title = ET.Element(ns + 'title')
            title.text = (f'{agency}: {row.full_theme_name}; observed {row.observed_pct:.3f}%; '
                          f'challenge-standardized {row.standardized_pct:.3f}%; shift {row.delta_pp:+.3f} pp')
            element.insert(0, title)
    ET.register_namespace('', ns[1:-1])
    svg.write(OUT / f'{STEM}.svg', encoding='utf-8', xml_declaration=True)
    assert hashes == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    report = dict(size_mm=[width_mm, height_mm], archetype='quantitative grid with theme annotations',
        source_sha256=hashes, unchanged_estimates=True, unchanged_point_coordinates=True,
        all_scatter_points=108, complete_theme_labels=16, outlined_points=16,
        selection='four largest absolute point-estimate shifts per direction per agency; no significance filtering',
        sdg_contributions_sum_to_theme_shifts=True, shared_color_and_font_mapping=True,
        font_size_min_pt=min(r['font_size_pt'] for r in details), font_size_max_pt=max(r['font_size_pt'] for r in details),
        no_upper_scatter=True, no_leaders=True, no_neighborhood_circles=True,
        no_numeric_word_labels=True, no_task_codes=True, no_overlap=True, no_clipping=True)
    (QA / '双向偏离_画面与数据断言.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('PASS: 108 unchanged points; 16 complete names, four per direction per agency; SDG decomposition and label mapping verified; no overlap or clipping.')


if __name__ == '__main__':
    main()
