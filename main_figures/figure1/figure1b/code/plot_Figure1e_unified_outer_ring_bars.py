"""Redraw Figure 1e from the archived CSVs; no bootstrap recomputation."""
from pathlib import Path
from types import SimpleNamespace
import importlib.util
import json
import hashlib

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA, OUT, QA = ROOT / 'data', ROOT / 'figures', ROOT / 'checks'
# Exact dark endpoints from Figure1a, as confirmed by the user.
NSF, NSFC = '#003366', '#8B0000'
BLUE, RED = NSF, NSFC
BLUE_LIGHT, RED_LIGHT = '#E4EDF5', '#F6E4E4'
TEXT, GRID = '#26313B', '#000000'
LEVELS = ['SDG', 'Target', 'Urban-need domain']
CENTERS = dict(zip(LEVELS, np.deg2rad([150, 90, 30])))
BASE, SPAN, LIMIT = .77, .36, 45.
BAR_WIDTH = np.deg2rad(5.1)


def tangent(theta):
    return (np.degrees(theta) - 90 + 90) % 180 - 90


def read(name):
    return pd.read_csv(DATA / ('figures_1e_central_panel_revision_' + name + '.csv'))


def prepare():
    top = read('Top5_radial_lollipop')
    topics = read('19_specific_needs').sort_values('topic_order')
    records = []
    for level in LEVELS:
        part = top[top.Level.eq(level)].sort_values('Rank')
        for angle, (_, row) in zip(CENTERS[level] + np.deg2rad([24, 12, 0, -12, -24]), part.iterrows()):
            lo, hi = float(row['Signed_CI_2.5%']), float(row['Signed_CI_97.5%'])
            # All selected Top-5 intervals have stable sign; absolute endpoints
            # are therefore the exact corresponding magnitude quantiles.
            assert lo * hi > 0, 'Sign-changing CI needs original unsigned bootstrap quantiles'
            records.append(dict(level=level, code=str(row.Category_code),
                full_name=str(row.Category_label_en), parent_domain='',
                magnitude_pct=float(row.JSD_contribution_share_pct),
                signed_pct=float(row.Signed_JSD_contribution_share_pct),
                ci_low_pct=min(abs(lo), abs(hi)), ci_high_pct=max(abs(lo), abs(hi)),
                higher_share_in=row.Higher_share_in, theta=float(angle)))
    domains = list(topics.parent_domain.unique())
    edge, gap = np.deg2rad(6), np.deg2rad(3)
    step = (np.pi - 2 * edge - gap * (len(domains) - 1)) / len(topics)
    cursor, domain_bounds = np.pi + edge, {}
    for domain in domains:
        start = cursor
        for row in topics[topics.parent_domain.eq(domain)].itertuples():
            sign = 1 if row.higher_share_in == 'NSF' else -1
            records.append(dict(level='Urban-need topic', code=row.topic_code,
                full_name=row.topic_label_en, parent_domain=domain,
                magnitude_pct=row.jsd_contribution_share_pct,
                signed_pct=sign * row.jsd_contribution_share_pct,
                ci_low_pct=row.contribution_share_ci_low_pct,
                ci_high_pct=row.contribution_share_ci_high_pct,
                higher_share_in=row.higher_share_in, theta=cursor + step / 2))
            cursor += step
        domain_bounds[domain] = (start, cursor)
        cursor += gap
    bars = pd.DataFrame(records)
    assert len(bars) == 34 and not bars.duplicated(['level', 'code']).any()
    assert np.isfinite(bars[['magnitude_pct', 'signed_pct', 'ci_low_pct', 'ci_high_pct']]).all().all()
    assert (bars.ci_low_pct >= 0).all() and (bars.ci_high_pct <= LIMIT).all()
    assert (bars.ci_low_pct <= bars.magnitude_pct).all() and (bars.magnitude_pct <= bars.ci_high_pct).all()
    assert np.isclose(topics.jsd_contribution_share_pct.sum(), 100)
    assert np.isclose(bars.loc[bars.code.eq('S13'), 'signed_pct'].iloc[0], 18.233979350068974)
    return bars, top, topics, domain_bounds


def draw_outer(ax, bars, top, domains):
    theta = np.linspace(0, 2 * np.pi, 721)
    for value in [0, 10, 20, 30, 40, 45]:
        radius = BASE + SPAN * value / LIMIT
        ax.plot(theta, np.full_like(theta, radius), color=GRID,
                lw=1.0 if value == 0 else .28, zorder=0)
        ax.text(0, radius, str(value), fontsize=7, color=TEXT,
                ha='center', va='center', bbox=dict(facecolor='white', edgecolor='none', pad=1), zorder=8)
    ax.text(np.deg2rad(-3.5), 1.01, 'JSD share (%)', fontsize=7, ha='center', color=TEXT)
    for row in bars.itertuples():
        color, dark = (NSF, BLUE) if row.higher_share_in == 'NSF' else (NSFC, RED)
        end = BASE + SPAN * row.magnitude_pct / LIMIT
        low, high = BASE + SPAN * np.array([row.ci_low_pct, row.ci_high_pct]) / LIMIT
        ax.bar(row.theta, end - BASE, bottom=BASE, width=BAR_WIDTH,
               facecolor=color, edgecolor=dark, linewidth=.45, zorder=3)
        ax.plot([row.theta, row.theta], [low, high], color=TEXT, lw=.85, zorder=4)
        for r in [low, high]:
            ax.plot([row.theta - BAR_WIDTH * .19, row.theta + BAR_WIDTH * .19],
                    [r, r], color=TEXT, lw=.85, zorder=4)
        value_label = f'{row.signed_pct:+.1f}%' if abs(row.signed_pct) >= .05 else '0.0%'
        ax.text(row.theta, high + .024, value_label, rotation=tangent(row.theta),
                rotation_mode='anchor', ha='center', va='center', fontsize=8.3, color=dark, zorder=6)
        ax.text(row.theta, BASE - .027, row.code, rotation=tangent(row.theta),
                rotation_mode='anchor', ha='center', va='center', fontsize=8.6, color=TEXT, zorder=6)
    titles = {'SDG': 'SDG · Top 5', 'Target': 'Target · Top 5', 'Urban-need domain': 'Need domain · Top 5'}
    for level in LEVELS:
        ax.bar(CENTERS[level], .035, bottom=1.225, width=np.deg2rad(56),
               color='#ECEFF1', edgecolor=GRID, linewidth=.28, zorder=1)
        cumulative = top.loc[top.Level.eq(level), 'Top5_cumulative_JSD_contribution_pct'].iloc[0]
        ax.text(CENTERS[level], 1.2425, titles[level] + f': {cumulative:.1f}%', fontsize=10,
                rotation=tangent(CENTERS[level]), rotation_mode='anchor', ha='center', va='center', color=TEXT)
    for i, (domain, (start, end)) in enumerate(domains.items()):
        mid = (start + end) / 2
        ax.bar(mid, .029, bottom=.681, width=end-start,
               color=['#E9EEF2', '#F3EEE9'][i % 2], edgecolor=GRID, linewidth=.25)
        ax.text(mid, .6955, domain, fontsize=8.2, rotation=tangent(mid),
                rotation_mode='anchor', ha='center', va='center', color=TEXT)
    ax.text(1.5 * np.pi, 1.2425, 'Urban-need topics · All 19', ha='center', va='center', fontsize=10, color=TEXT)
    for angle in np.deg2rad([0, 60, 120, 180]):
        ax.plot([angle, angle], [.72, 1.195], color=GRID, lw=.28)


def draw_metrics(fig, main_ax, summary):
    """Equal-length arc tracks encode observed values; CIs remain in source data."""
    span = np.deg2rad(50)
    drawn = []
    for level in LEVELS:
        center = CENTERS[level]
        start = center + span / 2
        weight = 'bold' if level == 'Target' else 'normal'
        main_ax.text(center, .716, 'Need domain' if level == 'Urban-need domain' else level,
                     ha='center', va='center', fontsize=8.5, fontweight=weight,
                     rotation=tangent(center), rotation_mode='anchor', color='black')
        for metric, short, maximum, radius in [
            ('Overlap coefficient', 'Overlap', 1., .665),
            ('Jensen-Shannon divergence', 'JSD', .16, .585),
        ]:
            row = summary.loc[summary.Level.eq(level) & summary.Metric.eq(metric)].iloc[0]
            lo, hi = float(row['CI_2.5%']), float(row['CI_97.5%'])
            fraction = float(row.Observed) / maximum
            assert 0 <= lo <= row.Observed <= hi <= maximum
            assert 0 <= fraction <= 1
            track = main_ax.bar(center, .040, bottom=radius-.020, width=span,
                               color='#ECEFF1', edgecolor='black', linewidth=.3, zorder=2)[0]
            fill = main_ax.bar(start-span*fraction/2, .040, bottom=radius-.020,
                              width=span*fraction, color='#59636E', edgecolor='none', zorder=3)[0]
            assert np.isclose(fill.get_width()/track.get_width(), fraction)
            label = f'{row.Observed*100:.1f}%' if short == 'Overlap' else f'{row.Observed:.3f}'
            main_ax.text(center, radius, label, ha='center', va='center', fontsize=8.3,
                         fontweight=weight, rotation=tangent(center), rotation_mode='anchor',
                         color='white' if fraction > .60 else 'black', zorder=5)
            drawn.append(dict(level=level, metric=short, observed=float(row.Observed),
                              ci_low=lo, ci_high=hi, scale_min=0., scale_max=maximum,
                              coverage_fraction=fraction, coverage_degrees=50*fraction,
                              ci_displayed=False))
    main_ax.text(np.deg2rad(-19), .595, 'Overlap\n0–100%', fontsize=7.5,
                 ha='center', va='center', color='black')
    main_ax.text(np.deg2rad(-8), .595, 'JSD\n0–0.16', fontsize=7.5,
                 ha='center', va='center', color='black')
    assert len(drawn) == 6
    return pd.DataFrame(drawn)


def draw_radar(fig, main_ax, targets):
    spec = importlib.util.spec_from_file_location('original_radar', Path(__file__).with_name('original_central_radar.py'))
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    original.DIFF_COLOR, original.JSD_COLOR = NSF, NSFC
    original.PARENT_BANDS = ('#F7F8FA', '#EEF1F4')
    fig.canvas.draw()
    box = main_ax.get_position()
    size = box.width * .535 / 1.32
    ax = fig.add_axes([box.x0 + box.width/2 - size/2,
                       box.y0 + box.height/2 - size/2, size, size], polar=True)
    ax.set_ylim(0, .235)
    ax.set_theta_zero_location('E')
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False); ax.spines['polar'].set_visible(False)
    original.draw_center_target_radar(ax, targets, SimpleNamespace(NSF_COLOR=BLUE, NSFC_COLOR=RED))
    for line in ax.lines:
        if line.get_color() == NSFC:
            line.set_linestyle('--')
        if line.get_color() in ('#E0E4E8', '#E4E8EB'):
            line.set_color('black')
            line.set_linewidth(.25)
    for collection in ax.collections:
        if collection.get_alpha() is not None:
            mask = targets.rank_by_jsd_contribution.astype(int).le(5)
            collection.set_facecolor(np.where(targets.loc[mask, 'higher_share_in'].eq('NSF'),
                                               BLUE_LIGHT, RED_LIGHT))
            collection.set_alpha(1)
    for patch in ax.patches:
        if np.isclose(patch.get_height(), .020):
            patch.set_edgecolor('black')
            patch.set_linewidth(.25)
    for text in ax.texts:
        text.set_fontsize(text.get_fontsize() * 1.55)
        if text.get_position() == (0., 0.):
            text.set_text(f"Top 30 Targets\n{targets.top30_cumulative_jsd_share_pct.iloc[0]:.1f}% of Target JSD")
            text.set_fontsize(8)
    circle = np.linspace(0, 2*np.pi, 361)
    ax.plot(circle, np.full_like(circle, .23), color='black', lw=1)
    return ax


def main():
    mpl.rcParams.update({'font.family':'serif', 'font.serif':['Times New Roman'],
        'font.size':9, 'svg.fonttype':'none', 'pdf.fonttype':42, 'ps.fonttype':42,
        'figure.facecolor':'white', 'savefig.facecolor':'white'})
    bars, top, topics, domains = prepare()
    targets = read('Top30Target').sort_values('radar_order').reset_index(drop=True)
    distributions, summary = read('Bootstrap_distributions'), read('cross_level_metrics')
    assert len(targets) == 30 and len(distributions) == 12000
    fig = plt.figure(figsize=(13, 13))
    ax = fig.add_axes([.025, .065, .95, .87], polar=True)
    ax.set_theta_zero_location('E'); ax.set_theta_direction(1); ax.set_ylim(0, 1.32)
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False); ax.spines['polar'].set_visible(False)
    draw_outer(ax, bars, top, domains)
    metric_points = draw_metrics(fig, ax, summary)
    ax.set_xticks([]); ax.set_yticks([])
    draw_radar(fig, ax, targets)
    fig.text(.03, .975, 'e', fontsize=19, fontweight='bold', va='top')
    fig.text(.5, .975, 'Broad agreement masks concentrated category-level divergence',
             fontsize=16, fontweight='bold', ha='center', va='top')
    fig.text(.5, .948, '34 category contributions · shared radial scale · bootstrap 95% intervals',
             fontsize=10, color='#65717C', ha='center')
    handles = [Patch(facecolor=NSF, edgecolor=BLUE, label='NSF higher (+)'),
               Patch(facecolor=NSFC, edgecolor=RED, label='NSFC higher (−)'),
               Line2D([], [], color=TEXT, marker='|', markersize=7, lw=.8, label='Outer bars: 95% CI'),
               Line2D([], [], color=NSF, lw=1.5, label='Radar: relative difference'),
               Line2D([], [], color=NSFC, lw=1.5, ls='--', label='Radar: JSD contribution (sqrt)')]
    fig.legend(handles=handles, loc='center', bbox_to_anchor=(.5, .063), ncol=3,
               frameon=False, fontsize=8.6, labelspacing=.4)
    fig.text(.5, .034, 'Inner arcs: observed values; overlap 0–100%, JSD 0–0.16. Metric 95% CIs are provided in the accompanying data table.',
             ha='center', fontsize=8.7, color='#65717C')
    fig.text(.5, .016, 'Signs indicate the country with higher share; JSD contributions are non-negative. Full category names accompany the figure.',
             ha='center', fontsize=8.6, color='#65717C')
    for directory in (OUT, QA): directory.mkdir(exist_ok=True)
    stem = OUT / 'Figure1e_two_level_arc_coverage_bars_dark_blue_dark_red'
    for ext in ['png','pdf','svg','tiff']:
        opts = {'dpi': 300 if ext == 'png' else 600}
        if ext == 'tiff': opts['pil_kwargs'] = {'compression':'tiff_lzw'}
        fig.savefig(stem.with_suffix('.'+ext), **opts)
    plt.close(fig)
    bars.to_csv(DATA / 'Figure1e_34_bar_plot_data.csv', index=False, encoding='utf-8-sig')
    metric_points.to_csv(DATA / 'Figure1e_arc_coverage_bars_6_metrics.csv', index=False, encoding='utf-8-sig')
    dictionary = bars[['level','code','full_name','parent_domain']]
    dictionary.to_csv(DATA / 'Figure1e_outer_ring_code_full_name_glossary.csv', index=False, encoding='utf-8-sig')
    targets[['category_code','category_label_en','parent_sdg']].to_csv(
        DATA / 'Figure1e_center_30Target_code_glossary.csv', index=False, encoding='utf-8-sig')
    domain_names = topics[['parent_domain','parent_domain_label_en']].drop_duplicates()
    lines = ['# Figure 1e 编号全称释义', '', '## 外环 34 个类别', '',
             '| 层级 | 编号 | 原始数据全称 |', '|---|---|---|']
    lines += [f'| {r.level} | {r.code} | {r.full_name} |' for r in dictionary.itertuples()]
    lines += ['', '## D01–D06 需求分组', '', '| 编号 | 原始数据全称 |', '|---|---|']
    lines += [f'| {r.parent_domain} | {r.parent_domain_label_en} |' for r in domain_names.itertuples()]
    lines += ['', '## 中心 30 个 Target', '', '| 编号 | 原始数据全称 |', '|---|---|']
    lines += [f'| {r.category_code} | {r.category_label_en} |' for r in targets.itertuples()]
    (ROOT / 'code_full_name_glossary.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    report = dict(outer_bars=len(bars), center_targets=len(targets), bootstrap_rows=len(distributions),
        radial_scale=[0,LIMIT], max_ci=float(bars.ci_high_pct.max()),
        s13_signed_pct=float(bars.loc[bars.code.eq('S13'),'signed_pct'].iloc[0]),
        nsf_fill=NSF, nsfc_fill=NSFC, alpha=1, circular_lines='#000000',
        inner_metric_display='three sectors with equal-length clockwise coverage arcs; metric CIs in data table',
        inner_metric_points=len(metric_points),
        radar_relative_difference=NSF, radar_jsd_contribution=NSFC,
        radar_line_styles=['solid', 'dashed'], highlight_fills=[BLUE_LIGHT, RED_LIGHT],
        palette_basis='Exact Figure1a dark endpoints: NSF #003366 and NSFC #8B0000; alpha 1',
        radar_radius=.535, radar_y_shift=0, jsd_scale=[0,.16], overlap_scale=[0,1], arc_span_degrees=50,
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in DATA.glob('figures_1e_central_panel_revision_*.csv')})
    (QA / 'data_and_style_check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
