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

# Overall statistics have two country values, so each line joins NSF to NSFC.
# The two metrics share country positions and use explicitly labelled independent scales.
metric_text=[]; metric_lines=[]; metric_artists=[]; metric_checks=[]
mask=Rectangle((.017,.60),.493,.379,transform=ax.transAxes,facecolor='white',edgecolor='none',zorder=5)
ax.add_patch(mask)
metric_text.append(ax.text(.025,.958,'Overall alignment',transform=ax.transAxes,fontsize=6.7,fontweight='bold',va='top',zorder=6))
country_x={'NSF':.282,'NSFC':.447}
for agency in COLORS:
    metric_text.append(ax.text(country_x[agency],.91,agency,transform=ax.transAxes,ha='center',va='center',fontsize=6.0,fontweight='bold',color=COLORS[agency],zorder=6))
metric_specs=[('composition_overlap',100,1,'%',(51,56),.785,.087,.757,.831,'Composition overlap ↑'),
              ('aitchison_distance',1,2,'',(4.3,6.3),.642,.067,.618,.680,'Aitchison distance ↓')]
for metric,factor,digits,suffix,limits,bottom,height,value_y,label_y,title in metric_specs:
    metric_text.append(ax.text(.025,label_y,title,transform=ax.transAxes,ha='left',va='center',fontsize=6.1,fontweight='bold',zorder=6))
    coords=[]
    for agency in COLORS:
        row=summary.loc[agency]
        est,lo,hi=[float(row[k])*factor for k in [metric,metric+'_ci_low',metric+'_ci_high']]
        assert limits[0]<lo<est<hi<limits[1]
        py=[bottom+height*(v-limits[0])/(limits[1]-limits[0]) for v in [est,lo,hi]]
        xpos=country_x[agency];coords.append((xpos,py[0]))
        ci=ax.errorbar(xpos,py[0],yerr=np.array([[py[0]-py[1]],[py[2]-py[0]]]),
                      fmt='o',markersize=3.6,mfc=COLORS[agency],mec=COLORS[agency],
                      ecolor='#26323D',elinewidth=.65,capsize=2,capthick=.65,
                      transform=ax.transAxes,zorder=7)
        metric_artists.append(ci.lines[0])
        estimate=TextArea(f'{est:.{digits}f}{suffix}',textprops={'fontsize':5.8,'fontweight':'bold','color':COLORS[agency]})
        interval=TextArea(f'[{lo:.{digits}f}, {hi:.{digits}f}]',textprops={'fontsize':5.4,'color':'#52606C'})
        label=AnnotationBbox(HPacker(children=[estimate,interval],align='baseline',pad=0,sep=2.5),
                (xpos,value_y),xycoords=ax.transAxes,box_alignment=(.5,.5),frameon=False,pad=0,zorder=7)
        ax.add_artist(label);metric_text.append(label)
        metric_checks.append({'agency':agency,'metric':metric,'estimate':est,'ci95':[lo,hi],
                              'display_range':list(limits),'axes_y_positions':py,'axes_x_position':xpos})
    metric_lines.extend(ax.plot(*zip(*coords),transform=ax.transAxes,color='#52606C',lw=.85,zorder=6))
    for value in limits:
        ypos=bottom+height*(value-limits[0])/(limits[1]-limits[0])
        metric_lines.extend(ax.plot([.245,.251],[ypos,ypos],transform=ax.transAxes,color='#939DA7',lw=.4,zorder=6))
        metric_text.append(ax.text(.239,ypos,f'{value:g}',transform=ax.transAxes,ha='right',va='center',fontsize=5.0,color='#52606C',zorder=6))
assert all(np.isclose(p.get_xdata()[0],c['axes_x_position']) and np.isclose(p.get_ydata()[0],c['axes_y_positions'][0]) for p,c in zip(metric_artists,metric_checks))

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
bad=[(i,j,str(metric_text[i]),str(metric_text[j])) for i,a in enumerate(metric_bounds) for j,b in enumerate(metric_bounds) if i<j and a.overlaps(b)]
assert not bad,bad
assert all(not t.overlaps(b) for t in metric_bounds for b in bounds),'Metric text overlaps bar values'
assert all(not t.overlaps(b.get_window_extent(renderer)) for t in metric_bounds for b in bars),'Metric text overlaps bars'
assert all(ax.get_window_extent(renderer).contains(*p) for t in metric_bounds for p in t.get_points()),'Metric text outside main frame'
assert all(fig.bbox.contains(*p) for t in bounds for p in t.get_points())
mask_bounds=mask.get_window_extent(renderer)
assert all(not mask_bounds.overlaps(b.get_window_extent(renderer)) for b in bars),'Inset mask covers bars'
assert all(not mask_bounds.overlaps(b) for b in bounds),'Inset mask covers bar values'
assert len(metric_checks)==4
stem=OUT/'Figure4a_全量构成与总体折线_重构'
for ext in ['png','pdf','svg','tiff']:
    kwargs={'facecolor':'white','dpi':600}
    if ext=='tiff':kwargs['pil_kwargs']={'compression':'tiff_lzw'}
    fig.savefig(stem.with_suffix('.'+ext),**kwargs)
fig.savefig(OUT/'Figure4a_总体折线_preview.png',dpi=240,facecolor='white')
report={'canvas_mm':[183,110],'source_rows':24,'supply_bars':24,'challenge_bars':24,'bar_value_labels':48,
        'excluded_rows':0,'bar_label_collisions':collisions,'metric_text_collisions':False,'inset_covers_bars_or_values':False,'metric_graphics':metric_checks,
        'palette':COLORS,'overall_estimates_and_intervals':checks,'bootstrap_recomputed':False,
        'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in DATA.glob('*.csv')}}
(QA/'line_layout_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('checks_passed: 24 records, 48 bars and values, 4 metric intervals')
plt.close(fig)
