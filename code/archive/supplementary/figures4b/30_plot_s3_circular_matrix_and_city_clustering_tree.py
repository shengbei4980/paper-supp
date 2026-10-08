"""Modelviz rel_circular_grouped_correlation_heatmap adaptation.

Preserves the polar, open-ring matrix and radial grouping conventions.
Replaces demonstration correlations with observed binary presence and adds
the approved Jaccard / average-linkage city dendrogram. Original templates
and source data are read-only.
"""
import os
import sys
import json
import hashlib
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import linkage, leaves_list

BASE = Path(__file__).resolve().parent.parent
SOURCE = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get('DATA_PATH', str(BASE/'数据'/'输入数据'/'city_stable_pair_profiles_long.csv'))).parent
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else os.environ.get('OUTPUT_DIR', str(BASE/'图')))
DATA = BASE / '数据'
REPORT = BASE / '代码' / '核查报告'
REPORT.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.family': ['Arial', 'Microsoft YaHei', 'DejaVu Sans'],
                     'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none',
                     'font.size': 9, 'axes.unicode_minus': False})
COLORS = {'NSF': '#003366', 'NSFC': '#8B0000'}
TEXT = '#202830'
GRAY = '#747D85'
profiles = pd.read_csv(SOURCE / 'city_stable_pair_profiles_long.csv')
pairs = pd.read_csv(SOURCE / 'stable_target_pairs.csv')
events = pd.read_csv(SOURCE / 'project_stable_pair_events.csv')
nodes = pd.read_csv(SOURCE / 'city_nodes_all.csv')
assert len(pairs) == 62 and pairs.pair_id.nunique() == 62
assert not events.duplicated(['agency', 'record_id', 'city_id', 'pair_id']).any()

# Both figures retain one fixed ring order: shared stable, NSF-only stable,
# NSFC-only stable; within a class use the source catalog order.
pairs['stable_group'] = np.select(
    [pairs.stable_nsf & pairs.stable_nsfc, pairs.stable_nsf],
    ['Both', 'NSF only'], default='NSFC only')
pairs['group_order'] = pairs.stable_group.map({'Both': 0, 'NSF only': 1, 'NSFC only': 2})
pairs = pairs.sort_values('group_order', kind='stable').reset_index(drop=True)
pairs.insert(0, 'pair_code', [f'P{i:02d}' for i in range(1, 63)])
pair_order = pairs.pair_id.tolist()
coverage = []
agencies = {}
audit = {'metric': 'Jaccard on binary presence', 'linkage': 'average',
         'optimal_leaf_ordering': True, 'city_unit': 'institution city',
         'event_unit': 'project record', 'absent_cell': 'not observed in this sample',
         'ring_order': pair_order, 'countries': {}}
for agency, prefix in [('NSF', 'U'), ('NSFC', 'C')]:
    ev = events.loc[events.agency == agency]
    counts = ev.groupby(['city_id', 'pair_id']).record_id.nunique().unstack(fill_value=0)
    counts = counts.reindex(columns=pair_order, fill_value=0).sort_index()
    supplied = profiles.loc[profiles.agency == agency].pivot(
        index='city_id', columns='pair_id', values='pair_project_count')
    supplied = supplied.reindex(index=counts.index, columns=pair_order).fillna(0)
    assert np.array_equal(counts.to_numpy(), supplied.to_numpy())
    binary = (counts > 0).astype('uint8')
    assert (binary.sum(axis=1) > 0).all()
    distance = pdist(binary.to_numpy(), metric='jaccard')
    z = linkage(distance, method='average', optimal_ordering=True)
    leaf_order = leaves_list(z)
    ordered = binary.iloc[leaf_order]
    index = nodes.set_index('city_id').loc[ordered.index,
        ['institution_city', 'institution_region', 'project_count']].reset_index()
    index.insert(0, 'city_code', [f'{prefix}{i:03d}' for i in range(1, len(index)+1)])
    index.insert(0, 'agency', agency)
    index['observed_pair_count'] = ordered.sum(axis=1).to_numpy()
    index.to_csv(DATA / f'{agency}_city_index.csv', index=False, encoding='utf-8-sig')
    ordered.to_csv(DATA / f'{agency}_presence_clustered.csv', encoding='utf-8-sig')
    counts.iloc[leaf_order].to_csv(DATA / f'{agency}_record_counts_clustered.csv', encoding='utf-8-sig')
    pd.DataFrame(z, columns=['child1', 'child2', 'jaccard_height', 'leaf_count']).to_csv(
        DATA / f'{agency}_linkage.csv', index=False)
    c = binary.sum(axis=0).astype(int)
    pairs[f'{agency}_cities'] = c.reindex(pair_order).to_numpy()
    agencies[agency] = dict(binary=binary, ordered=ordered, z=z, order=leaf_order, index=index)
    audit['countries'][agency] = dict(cities=len(binary), cells=int(binary.size),
        occupied_cells=int(binary.to_numpy().sum()), distinct_profiles=len(binary.drop_duplicates()),
        all_leaves_retained=len(set(leaf_order)) == len(binary),
        count_matrix_matches_source=True)

pairs.drop(columns='group_order').to_csv(DATA / 'Target_pair_index_and_city_coverage.csv',
                                       index=False, encoding='utf-8-sig')
audit['source_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
    for p in [SOURCE/'stable_target_pairs.csv', SOURCE/'project_stable_pair_events.csv',
              SOURCE/'city_stable_pair_profiles_long.csv', SOURCE/'city_nodes_all.csv']}
(REPORT/'figure_data_audit.json').write_text(
    json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')

START, END = np.deg2rad(25), np.deg2rad(335)
ROOT, LEAF, INNER, OUTER = 0.055, 0.31, 0.34, 1.0
ring_edges = np.linspace(INNER, OUTER, 63)
group_bounds = [0, 22, 42, 62]

def plot_country(ax, agency):
    obj = agencies[agency]
    n = len(obj['ordered'])
    edges = np.linspace(START, END, n+1)
    angles = (edges[:-1]+edges[1:])/2
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 1.095)
    ax.set_axis_off()
    ax.pcolormesh(edges, ring_edges, obj['ordered'].to_numpy().T,
                  cmap=ListedColormap(['#FFFFFF', COLORS[agency]]),
                  vmin=0, vmax=1, shading='flat', rasterized=False, zorder=3)
    arc = np.linspace(START, END, 600)
    for k,r in enumerate(ring_edges):
        ax.plot(arc, np.full_like(arc,r), color='#000000', lw=.12, zorder=4)
    for k in group_bounds:
        r = ring_edges[k]
        ax.plot(arc, np.full_like(arc,r), color='#000000', lw=.60, zorder=5)
    # Sparse angular guides distinguish city sectors without hiding cells.
    step = 20 if agency == 'NSF' else 10
    for k in range(0,n+1,step):
        ax.plot([edges[k]]*2,[INNER,OUTER],color='#000000',lw=.12,zorder=4)
    for angle in [START, END]:
        ax.plot([angle]*2,[INNER,OUTER],color='#000000',lw=.60,zorder=5)
    # Tree leaf coordinates use exactly the heatmap column order.
    positions = {int(leaf): (angles[k],LEAF) for k,leaf in enumerate(obj['order'])}
    for leaf,(theta,r) in positions.items():
        ax.plot([theta,theta],[r,INNER-.004],color='#A4ABB1',lw=.30,zorder=2)
    for k,row in enumerate(obj['z']):
        left,right = int(row[0]),int(row[1])
        ta,ra = positions[left];tb,rb = positions[right]
        r = LEAF - float(row[2])*(LEAF-ROOT)
        t = (ta+tb)/2
        for theta,child_r in [(ta,ra),(tb,rb)]:
            ax.plot([theta,theta],[r,child_r],color=GRAY,lw=.39,zorder=2)
        a = np.linspace(min(ta,tb),max(ta,tb),max(4,int(abs(tb-ta)*45)))
        ax.plot(a,np.full_like(a,r),color=GRAY,lw=.39,zorder=2)
        positions[n+k] = (t,r)
    # Use actual Target codes, not opaque P codes. Identical sampled rings
    # are labelled in both circles; the full 62-row index remains available.
    for i in [*range(0,57,4),61]:
        r = (ring_edges[i]+ring_edges[i+1])/2
        row = pairs.iloc[i]
        y = r*np.cos(START)
        ax.text(0,y,f'{row.target_a} + {row.target_b}',ha='center',va='center',
                fontsize=8,color='#000000',bbox=dict(facecolor='white',edgecolor='none',pad=.2),zorder=7)
        # Horizontal leaders align each label with its precise ring at the cut.
        x = np.linspace(.125,r*np.sin(START),20)
        ax.plot(np.arctan2(x,y),np.hypot(x,y),color='#000000',lw=.32,zorder=5)
    ax.text(0,1.073,'Target pairs',ha='center',va='center',fontsize=9,fontweight='bold',color=TEXT)
    ticks = sorted(set([0,*range(step-1,n,step),n-1]))
    for k in ticks:
        theta = angles[k]
        ax.plot([theta]*2,[1.002,1.014],color=TEXT,lw=.45)
        deg=np.rad2deg(theta)
        rotation = -deg if deg<90 or deg>270 else 180-deg
        ax.text(theta,1.043,obj['index'].city_code.iloc[k],rotation=rotation,
                ha='center',va='center',fontsize=7.3,color=TEXT)
    ax.text(0,0,agency,ha='center',va='center',fontsize=7,fontweight='bold',color=COLORS[agency])
    # Same distance-to-radius transformation in both countries.
    for d in [0,.5,1]:
        r=LEAF-d*(LEAF-ROOT)
        ax.plot([np.deg2rad(-3),np.deg2rad(3)],[r,r],color=GRAY,lw=.6)
        ax.text(0,r-.017,f'{d:g}',fontsize=5.7,ha='center',va='top',color=GRAY)
    ax.plot([0,0],[ROOT,LEAF],color=GRAY,lw=.45)
    ax.text(np.deg2rad(-16),.20,'Jaccard',rotation=90,ha='center',va='center',
            fontsize=5.8,color=GRAY)

fig = plt.figure(figsize=(20,12),facecolor='white')
fig.text(.04,.954,'S3',fontsize=19,fontweight='bold',color=TEXT)
fig.text(.095,.955,'Stable Target combinations across research cities',
         fontsize=20,fontweight='bold',color=TEXT)
fig.text(.095,.918,'62 combinations  |  All 429 cities with at least one observed combination',
         fontsize=11.8,color=GRAY)
for left,agency,label in [(.025,'NSF','a'),(.515,'NSFC','b')]:
    obj=agencies[agency]
    fig.text(left+.033,.868,f'{label}   {agency}',fontsize=15,fontweight='bold',color=COLORS[agency])
    fig.text(left+.033,.841,f'{len(obj["ordered"])} institution cities',fontsize=10.5,color=GRAY)
    ax=fig.add_axes([left,.175,.46,.665],projection='polar')
    plot_country(ax,agency)
fig.legend(handles=[Patch(facecolor=COLORS['NSF'],label='Observed in NSF'),
                    Patch(facecolor=COLORS['NSFC'],label='Observed in NSFC'),
                    Patch(facecolor='white',edgecolor='#B0B6BC',label='Not observed'),
                    Line2D([0],[0],color=GRAY,lw=1,label='City-profile clustering')],
           loc='lower center',bbox_to_anchor=(.5,.134),ncol=4,frameon=False,
           fontsize=10.2,handlelength=1.5,columnspacing=2.5)
fig.text(.5,.098,'Each spoke = one city; each ring = one Target pair. Pair order is identical in both countries.',
         fontsize=10,ha='center',color=TEXT)
fig.text(.5,.07,'Inner to outer: 22 pairs stable in both countries, 20 in NSF only, 20 in NSFC only; black arcs mark boundaries.',
         fontsize=9.5,ha='center',color=GRAY)
fig.text(.5,.042,'Trees use binary Jaccard distance and average linkage; branches indicate similarity, not collaboration.',
         fontsize=9.5,ha='center',color=GRAY)
fig.text(.5,.016,'Selected rings are labelled with their Target codes. All 62 pairs, city names and coverage counts are in the index.',
         fontsize=9.2,ha='center',color=GRAY)
stem='FigureS3_全量城市Target组合_清晰标注版'
for fmt in ['png','pdf','svg']:
    fig.savefig(OUT/f'{stem}.{fmt}',dpi=350,facecolor='white')
plt.close(fig)

# Country enlargements preserve exactly the same matrices and coordinates.
for agency in ['NSF', 'NSFC']:
    fig=plt.figure(figsize=(12,12),facecolor='white')
    fig.text(.05,.963,f'{agency} | Stable Target combinations across cities',
             fontsize=19,fontweight='bold',color=COLORS[agency])
    fig.text(.05,.931,f'{len(agencies[agency]["ordered"])} institution cities · all 62 combinations',
             fontsize=12,color=GRAY)
    ax=fig.add_axes([.035,.075,.93,.84],projection='polar')
    plot_country(ax,agency)
    fig.text(.5,.044,'Each spoke = one city; each ring = one Target pair. Colour = observed; white = not observed.',
             ha='center',fontsize=10,color=TEXT)
    fig.text(.5,.020,'Tree: Jaccard similarity clustering. Full Target and city names are supplied in the accompanying index.',
             ha='center',fontsize=9,color=GRAY)
    for fmt in ['png','pdf']:
        fig.savefig(OUT/f'FigureS3_{agency}_外环放大版.{fmt}',dpi=350,facecolor='white')
    plt.close(fig)

# Exact per-pair coverage, readable without tracing hundreds of sectors.
with PdfPages(OUT/'FigureS3_完整组合与城市索引.pdf') as pdf:
    fig=plt.figure(figsize=(11.7,8.3),facecolor='white')
    fig.text(.05,.944,'Target-pair index and observed city coverage',fontsize=16,fontweight='bold')
    fig.text(.05,.905,'All 62 pairs; counts refer to distinct institution cities, not project records.',fontsize=9,color=GRAY)
    for side in range(2):
        x=.05+side*.49
        heads=[('ID',x),('Target pair',x+.065),('Stability',x+.205),('NSF',x+.35),('NSFC',x+.407)]
        for txt,xx in heads:fig.text(xx,.856,txt,fontsize=9,fontweight='bold')
        for j in range(31):
            row=pairs.iloc[side*31+j];y=.829-j*.0227
            if j%2==0:
                fig.add_artist(plt.Rectangle((x-.003,y-.004),.455,.0215,transform=fig.transFigure,
                    color='#F3F5F6',zorder=0,lw=0))
            vals=[row.pair_code,row.pair_id,row.stable_group,str(row.NSF_cities),str(row.NSFC_cities)]
            for k,((txt,xx),val) in enumerate(zip(heads,vals)):
                fig.text(xx,y,val,fontsize=8.5,color=COLORS['NSF'] if k==3 else COLORS['NSFC'] if k==4 else TEXT)
    fig.text(.05,.061,'Stability refers to the national test. Every selected pair is displayed in both countries, including observed zeros.',fontsize=8,color=GRAY)
    fig.text(.05,.035,'Full official Target labels and all record counts are available in the accompanying CSV files.',fontsize=8,color=GRAY)
    pdf.savefig(fig);fig.savefig(OUT/'FigureS3_组合编号与城市覆盖数.png',dpi=200);plt.close(fig)
    # Full city labels in leaf order, preserving the overview IDs.
    for agency in ['NSF','NSFC']:
        idx=agencies[agency]['index']
        page_size=100
        for start in range(0,len(idx),page_size):
            fig=plt.figure(figsize=(11.7,8.3),facecolor='white')
            fig.text(.05,.943,f'{agency} city index | {start+1}–{min(start+page_size,len(idx))} of {len(idx)}',fontsize=16,fontweight='bold',color=COLORS[agency])
            fig.text(.05,.9,'IDs follow tree-leaf order. Region codes distinguish cities with the same name.',fontsize=9,color=GRAY)
            part=idx.iloc[start:start+page_size]
            for j,row in enumerate(part.itertuples(index=False)):
                col=j//50;k=j%50;x=.05+col*.49;y=.86-k*.0154
                fig.text(x,y,row.city_code,fontsize=7.8,color=COLORS[agency])
                name=f'{row.institution_city}, {row.institution_region}'
                fig.text(x+.057,y,name,fontsize=7.1,color=TEXT)
            fig.text(.05,.035,'Tree topology is descriptive; identical binary profiles may have multiple equivalent leaf orders.',fontsize=8,color=GRAY)
            pdf.savefig(fig);plt.close(fig)

print(json.dumps({'figure':stem,'cities':{a:len(agencies[a]['ordered']) for a in agencies},
                  'pairs':62,'nonzero_cells':2570,'index_pages':6}))
