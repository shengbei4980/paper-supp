"""Theme-level structural differences: compact full-phrase clouds with linked selection highlights.
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
from matplotlib.patches import Circle
from figure5c import DATA, OUT, QA, AGENCIES
from figure5c_continuous_color_scale_version import CMAP

STEM = 'Figure5c_规整紧凑词云_参考式灰圈版'
NORM = TwoSlopeNorm(vmin=-8, vcenter=0, vmax=8)
GROUPS = [(-1, 'Observed > benchmark'), (1, 'Observed < benchmark')]


def place_theme_cloud(ax, selected, global_max, agency):
    """Align full phrases to two left-aligned columns and four compact ranked rows."""
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bounds = ax.get_window_extent(renderer)
    row_heights = np.zeros(4)
    placed = []
    for row in selected.itertuples():
        sign = -1 if row.delta_pp < 0 else 1
        text = ax.text(.01 if sign < 0 else .515, .5, '',
            fontsize=6.3 + 4.2 * (abs(row.delta_pp) / global_max) ** 2,
            ha='left', va='top', multialignment='left', linespacing=1.03,
            fontweight='bold' if row.rank_in_direction == 1 else 'normal',
            color=CMAP(NORM(row.delta_pp)))
        options = []
        for wrap in range(14, 43):
            label = textwrap.fill(row.full_theme_name, width=wrap,
                                  break_long_words=False, break_on_hyphens=False)
            text.set_text(label)
            box = text.get_window_extent(renderer)
            if box.width <= .475 * bounds.width:
                options.append((label.count('\n'), -box.width, label))
        assert options, f'Cannot fit complete phrase: {agency} {row.full_theme_name}'
        text.set_text(min(options)[2])
        text.set_gid(f'theme_label_{agency}_{row.theme}')
        rank = row.rank_in_direction - 1
        row_heights[rank] = max(row_heights[rank], text.get_window_extent(renderer).height * 1.08)
        placed.append((rank, text))
    gap = fig.dpi * .60 / 25.4
    view_height = row_heights.sum() + gap * 3 + 6
    top = view_height - 3
    anchors = []
    for height in row_heights:
        anchors.append((top - height * .04 / 1.08) / view_height)
        top -= height + gap
    for rank, text in placed:
        text.set_position((text.get_position()[0], anchors[rank]))
    for rank in range(4):
        assert len([text for i, text in placed if i == rank]) == 2
        assert len({text.get_position()[1] for i, text in placed if i == rank}) == 1
    return [text for _, text in placed], view_height * 25.4 / fig.dpi


def main():
    paths = [DATA / 'observed_research_theme_estimates_108_items.csv', DATA / 'research_themes_SDG_contributions_1296_items.csv']
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
    width_mm, height_mm = 183, 183
    fig = plt.figure(figsize=(width_mm / 25.4, height_mm / 25.4), dpi=300)
    fig.text(.025, .982, 'c', va='top', fontweight='bold', fontsize=9)
    fig.text(.535, .981, 'Research-theme differences under national SDG challenge weights',
             ha='center', va='top', fontsize=8.8)
    details, labels, mappings, text_axes, full_axes, circle_regions = [], [], [], [], [], []
    cloud_heights_mm, agency_titles = [], []
    for agency, left in zip(AGENCIES, [.105, .565]):
        t = d[d.agency.eq(agency)].copy()
        assert len(t) == 54 and np.isclose(t.observed_pct.sum(), 100)
        assert np.isclose(t.standardized_pct.sum(), 100) and np.isclose(t.delta_pp.sum(), 0)
        agency_titles.append(fig.text(left + .2075, .945, agency, ha='center', fontsize=10, fontweight='bold'))
        groups = []
        for sign, heading in GROUPS:
            rows = t[t.delta_pp * sign > 0].assign(magnitude=lambda x: x.delta_pp.abs())
            rows = rows.sort_values(['magnitude', 'theme'], ascending=[False, True]).head(4)
            assert len(rows) == 4 and (rows.delta_pp * sign > 0).all()
            groups.append(rows.assign(direction=heading, rank_in_direction=range(1, 5)))
        selected = pd.concat(groups, ignore_index=True)
        selected_keys = set(selected.theme)
        cloud = fig.add_axes([left, .598, .415, .310], facecolor='white')
        cloud.patch.set_visible(False)
        cloud.set(xlim=(0, 1), ylim=(0, 1), xticks=[], yticks=[])
        for spine in cloud.spines.values():
            spine.set_visible(False)
        placed, cloud_height_mm = place_theme_cloud(cloud, selected, d.delta_pp.abs().max(), agency)
        cloud_heights_mm.append(cloud_height_mm)
        for (_, row), text in zip(selected.iterrows(), placed):
            fs = 6.3 + 4.2 * (abs(row.delta_pp) / d.delta_pp.abs().max()) ** 2
            labels.append(text)
            z = contribution[contribution.agency.eq(agency) & contribution.theme.eq(row.theme)]
            drivers = z.assign(magnitude=z.contribution_pp.abs()).sort_values('magnitude', ascending=False).head(2)
            record = {key: value for key, value in row.to_dict().items() if key != 'magnitude'}
            record.update(font_size_pt=fs, color=to_hex(CMAP(NORM(row.delta_pp))),
                label_anchor_x=text.get_position()[0], label_anchor_y=text.get_position()[1],
                horizontal_alignment=text.get_ha(), vertical_alignment=text.get_va(),
                main_sdg_drivers=','.join(drivers.sdg))
            details.append(record)
        assert not cloud.patch.get_visible() and not cloud.collections and not cloud.lines and not cloud.patches
        text_axes.append(cloud)
        assert len(selected_keys) == 8
        full = fig.add_axes([left, .110, .415, .415 * width_mm / height_mm])
        full.set_aspect('equal', adjustable='box')
        selected_xy = selected[['observed_pct', 'standardized_pct']].to_numpy()
        circle_center = (selected_xy.min(axis=0) + selected_xy.max(axis=0)) / 2
        circle_radius = np.linalg.norm(selected_xy - circle_center, axis=1).max() + .20
        roi = Circle(circle_center, circle_radius, facecolor='#D6D6D6',
                     edgecolor='none', alpha=.55, zorder=0)
        roi.set_gid(f'enlarged_region_{agency}')
        full.add_patch(roi)
        circle_regions.append(dict(agency=agency, theme_count=8,
            circle_center_x=circle_center[0], circle_center_y=circle_center[1], circle_radius=circle_radius))
        for row in t.itertuples():
            chosen = row.theme in selected_keys
            point = full.scatter(row.observed_pct, row.standardized_pct,
                s=11 if chosen else 7, marker='o', color='#C92D2D' if chosen else '#161616',
                edgecolor='none', linewidth=0,
                zorder=3 if chosen else 2)
            point.set_gid(f'full_point_{agency}_{row.theme}')
        full.plot([0, 16], [0, 16], color='#BBBBBB', lw=.65, ls='--', zorder=1)
        full.set(xlim=(0, 16), ylim=(0, 16), xticks=[0, 4, 8, 12, 16], yticks=[0, 4, 8, 12, 16])
        full.spines[['top', 'right']].set_visible(False)
        full.tick_params(length=2.4, width=.55, pad=3)
        full.set_xlabel('Observed research share (%)', labelpad=4)
        if agency == 'NSF':
            full.set_ylabel('Challenge-standardized share (%)', labelpad=4)
        assert len(full.collections) == 54 and len(full.lines) == 1 and len(full.patches) == 1
        assert np.all(np.linalg.norm(selected_xy - roi.center, axis=1) < roi.radius)
        full_axes.append(full)
        mappings.append(dict(agency=agency, full_theme_count=54, annotated_theme_count=8,
            observed_above=int(t.delta_pp.lt(0).sum()), observed_below=int(t.delta_pp.gt(0).sum()),
            selected_absolute_shift_pct=100 * t[t.theme.isin(selected_keys)].delta_pp.abs().sum() / t.delta_pp.abs().sum()))
    # Fit the page to real phrase heights, keeping the lower quantitative panels at their original size.
    panel_mm = .415 * width_mm
    lower_bottom_mm = 20.130
    note_y_mm = lower_bottom_mm + panel_mm + 4.700
    cloud_top_mm = note_y_mm + 5 + max(cloud_heights_mm)
    height_mm = round(cloud_top_mm + 15, 2)
    assert height_mm < 183, 'Compact layout must reduce the previous page height'
    fig.set_size_inches(width_mm / 25.4, height_mm / 25.4)
    for header in fig.texts[:2]:
        header.set_y(1 - 2.5 / height_mm)
    for header in agency_titles:
        header.set_y(1 - 10 / height_mm)
    for left, cloud, full, cloud_height in zip([.105, .565], text_axes, full_axes, cloud_heights_mm):
        cloud.set_position([left, (cloud_top_mm - cloud_height) / height_mm, .415, cloud_height / height_mm])
        full.set_position([left, lower_bottom_mm / height_mm, .415, panel_mm / height_mm])
    fig.text(.535, note_y_mm / height_mm, 'Gray circles highlight selected themes · Red points are named above',
             ha='center', fontsize=7, color='#444444')
    cax = fig.add_axes([.255, 6.954 / height_mm, .535, 1.830 / height_mm])
    bar = fig.colorbar(plt.cm.ScalarMappable(norm=NORM, cmap=CMAP), cax=cax, orientation='horizontal')
    bar.set_ticks([-8, -4, 0, 4, 8])
    bar.set_ticklabels(['−8', '−4', '0', '+4', '+8'])
    bar.outline.set_visible(False)
    bar.ax.tick_params(length=2, width=.5, pad=2, labelsize=6.5)
    bar.set_label('Theme-label color: challenge-standardized − observed share (pp)', fontsize=7, labelpad=3)
    bar_end_labels = [
        fig.text(.24, 7.869 / height_mm, 'Observed >\nbenchmark', ha='right', va='center', fontsize=6.5, color='#A73B3B'),
        fig.text(.805, 7.869 / height_mm, 'Observed <\nbenchmark', ha='left', va='center', fontsize=6.5, color='#285D96')]
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    assert not any(label.get_window_extent(renderer).overlaps(ax.xaxis.label.get_window_extent(renderer))
                   for label in bar_end_labels for ax in full_axes), 'Colorbar endpoint overlaps x-axis label'
    for ax in text_axes:
        bounds = ax.get_window_extent(renderer)
        boxes = [text.get_window_extent(renderer).expanded(1.02, 1.08) for text in ax.texts]
        for text, box in zip(ax.texts, boxes):
            assert bounds.contains(box.x0, box.y0) and bounds.contains(box.x1, box.y1), f'Text outside its group: {text.get_text()}'
        assert not any(box.overlaps(other) for i, box in enumerate(boxes) for other in boxes[i + 1:]), 'Text overlap'
    assert len(text_axes) == 2 and all(len(ax.texts) == 8 for ax in text_axes)
    for cloud, full in zip(text_axes, full_axes):
        assert np.allclose([cloud.get_position().x0, cloud.get_position().x1],
                           [full.get_position().x0, full.get_position().x1])
    for text in fig.findobj(matplotlib.text.Text):
        if text.get_visible() and text.get_text():
            b = text.get_window_extent(renderer)
            assert b.x0 >= -1 and b.y0 >= -1 and b.x1 <= fig.bbox.width + 1 and b.y1 <= fig.bbox.height + 1, text.get_text()
    pd.DataFrame(details).to_csv(DATA / 'aligned_word_cloud_16_full_theme_annotations.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(mappings).to_csv(DATA / 'aligned_word_cloud_full_and_annotated_extent.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(circle_regions).to_csv(DATA / 'aligned_word_cloud_gray_circle_extent_mapping.csv', index=False, encoding='utf-8-sig')
    fig.savefig(OUT / f'{STEM}.pdf')
    fig.savefig(OUT / f'{STEM}.svg')
    fig.savefig(OUT / f'{STEM}.png', dpi=600)
    fig.savefig(OUT / f'{STEM}.tiff', dpi=600, pil_kwargs={'compression': 'tiff_lzw'})
    fig.savefig(OUT / f'{STEM}_preview.png', dpi=300)
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
    report = dict(size_mm=[width_mm, height_mm], archetype='quantitative grid with compact phrase clouds',
        source_sha256=hashes, unchanged_estimates=True, unchanged_point_coordinates=True,
        all_scatter_points=108, complete_theme_labels=16, red_selected_points=16, black_context_points=92,
        selection='four largest absolute point-estimate shifts per direction per agency; no significance filtering',
        sdg_contributions_sum_to_theme_shifts=True, shared_theme_label_color_and_font_mapping=True,
        font_size_min_pt=min(r['font_size_pt'] for r in details), font_size_max_pt=max(r['font_size_pt'] for r in details),
        no_upper_scatter=True, no_leaders=True,
        word_positions_are_editorial=True, background_free_phrase_clouds=True,
        editorial_layout='two left-aligned columns and four top-aligned ranked rows per agency',
        inter_row_gap_mm=.60, minimum_column_gutter_mm=.03 * .415 * width_mm,
        cloud_content_height_mm=dict(zip(AGENCIES, cloud_heights_mm)),
        font_sizes_unchanged_from_previous_version=True,
        upper_cloud_count=2, names_per_agency_cloud=8,
        lower_circle_count=2, lower_circles_contain_all_named_points=True,
        circles_are_selection_highlights_not_semantic_neighborhoods=True,
        circle_regions=circle_regions,
        no_numeric_word_labels=True, no_task_codes=True, no_overlap=True, no_clipping=True)
    (QA / 'aligned_word_cloud_visual_and_data_assertions.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('PASS: 108 unchanged points; 16 complete phrases in background-free clouds; matching red points and gray circles; no overlap or clipping.')


if __name__ == '__main__':
    main()
