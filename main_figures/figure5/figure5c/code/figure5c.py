"""Figure 5c: fixed-profile challenge standardization; empirical project-family bootstrap.

Run normally to rebuild analysis and plots; --reuse redraws verified source tables.
All supplied country / SDG / task units are retained. No dimensionality reduction.
"""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '4'
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import json
import hashlib
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from matplotlib.colors import to_rgb, to_hex

ROOT = Path(__file__).resolve().parents[1]
PROJECT = Path(r'E:\可持续发展目标基金')
FIGURES = PROJECT / '定稿撰写/成图'
DATA, OUT, QA = [ROOT / s for s in ['data', 'outputs', 'review']]
for folder in [DATA, OUT, QA]:
    folder.mkdir(parents=True, exist_ok=True)
GOALS = [2, 3, 6, 7, 9, 10, 11, 12, 13, 15, 16, 17]
SDGS = [f'S{g:02d}' for g in GOALS]
TASKS = [f'K{k:02d}' for k in range(1, 7)]
AGENCIES = ['NSF', 'NSFC']
LABELS = ['Measure & diagnose', 'Explain mechanisms', 'Predict risks',
          'Design & optimize', 'Support decisions', 'Monitor & evaluate']
BASE_COLORS = ['#78A6C3', '#536E89', '#BCC7CE', '#D48B8B', '#986A74', '#D7CEC5']
# Preserve the Figure 5b task hues; darken pale colors for small-text readability.
COLORS = [to_hex(np.array(to_rgb(c)) * f) for c, f in zip(BASE_COLORS, [.70, .85, .57, .76, .85, .52])]
MARKERS = ['o', 's', '^', 'D', 'v', 'P']
STEM = 'Figure5c_挑战标准化任务组合_全量贡献'
B = 2000
SEED = 20261001

def export_csv(rows, name):
    pd.DataFrame(rows).to_csv(DATA / name, index=False, encoding='utf-8-sig')

def estimate(totals, challenge):
    """Last two dimensions are goal and task; accepts bootstrap batches."""
    goal_mass = totals.sum(axis=-1)
    assert np.all(goal_mass > 0), 'Unobserved goal profile; do not impute as zero.'
    supply = goal_mass / goal_mass.sum(axis=-1, keepdims=True)
    profile = totals / goal_mass[..., None]
    observed = (supply[..., None] * profile).sum(axis=-2)
    standardized = (challenge[..., None] * profile).sum(axis=-2)
    contribution = 100 * (challenge - supply)[..., None] * profile
    delta = 100 * (standardized - observed)
    assert np.allclose(contribution.sum(axis=-2), delta, atol=1e-10)
    assert np.allclose(delta.sum(axis=-1), 0, atol=1e-10)
    return supply, profile, observed, standardized, contribution, delta

def analyse():
    canonical_path = FIGURES / 'figure5/重新输出figure/figure5e/data/Figure5e_country_SDG_composite_coordinate_estimates.csv'
    paths_path = FIGURES / 'figure5/补充图_S17_全部SDG内容路径与敏感性/data/FigureS17_全部12SDG路径.csv'
    canonical = pd.read_csv(canonical_path)
    paths = pd.read_csv(paths_path)
    canonical.to_csv(DATA / 'input_country_SDG_benchmark.csv', index=False, encoding='utf-8-sig')
    summary, contributions, supports, profiles, sensitivity = [], [], [], [], []
    provenance = {'bootstrap_draws': B, 'seed': SEED, 'challenge_held_fixed': True,
                  'inputs': {}, 'countries': {}}
    source_paths = [canonical_path, paths_path]
    for ai, agency in enumerate(AGENCIES):
        path = PROJECT / f'框架内容初稿/数据/llm编码完数据/full_v3_5_2_combined_deepseek/{agency}_coding_results.csv'
        cols = ['record_id', 'project_family_id', 'project_family_weight', 'sdg_goal_multi', 'primary_knowledge_task']
        raw = pd.read_csv(path, usecols=cols)
        assert not raw[cols].isna().any().any(), 'Missing required source fields'
        assert raw.record_id.is_unique
        assert raw.primary_knowledge_task.isin(TASKS).all()
        raw.to_csv(DATA / f'input_{agency}_项目族.csv.gz', index=False, compression='gzip', encoding='utf-8-sig')
        source_paths.append(path)
        ids, families = pd.factorize(raw.project_family_id, sort=True)
        matrix = np.zeros((len(families), 12, 6))
        for fi, weight, goals, task in zip(ids, raw.project_family_weight, raw.sdg_goal_multi, raw.primary_knowledge_task):
            codes = goals.split('|')
            assert len(codes) == len(set(codes)) and set(codes).issubset(SDGS)
            assert weight > 0
            for goal in codes:
                matrix[fi, SDGS.index(goal), TASKS.index(task)] += weight / len(codes)
        assert np.allclose(matrix.sum(axis=(1, 2)), 1, atol=1e-10)
        ref = canonical[canonical.agency.eq(agency)].set_index('sdg').loc[SDGS]
        challenge = ref.challenge_share.to_numpy()
        assert np.isclose(challenge.sum(), 1) and np.all(challenge > 0)
        supply, profile, obs, std, contrib, delta = estimate(matrix.sum(axis=0), challenge)
        assert np.allclose(supply, ref.supply_share, atol=1e-10)
        old = paths[paths.agency.eq(agency)].groupby(['sdg', 'knowledge_task']).fractional_project_support.sum()
        old = old.reindex(pd.MultiIndex.from_product([SDGS, TASKS]), fill_value=0).to_numpy().reshape(12, 6)
        assert np.allclose(matrix.sum(axis=0), old, atol=1e-8)
        rng = np.random.default_rng(SEED + ai)
        draws = []
        # Resample whole observed families, preserving their fractional record/goal allocations.
        for start in range(0, B, 100):
            weights = rng.multinomial(len(families), np.full(len(families), 1 / len(families)), size=min(100, B-start))
            totals = (weights @ matrix.reshape(len(families), -1)).reshape(-1, 12, 6)
            valid = (totals.sum(axis=2) > 0).all(axis=1)
            if valid.any():
                draws.append(estimate(totals[valid], challenge)[4])
        boot = np.concatenate(draws)
        assert len(boot) >= .99 * B
        ci = np.quantile(boot, [.025, .975], axis=0)
        dci = np.quantile(boot.sum(axis=1), [.025, .975], axis=0)
        provenance['countries'][agency] = {'records': len(raw), 'families': len(families), 'bootstrap_valid': len(boot),
                                            'source_path_max_abs_error': float(np.max(np.abs(matrix.sum(axis=0)-old)))}
        for k, task in enumerate(TASKS):
            summary.append(dict(agency=agency, task=task, label=LABELS[k], observed_pct=100*obs[k],
                                standardized_pct=100*std[k], delta_pp=delta[k], ci_low=dci[0,k], ci_high=dci[1,k]))
        goal_weights = matrix.sum(axis=2)
        for g, sdg in enumerate(SDGS):
            support = goal_weights[:, g]
            supports.append(dict(agency=agency, sdg=sdg, supply_share=supply[g], challenge_share=challenge[g],
                                 challenge_supply_ratio=challenge[g]/supply[g], family_count=int((support>0).sum()),
                                 fractional_support=support.sum(), effective_family_n=support.sum()**2/(support**2).sum()))
            for k, task in enumerate(TASKS):
                contributions.append(dict(agency=agency, sdg=sdg, task=task, contribution_pp=contrib[g,k],
                                          ci_low=ci[0,g,k], ci_high=ci[1,g,k], bootstrap_valid=len(boot)))
                profiles.append(dict(agency=agency, sdg=sdg, task=task, conditional_task_share=profile[g,k],
                                     fractional_support=matrix[:,g,k].sum()))
            keep = np.arange(12) != g
            # Leave-one-goal-out changes the goal universe; independently reclose both weights.
            without = estimate(matrix.sum(axis=0)[keep], challenge[keep]/challenge[keep].sum())[-1]
            for k, task in enumerate(TASKS):
                sensitivity.append(dict(agency=agency, omitted_sdg=sdg, task=task, full_delta_pp=delta[k],
                                        reclosed_delta_pp=without[k], difference_pp=without[k]-delta[k]))
    for path in source_paths:
        provenance['inputs'][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    export_csv(summary, 'task_shifts_12_items.csv')
    export_csv(contributions, 'SDG_task_contributions_144_items.csv')
    export_csv(supports, 'SDG_support_24_items.csv')
    export_csv(profiles, 'conditional_task_combinations_144_items.csv')
    export_csv(sensitivity, 'per_SDG_leave_out_sensitivity_144_items.csv')
    export_csv([dict(task=t, label=l, source_color=b, display_color=c, marker=m) for t,l,b,c,m in zip(TASKS,LABELS,BASE_COLORS,COLORS,MARKERS)], 'task_codes_and_colors.csv')
    (QA / 'data_verification.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding='utf-8')

def check_tables():
    s = pd.read_csv(DATA / 'task_shifts_12_items.csv')
    c = pd.read_csv(DATA / 'SDG_task_contributions_144_items.csv')
    p = pd.read_csv(DATA / 'conditional_task_combinations_144_items.csv')
    assert len(s) == 12 and len(c) == len(p) == 144
    assert not c.duplicated(['agency','sdg','task']).any()
    assert np.isfinite(c[['contribution_pp','ci_low','ci_high']]).all().all()
    assert (c.ci_high >= c.ci_low).all()
    for a in AGENCIES:
        sub = s[s.agency.eq(a)].set_index('task').loc[TASKS]
        summed = c[c.agency.eq(a)].groupby('task').contribution_pp.sum().loc[TASKS]
        assert np.allclose(summed, sub.delta_pp, atol=1e-10)
        assert np.isclose(sub.delta_pp.sum(), 0, atol=1e-10)
        assert np.isclose(sub.observed_pct.sum(), 100) and np.isclose(sub.standardized_pct.sum(),100)
    assert np.allclose(p.groupby(['agency','sdg']).conditional_task_share.sum(), 1)
    return s, c

def plot():
    s, c = check_tables()
    plt.rcParams.update({'font.family':'Arial', 'font.size':7, 'axes.labelsize':7,
                         'xtick.labelsize':7, 'ytick.labelsize':7, 'svg.fonttype':'none',
                         'pdf.fonttype':42, 'axes.linewidth':.6, 'savefig.facecolor':'white'})
    size_inches = (183/25.4, 164/25.4)
    fig = plt.figure(figsize=size_inches, dpi=300)
    fig.text(.025,.969,'c',fontsize=10,fontweight='bold', va='top')
    fig.text(.52,.966,'Task shifts under challenge-standardized SDG weights',ha='center',va='top',fontsize=9)
    positions = [(.11,.51),(.575,.975)]
    texts = []
    extent = max(abs(c.ci_low.min()), abs(c.ci_high.max()))
    bound = 2 * np.ceil((extent+.4)/2)
    max_delta = s.delta_pp.abs().max()
    for ai, (agency, (left,right)) in enumerate(zip(AGENCIES,positions)):
        center = (left+right)/2
        fig.text(center,.912,agency,ha='center',fontweight='bold',fontsize=10)
        cloud = fig.add_axes([left,.55,right-left,.335])
        cloud.set_axis_off()
        cloud.add_patch(Ellipse((.5,.5),.995,.995,facecolor='#F3F4F5',edgecolor='none',transform=cloud.transAxes))
        rows = s[s.agency.eq(agency)].set_index('task')
        for k, (task, x, y) in enumerate(zip(TASKS,[.45,.52,.44,.51,.48,.54],[.90,.74,.58,.42,.26,.10])):
            delta = rows.loc[task,'delta_pp']
            fs = 8.5 + 4 * abs(delta)/max_delta
            txt = cloud.text(x,y,LABELS[k],ha='center',va='center',color=COLORS[k],fontsize=fs,
                             fontweight='bold' if abs(delta)>=4 else 'normal',transform=cloud.transAxes)
            txt.set_gid(f'term_{agency}_{task}')
            texts.append(txt)
            txt2 = cloud.text(x,y-.070,f'{task}  {delta:+.2f} pp',ha='center',va='center',fontsize=7,
                              color='#333333',transform=cloud.transAxes)
            texts.append(txt2)
        ax = fig.add_axes([left,.13,right-left,.345])
        ax.axhline(0,color='#777777',lw=.65,zorder=1)
        for g, sdg in enumerate(SDGS):
            for k, task in enumerate(TASKS):
                row = c[c.agency.eq(agency)&c.sdg.eq(sdg)&c.task.eq(task)].iloc[0]
                x = g + (k-2.5)*.125
                # Intervals plotted independently: percentile intervals need not contain the point estimate.
                ax.plot([x,x],[row.ci_low,row.ci_high],color=COLORS[k],alpha=.46,lw=.65,zorder=2)
                point = ax.scatter(x,row.contribution_pp,s=10,marker=MARKERS[k],facecolor=COLORS[k],
                                   edgecolor='white',linewidth=.22,zorder=3)
                point.set_gid(f'contribution_{agency}_{sdg}_{task}')
        ax.set_xlim(-.65,11.65)
        ax.set_ylim(-bound,bound)
        ax.set_xticks(range(12),GOALS)
        ax.set_yticks(np.arange(-bound,bound+.1,4))
        ax.set_xlabel('SDG', labelpad=5)
        ax.set_title('Contributions from all 12 SDGs',fontsize=8,pad=8)
        if ai == 0:
            ax.set_ylabel('Contribution to task shift (percentage points)',labelpad=5)
        ax.tick_params(direction='out',length=2.4,width=.55,pad=3)
        ax.spines[['top','right']].set_visible(False)
    fig.text(.54,.512,'Net task shift = sum of the SDG contributions below',ha='center',fontsize=7,color='#444444')
    # Shape plus hue identifies tasks even in grayscale; no sign encoded by color.
    handles = [plt.Line2D([],[],marker=m,linestyle='',markersize=3.5,color=c,label=t) for m,c,t in zip(MARKERS,COLORS,TASKS)]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.54,.028),ncol=6,frameon=False,
               fontsize=7,handletextpad=.4,columnspacing=1.6)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [t.get_window_extent(renderer) for t in texts]
    assert not any(b.overlaps(other) for i,b in enumerate(boxes) for other in boxes[i+1:]), 'Term overlap'
    for text in fig.findobj(matplotlib.text.Text):
        if text.get_visible() and text.get_text():
            box = text.get_window_extent(renderer)
            assert box.x0 >= -1 and box.y0 >= -1 and box.x1 <= fig.bbox.width+1 and box.y1 <= fig.bbox.height+1, text.get_text()
    fig.savefig(OUT / f'{STEM}.svg')
    fig.savefig(OUT / f'{STEM}.pdf')
    fig.savefig(OUT / f'{STEM}.png',dpi=600)
    fig.savefig(OUT / f'{STEM}.tiff',dpi=600,pil_kwargs={'compression':'tiff_lzw'})
    fig.savefig(OUT / f'{STEM}_preview.png',dpi=300)
    plt.close(fig)
    import xml.etree.ElementTree as ET
    svg = ET.parse(OUT / f'{STEM}.svg')
    ids = [e.get('id','') for e in svg.iter()]
    assert sum(i.startswith('contribution_') for i in ids) == 144
    assert sum(i.startswith('term_') for i in ids) == 12
    assert len(list(svg.iter('{http://www.w3.org/2000/svg}text'))) > 50
    print('PASS: 12 task summaries; 144 contributions; closure; source agreement; 2000 family-bootstrap draws; editable SVG; no term overlap or canvas clipping.')
    print(s[['agency','task','delta_pp','ci_low','ci_high']].round(3).to_string(index=False))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reuse',action='store_true',help='Render existing source tables without repeating bootstrap')
    parser.add_argument('--check',action='store_true',help='Validate source tables only')
    args = parser.parse_args()
    if args.check:
        check_tables()
        print('PASS: complete country/SDG/task tables and exact aggregation identities.')
    else:
        if not args.reuse:
            analyse()
        plot()
