"""One national-composition chart with full-width overall-alignment horizontal bars.
Uses the validated composition and bootstrap tables; no resampling.
Run directly with the existing py311 environment.
"""
from pathlib import Path
import hashlib
import json
import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from matplotlib.offsetbox import AnnotationBbox, HPacker, TextArea
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=Path(os.environ.get('DATA_PATH', str(ROOT/'data'/'Figure4a_composition_data.csv'))).parent
OUT=Path(os.environ.get('OUTPUT_DIR', str(ROOT/'outputs')))
QA=ROOT/'workspace'
COLORS={'NSF':'#3775BA','NSFC':'#B64342'}
ORDER=[2,3,6,7,9,10,11,12,13,15,16,17]
for folder in [DATA,OUT,QA]: folder.mkdir(parents=True,exist_ok=True)
comp=pd.read_csv(DATA/'Figure4a_composition_data.csv')
summary=pd.read_csv(DATA/'Figure4a_overall_metrics.csv').set_index('agency')
boot=pd.read_csv(DATA/'Figure4a_bootstrap_overall_metrics.csv')
assert len(comp)==24 and not comp.duplicated(['agency','sdg_number']).any()
checks=[]
for agency in COLORS:
    part=comp[comp.agency.eq(agency)].set_index('sdg_number').loc[ORDER]
    p,q=part.supply_share.to_numpy(),part.challenge_share.to_numpy()
    assert np.isfinite([p,q]).all() and (p>0).all() and (q>0).all()
    assert np.allclose([p.sum(),q.sum()],1)
    observed={'composition_overlap':np.minimum(p,q).sum(),
              'aitchison_distance':np.linalg.norm(np.log(p)-np.log(p).mean()-np.log(q)+np.log(q).mean())}
    for metric,value in observed.items():
        row=summary.loc[agency]; samples=boot[boot.agency.eq(agency)][metric].to_numpy()
        assert len(samples)==int(row.bootstrap_resamples)==2000
        interval=np.quantile(samples,[.025,.975])
        assert np.isclose(value,row[metric])
        assert np.allclose(interval,row[[metric+'_ci_low',metric+'_ci_high']].to_numpy(float))
        checks.append({'agency':agency,'metric':metric,'estimate':value,'ci95':interval.tolist()})

plt.rcParams.update({'font.family':'Arial','font.size':7,'axes.labelsize':7,
                     'xtick.labelsize':6.2,'ytick.labelsize':6.2,'text.color':'#1F2933',
                     'axes.labelcolor':'#1F2933','svg.fonttype':'none','pdf.fonttype':42,
                     'hatch.linewidth':.3,'legend.frameon':False,'axes.linewidth':.75})
BAR_HEIGHT_MM=110*.62
SHARE_UNIT_MM=BAR_HEIGHT_MM/58
CANVAS_H=110+20*SHARE_UNIT_MM
fig=plt.figure(figsize=(183/25.4,CANVAS_H/25.4),facecolor='white')
ax=fig.add_axes([.09,110*.17/CANVAS_H,.89,78*SHARE_UNIT_MM/CANVAS_H])
def top_y(old): return 1-(1-old)*110/CANVAS_H
def bottom_y(old): return old*110/CANVAS_H
def metric_y(value): return (value+18)/78
for spine in ax.spines.values(): spine.set_color('black')
x=np.arange(12); bars=[]; labels=[]
for agency,offset in [('NSF',-.19),('NSFC',.19)]:
    part=comp[comp.agency.eq(agency)].set_index('sdg_number').loc[ORDER]
    supply=part.supply_share.to_numpy()*100; challenge=part.challenge_share.to_numpy()*100
    up=ax.bar(x+offset,supply,width=.32,color=COLORS[agency],linewidth=0,zorder=3)
    down=ax.bar(x+offset,-challenge,width=.32,color='#D2D6DA',edgecolor=COLORS[agency],hatch='///',linewidth=.45,zorder=3)
    assert np.allclose([b.get_height() for b in up],supply)
    assert np.allclose([b.get_height() for b in down],-challenge)
    bars.extend(up); bars.extend(down)
    for xi,s,c in zip(x+offset,supply,challenge):
        labels.append(ax.text(xi,s+.6,f'{s:.1f}',ha='center',va='bottom',color=COLORS[agency],fontsize=6.0))
        labels.append(ax.text(xi,-c-.55,f'{c:.1f}',ha='center',va='top',color=COLORS[agency],fontsize=6.0))
ax.set(xlim=(-.65,11.65),ylim=(-18,60),xticks=x,xticklabels=ORDER,
       yticks=[-15,-10,-5,0,10,20,30,40],xlabel='SDG',ylabel='SDG composition share (%)')
ax.yaxis.set_major_formatter(FuncFormatter(lambda value,_:f'{abs(value):g}'))
ax.tick_params(axis='x',length=0,pad=5); ax.tick_params(axis='y',length=3,width=.7)
ax.xaxis.labelpad=3; ax.yaxis.labelpad=7
ax.yaxis.set_label_coords(-.05,metric_y(11))
ax.set_axisbelow(True); ax.grid(axis='y',color='#E3E6E9',lw=.45)
for line,value in zip(ax.get_ygridlines(),ax.get_yticks()):
    if value==40: line.set_visible(False)
ax.axhline(0,color='black',lw=.85,zorder=4)
ax.text(.985,metric_y(39.0),'Research supply ↑',transform=ax.transAxes,ha='right',va='top',fontsize=6.3,fontweight='bold')
ax.text(.985,metric_y(-17.25),'National challenge composition ↓',transform=ax.transAxes,ha='right',va='bottom',fontsize=5.7,color='#626C75')

fig.text(.025,top_y(.975),'a',fontsize=12,fontweight='bold',va='top')
fig.text(.09,top_y(.974),'National research-supply and SDG-challenge alignment',fontsize=10.1,fontweight='bold',va='top')
fig.text(.09,top_y(.93),'Research portfolios and SDSN-derived national challenge compositions · 2015–2025',fontsize=6.4,color='#67727D',va='top')
for agency,left,title in [('NSF',.09,'United States · NSF'),('NSFC',.56,'China · NSFC')]:
    row=summary.loc[agency]
    fig.text(left,top_y(.879),title,color=COLORS[agency],fontsize=8.5,fontweight='bold')
    fig.text(left,top_y(.849),f'{int(row.n_project_families):,} project families · observed {row.observed_project_coverage}',fontsize=6,color='#67727D')
fig.text(.56,top_y(.821),'2024–2025 not observed',fontsize=5.7,color='#67727D')

# Overall bars align with the outer edges of the first and last SDG bars.
# Metric names occupy the same external y-label column; units stay in the names.
metric_text=[]; metric_axis_labels=[]; metric_checks=[]; metric_bars=[]
first_edge=min(b.get_x() for b in bars)
last_edge=max(b.get_x()+b.get_width() for b in bars)
LEFT=(first_edge-ax.get_xlim()[0])/np.ptp(ax.get_xlim())
WIDTH=(last_edge-first_edge)/np.ptp(ax.get_xlim())
metric_specs=[('composition_overlap',100,1,'%',100,[57.0,54.6],'Overall\ncomposition\noverlap (%) ↑'),
              ('aitchison_distance',1,2,'',7,[47.3,44.9],'Overall\nAitchison\ndistance ↓')]
for metric,factor,digits,suffix,axis_max,rows,title in metric_specs:
    metric_axis_labels.append(ax.text(-.05,metric_y(np.mean(rows)),title,transform=ax.transAxes,
              ha='center',va='center',rotation=90,fontsize=5.7,linespacing=1.05,zorder=6,clip_on=False))
    for agency,row_y in zip(COLORS,rows):
        row=summary.loc[agency]
        est,lo,hi=[float(row[k])*factor for k in [metric,metric+'_ci_low',metric+'_ci_high']]
        assert 0<lo<est<hi<axis_max
        py=metric_y(row_y); px=[LEFT+WIDTH*v/axis_max for v in [est,lo,hi]]
        bar_height=1.25/78
        if metric=='composition_overlap':
            ax.add_patch(Rectangle((LEFT,py-bar_height/2),WIDTH,bar_height,transform=ax.transAxes,
                                  facecolor='#EDF0F3',edgecolor='none',zorder=5))
        bar=Rectangle((LEFT,py-bar_height/2),WIDTH*est/axis_max,bar_height,transform=ax.transAxes,
                      facecolor=COLORS[agency],edgecolor='none',zorder=6)
        ax.add_patch(bar);metric_bars.append(bar)
        ax.errorbar(px[0],py,xerr=np.array([[px[0]-px[1]],[px[2]-px[0]]]),fmt='none',
                    ecolor='#26323D',elinewidth=.7,capsize=2,capthick=.7,transform=ax.transAxes,zorder=7)
        estimate=TextArea(f'{est:.{digits}f}{suffix}',textprops={'fontsize':6.0,'fontweight':'bold','color':COLORS[agency]})
        interval=TextArea(f'[{lo:.{digits}f}, {hi:.{digits}f}]',textprops={'fontsize':5.6,'color':'#52606C'})
        label=AnnotationBbox(HPacker(children=[estimate,interval],align='baseline',pad=0,sep=2.5),
                (px[2]+.012,py),xycoords=ax.transAxes,box_alignment=(0,.5),frameon=False,pad=0,zorder=7)
        ax.add_artist(label);metric_text.append(label)
        metric_checks.append({'agency':agency,'metric':metric,'estimate':est,'ci95':[lo,hi],
                              'display_range':[0,axis_max],'axes_x_positions':px,'axes_y_position':py,
                              'colored_bar_width':bar.get_width(),'bar_starts_at_zero':True})
assert len(metric_bars)==len(metric_checks)==4
assert all(np.isclose(b.get_x(),LEFT) and np.isclose(b.get_width(),WIDTH*c['estimate']/c['display_range'][1]) for b,c in zip(metric_bars,metric_checks))
assert all(b.get_y()>metric_y(40) for b in metric_bars)

handles=[Patch(facecolor=COLORS[a],label=f'{a} supply') for a in COLORS]
handles += [Patch(facecolor='#D2D6DA',edgecolor=COLORS[a],hatch='///',linewidth=.45,label=f'{country} challenges')
            for a,country in [('NSF','U.S.'),('NSFC','China')]]
fig.legend(handles=handles,ncol=4,loc='center',bbox_to_anchor=(.51,bottom_y(.06)),fontsize=6.1,
           handlelength=1.5,columnspacing=1.6,handletextpad=.5)
fig.text(.09,bottom_y(.018),'Overall bars: blue NSF, red NSFC; independent scales. Gray tails: unshared composition. Whiskers: bootstrap 95% CI.',fontsize=5.5,color='#626C75')

assert len(bars)==len(labels)==48
assert np.allclose(fig.get_size_inches()*25.4,[183,CANVAS_H])
fig.canvas.draw(); renderer=fig.canvas.get_renderer()
bounds=[label.get_window_extent(renderer) for label in labels]
collisions=[(i,j) for i in range(48) for j in range(i+1,48) if bounds[i].overlaps(bounds[j])]
assert not collisions,collisions
metric_bounds=[label.get_window_extent(renderer) for label in metric_text]
bad=[(i,j,str(metric_text[i]),str(metric_text[j])) for i,a in enumerate(metric_bounds) for j,b in enumerate(metric_bounds) if i<j and a.overlaps(b)]
assert not bad,bad
assert all(not t.overlaps(b) for t in metric_bounds for b in bounds),'Metric text overlaps bar values'
assert all(not t.overlaps(b.get_window_extent(renderer)) for t in metric_bounds for b in bars),'Metric text overlaps bars'
assert all(ax.get_window_extent(renderer).contains(*p) for t in metric_bounds for p in t.get_points()),'Metric text outside main frame'
axis_label_bounds=[label.get_window_extent(renderer) for label in metric_axis_labels]
assert not axis_label_bounds[0].overlaps(axis_label_bounds[1]),'Overall metric names collide'
assert all(t.x1<ax.get_window_extent(renderer).x0 for t in axis_label_bounds),'Metric name inside frame'
assert all(fig.bbox.contains(*p) for t in axis_label_bounds for p in t.get_points()),'Metric name outside canvas'
assert all(not t.overlaps(ax.yaxis.label.get_window_extent(renderer)) for t in axis_label_bounds)
assert np.isclose(LEFT,(min(b.get_x() for b in bars)-ax.get_xlim()[0])/np.ptp(ax.get_xlim()))
assert all(fig.bbox.contains(*p) for t in bounds for p in t.get_points())
assert np.isclose(ax.get_position().height*CANVAS_H*58/78,BAR_HEIGHT_MM)
assert all(b.get_y()>metric_y(40) for b in metric_bars)
assert len(metric_checks)==4
stem=OUT/'Figure4a_aligned_bars_external_metric_axis'
for ext in ['png','pdf','svg','tiff']:
    kwargs={'facecolor':'white','dpi':600}
    if ext=='tiff':kwargs['pil_kwargs']={'compression':'tiff_lzw'}
    fig.savefig(stem.with_suffix('.'+ext),**kwargs)
fig.savefig(OUT/'Figure4a_aligned_bars_external_metric_axis_preview.png',dpi=240,facecolor='white')
report={'canvas_mm':[183,CANVAS_H],'source_rows':24,'supply_bars':24,'challenge_bars':24,'bar_value_labels':48,
        'excluded_rows':0,'bar_label_collisions':collisions,'metric_text_collisions':False,'metric_graphics_overlap_bars_or_values':False,'bar_region_mm':[183*.89,BAR_HEIGHT_MM],'metric_scale_width_fraction':WIDTH,'aligned_start_data_x':first_edge,'metric_x_axes_visible':False,'metric_country_row_labels_visible':False,'metric_names_outside_frame':True,'metric_graphics':metric_checks,
        'palette':COLORS,'overall_estimates_and_intervals':checks,'bootstrap_recomputed':False,
        'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in DATA.glob('*.csv')}}
(QA/'full_width_bar_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('checks_passed: 24 records, 48 bars and values, 4 metric intervals')
plt.close(fig)
