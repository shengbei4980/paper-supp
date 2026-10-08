"""One national-composition chart with embedded overall-alignment point and interval graphics.
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
DATA=Path(os.environ.get('DATA_PATH', str(ROOT/'data'/'Figure4a_构成数据.csv'))).parent
OUT=Path(os.environ.get('OUTPUT_DIR', str(ROOT/'outputs')))
QA=ROOT/'workspace'
COLORS={'NSF':'#3775BA','NSFC':'#B64342'}
ORDER=[2,3,6,7,9,10,11,12,13,15,16,17]
for folder in [DATA,OUT,QA]: folder.mkdir(parents=True,exist_ok=True)
comp=pd.read_csv(DATA/'Figure4a_构成数据.csv')
summary=pd.read_csv(DATA/'Figure4a_总体指标.csv').set_index('agency')
boot=pd.read_csv(DATA/'Figure4a_bootstrap总体指标.csv')
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
fig=plt.figure(figsize=(183/25.4,110/25.4),facecolor='white')
ax=fig.add_axes([.09,.17,.89,.62])
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
ax.set(xlim=(-.65,11.65),ylim=(-18,40),xticks=x,xticklabels=ORDER,
       yticks=[-15,-10,-5,0,10,20,30,40],xlabel='SDG',ylabel='Composition share (%)')
ax.yaxis.set_major_formatter(FuncFormatter(lambda value,_:f'{abs(value):g}'))
ax.tick_params(axis='x',length=0,pad=5); ax.tick_params(axis='y',length=3,width=.7)
ax.xaxis.labelpad=3; ax.yaxis.labelpad=7
ax.set_axisbelow(True); ax.grid(axis='y',color='#E3E6E9',lw=.45)
ax.axhline(0,color='black',lw=.85,zorder=4)
ax.text(.985,.963,'Research supply ↑',transform=ax.transAxes,ha='right',va='top',fontsize=6.3,fontweight='bold')
ax.text(.985,.013,'National challenge composition ↓',transform=ax.transAxes,ha='right',va='bottom',fontsize=5.7,color='#626C75')

fig.text(.025,.975,'a',fontsize=12,fontweight='bold',va='top')
fig.text(.09,.974,'National research-supply and SDG-challenge alignment',fontsize=10.1,fontweight='bold',va='top')
fig.text(.09,.93,'Research portfolios and SDSN-derived national challenge compositions · 2015–2025',fontsize=6.4,color='#67727D',va='top')
for agency,left,title in [('NSF',.09,'United States · NSF'),('NSFC',.56,'China · NSFC')]:
    row=summary.loc[agency]
    fig.text(left,.879,title,color=COLORS[agency],fontsize=8.5,fontweight='bold')
    fig.text(left,.849,f'{int(row.n_project_families):,} project families · observed {row.observed_project_coverage}',fontsize=6,color='#67727D')
fig.text(.56,.821,'2024–2025 not observed',fontsize=5.7,color='#67727D')

# Embed independent metric scales in genuinely unused space above the first six SDGs.
# Point positions and whisker widths use the original units; no resampling or invented bounds.
metric_text=[]; metric_lines=[]; metric_artists=[]; metric_checks=[]
mask=Rectangle((.017,.64),.501,.339,transform=ax.transAxes,facecolor='white',edgecolor='none',zorder=5)
ax.add_patch(mask)
metric_text.append(ax.text(.025,.958,'Overall alignment',transform=ax.transAxes,fontsize=6.7,fontweight='bold',va='top',zorder=6))
metric_specs=[('composition_overlap',100,1,'%',.10,.168,(51,56),[51,53,55],
               'Composition overlap ↑','Higher = more shared'),
              ('aitchison_distance',1,2,'',.326,.18,(4.3,6.3),[4.5,5.0,5.5,6.0],
               'Aitchison distance ↓','Lower = closer structure')]
for metric,factor,digits,suffix,left,width,limits,ticks,title,interpretation in metric_specs:
    centre=left+width/2
    metric_text.append(ax.text(centre,.89,title,transform=ax.transAxes,ha='center',va='center',fontsize=6.1,fontweight='bold',zorder=6))
    metric_text.append(ax.text(centre,.855,interpretation,transform=ax.transAxes,ha='center',va='center',fontsize=5.4,color='#67727D',zorder=6))
    for agency,text_y,point_y in [('NSF',.812,.778),('NSFC',.736,.702)]:
        row=summary.loc[agency]
        est,lo,hi=[float(row[k])*factor for k in [metric,metric+'_ci_low',metric+'_ci_high']]
        assert limits[0]<lo<est<hi<limits[1]
        px=[left+width*(value-limits[0])/(limits[1]-limits[0]) for value in [est,lo,hi]]
        ci=ax.errorbar(px[0],point_y,xerr=np.array([[px[0]-px[1]],[px[2]-px[0]]]),
                       fmt='o',markersize=3.5,mfc=COLORS[agency],mec=COLORS[agency],
                       ecolor='#26323D',elinewidth=.7,capsize=2,capthick=.7,
                       transform=ax.transAxes,zorder=7)
        metric_artists.append(ci.lines[0])
        metric_artists.extend(ci.lines[1]); metric_lines.extend(ci.lines[2])
        estimate=TextArea(f'{est:.{digits}f}{suffix}',textprops={'fontsize':5.8,'fontweight':'bold','color':COLORS[agency]})
        interval=TextArea(f'[{lo:.{digits}f}, {hi:.{digits}f}]',textprops={'fontsize':5.4,'color':'#52606C'})
        label=AnnotationBbox(HPacker(children=[estimate,interval],align='baseline',pad=0,sep=2.5),
                (centre,text_y),xycoords=ax.transAxes,box_alignment=(.5,.5),frameon=False,pad=0,zorder=7)
        ax.add_artist(label);metric_text.append(label)
        metric_checks.append({'agency':agency,'metric':metric,'estimate':est,'ci95':[lo,hi],
                              'display_range':list(limits),'axes_positions':px,'display_y':point_y})
    metric_lines.extend(ax.plot([left,left+width],[.665,.665],transform=ax.transAxes,color='#939DA7',lw=.4,zorder=6))
    for value in ticks:
        xpos=left+width*(value-limits[0])/(limits[1]-limits[0])
        metric_lines.extend(ax.plot([xpos,xpos],[.665,.657],transform=ax.transAxes,color='#939DA7',lw=.4,zorder=6))
        metric_text.append(ax.text(xpos,.652,f'{value:g}',transform=ax.transAxes,ha='center',va='top',fontsize=5.2,color='#52606C',zorder=6))
for agency,ypos in [('NSF',.788),('NSFC',.712)]:
    metric_text.append(ax.text(.025,ypos,agency,transform=ax.transAxes,fontsize=6.0,fontweight='bold',color=COLORS[agency],va='center',zorder=6))

handles=[Patch(facecolor=COLORS[a],label=f'{a} supply') for a in COLORS]
handles += [Patch(facecolor='#D2D6DA',edgecolor=COLORS[a],hatch='///',linewidth=.45,label=f'{country} challenges')
            for a,country in [('NSF','U.S.'),('NSFC','China')]]
fig.legend(handles=handles,ncol=4,loc='center',bbox_to_anchor=(.51,.06),fontsize=6.1,
           handlelength=1.5,columnspacing=1.6,handletextpad=.5)
fig.text(.09,.018,'Downward bars: mirrored non-negative shares. Points and whiskers: observed values and project-family bootstrap 95% CI (2,000 resamples).',fontsize=5.5,color='#626C75')

assert len(bars)==len(labels)==48
assert np.allclose(fig.get_size_inches()*25.4,[183,110])
fig.canvas.draw(); renderer=fig.canvas.get_renderer()
bounds=[label.get_window_extent(renderer) for label in labels]
collisions=[(i,j) for i in range(48) for j in range(i+1,48) if bounds[i].overlaps(bounds[j])]
assert not collisions,collisions
metric_bounds=[label.get_window_extent(renderer) for label in metric_text]
assert all(not a.overlaps(b) for i,a in enumerate(metric_bounds) for b in metric_bounds[i+1:]),'Metric text overlaps'
assert all(not t.overlaps(b) for t in metric_bounds for b in bounds),'Metric text overlaps bar values'
assert all(not t.overlaps(b.get_window_extent(renderer)) for t in metric_bounds for b in bars),'Metric text overlaps bars'
assert all(ax.get_window_extent(renderer).contains(*p) for t in metric_bounds for p in t.get_points()),'Metric text outside main frame'
assert all(fig.bbox.contains(*p) for t in bounds for p in t.get_points())
mask_bounds=mask.get_window_extent(renderer)
assert all(not mask_bounds.overlaps(b.get_window_extent(renderer)) for b in bars),'Inset mask covers bars'
assert all(not mask_bounds.overlaps(b) for b in bounds),'Inset mask covers bar values'
assert len(metric_checks)==4
stem=OUT/'Figure4a_全量构成与总体对齐_重构'
for ext in ['png','pdf','svg','tiff']:
    kwargs={'facecolor':'white','dpi':600}
    if ext=='tiff':kwargs['pil_kwargs']={'compression':'tiff_lzw'}
    fig.savefig(stem.with_suffix('.'+ext),**kwargs)
fig.savefig(OUT/'Figure4a_全量构成重构_预览.png',dpi=240,facecolor='white')
report={'canvas_mm':[183,110],'source_rows':24,'supply_bars':24,'challenge_bars':24,'bar_value_labels':48,
        'excluded_rows':0,'bar_label_collisions':collisions,'metric_text_collisions':False,'inset_covers_bars_or_values':False,'metric_graphics':metric_checks,
        'palette':COLORS,'overall_estimates_and_intervals':checks,'bootstrap_recomputed':False,
        'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in DATA.glob('*.csv')}}
(QA/'data_layout_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('checks_passed: 24 records, 48 bars and values, 4 metric intervals')
plt.close(fig)
