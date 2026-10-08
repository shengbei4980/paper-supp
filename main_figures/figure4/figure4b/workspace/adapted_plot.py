"""Figure4d: all Targets, paired-country split cells. Adapted from modelviz 09_REL_005.
Run: python render_figure4d.py --data-path DATA.csv --output-dir DIR
Default input/output paths resolve relative to this file, including workspace copy.
"""
import argparse
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from matplotlib.colors import LinearSegmentedColormap

ROOT=Path(__file__).resolve().parent
if ROOT.name=='workspace': ROOT=ROOT.parent
parser=argparse.ArgumentParser()
parser.add_argument('--data-path',default=os.getenv('DATA_PATH',str(ROOT/'数据/paired_target_metrics.csv')))
parser.add_argument('--output-dir',default=os.getenv('OUTPUT_DIR',str(ROOT/'figures')))
args,_=parser.parse_known_args()
OUT=Path(args.output_dir); OUT.mkdir(parents=True,exist_ok=True)
df=pd.read_csv(args.data_path,dtype={'target':str})
assert len(df)==595 and df.target.nunique()==85 and df.sdg.nunique()==12
assert not df.duplicated(['target','metric']).any()
METRICS=['Share']+[f'K{i:02}' for i in range(1,7)]
COLORS={'nsf':'#3775BA','nsfc':'#B64342'}
CMAPS={c:LinearSegmentedColormap.from_list(c,['#FFFFFF',v],N=256) for c,v in COLORS.items()}
for country in COLORS:
    v=df[f'value_{country}'].dropna()
    assert v.between(0,1.000001).all()
    for _,g in df[df.metric!='Share'].groupby('target'):
        v=g[f'value_{country}']
        assert v.isna().all() or np.isclose(v.sum(),1,atol=2e-6)
    assert np.allclose(df[df.metric=='Share'].groupby('sdg')[f'value_{country}'].sum(),1,atol=2e-6)

plt.rcParams.update({'font.family':'Arial','font.size':6.5,'pdf.fonttype':42,'svg.fonttype':'none',
                     'axes.linewidth':.55,'text.color':'#20262C','axes.labelcolor':'#20262C'})
fig=plt.figure(figsize=(183/25.4,110/25.4),facecolor='white')
fig.text(.018,.969,'d',fontsize=11,fontweight='bold',va='top')
fig.text(.078,.969,'Target carriers and knowledge-task profiles',fontsize=10,fontweight='bold',va='top')
fig.text(.078,.924,'All 85 observed Targets · 12 SDGs',fontsize=6.5,color='#56616B')
# A single key describes the pairing in every cell.
key=fig.add_axes([.731,.915,.028,.038]); key.set(xlim=(0,1),ylim=(1,0)); key.axis('off')
key.add_patch(Polygon([(0,0),(1,0),(0,1)],facecolor=COLORS['nsf'],edgecolor='white',lw=.3))
key.add_patch(Polygon([(1,0),(1,1),(0,1)],facecolor=COLORS['nsfc'],edgecolor='white',lw=.3))
fig.text(.77,.944,'NSF  /  NSFC',fontsize=6.5,va='center')
fig.text(.77,.921,'upper left / lower right',fontsize=5.8,va='center',color='#56616B')

def target_key(t):
    a,b=t.split('.')
    return int(a),(0,int(b)) if b.isdigit() else (1,b)

targets=sorted(df.target.unique(),key=target_key)
lookup=df.set_index(['target','metric'])
seen=[]; absent=0; values=[]; texts=[]
for band,sdgs in enumerate(([2,3,6,7,9,10],[11,12,13,15,16,17])):
    ts=[t for t in targets if int(t.split('.')[0]) in sdgs]
    # Horizontal wrap at an SDG boundary; all cells use the same dimensions.
    xpos={}; groups=[]; cursor=0.
    for sdg in sdgs:
        subset=[t for t in ts if t.startswith(str(sdg)+'.')]
        start=cursor
        for t in subset: xpos[t]=cursor; cursor+=1
        groups.append((sdg,start,cursor)); cursor+=.5
    width=47.5
    ax=fig.add_axes([.078,.565 if band==0 else .205,.905,.267])
    ax.set(xlim=(0,width),ylim=(7.35,0))
    ax.set_yticks([.5]+[i+.85 for i in range(1,7)],METRICS)
    ax.set_xticks([]); ax.tick_params(axis='y',length=0,pad=5,labelsize=6.5)
    for spine in ax.spines.values(): spine.set_visible(False)
    for sdg,start,end in groups:
        ax.text((start+end)/2,-.42,f'SDG{sdg}',ha='center',va='center',fontsize=7,fontweight='bold',clip_on=False)
        ax.add_patch(Rectangle((start,0),end-start,1,facecolor='none',edgecolor='#202020',lw=.4,zorder=4))
        ax.add_patch(Rectangle((start,1.35),end-start,6,facecolor='none',edgecolor='#202020',lw=.4,zorder=4))
    for t in ts:
        seen.append(t); x=xpos[t]
        row=lookup.loc[(t,'Share')]
        flag=bool(row.low_support_nsf or row.low_support_nsfc)
        text=ax.text(x+.5,7.55,t+('†' if flag else ''),rotation=90,ha='center',va='top',fontsize=5.8,clip_on=False)
        texts.append(text)
        for mi,metric in enumerate(METRICS):
            y=mi+(0 if mi==0 else .35)
            r=lookup.loc[(t,metric)]
            triangles=([(x,y),(x+1,y),(x,y+1)],[(x+1,y),(x+1,y+1),(x,y+1)])
            for ci,country in enumerate(COLORS):
                value=r[f'value_{country}']; observed=bool(r[f'observed_{country}'])
                missing=not observed or pd.isna(value)
                color='#ECEDEF' if missing else CMAPS[country](float(value))
                ax.add_patch(Polygon(triangles[ci],facecolor=color,edgecolor='#E2E4E6',lw=.17))
                if missing:
                    absent+=1
                    xx=x+(.27 if ci==0 else .73); yy=y+(.29 if ci==0 else .71)
                    ax.plot([xx-.1,xx+.1],[yy,yy],color='#6A7077',lw=.45)
                else: values.append((t,metric,country,float(value)))

fig.text(.078,.083,'Share (%)',fontsize=6.3,va='center')
gradient=np.linspace(0,1,256).reshape(1,-1)
for i,country in enumerate(COLORS):
    ax=fig.add_axes([.215,.089-i*.023,.28,.016])
    ax.imshow(gradient,cmap=CMAPS[country],vmin=0,vmax=1,aspect='auto',extent=(0,100,0,1))
    ax.set_yticks([]); ax.text(-4,.5,country.upper(),ha='right',va='center',fontsize=5.8)
    ax.set_xticks([0,25,50,75,100] if i==1 else [])
    ax.tick_params(axis='x',length=1.5,pad=1,labelsize=5.6)
    for sp in ax.spines.values(): sp.set_linewidth(.3)
fig.text(.54,.091,'† Low Target support in at least one country',fontsize=5.8,va='center')
fig.text(.54,.067,'Gray / dash: unobserved; white: observed zero',fontsize=5.8,va='center')
fig.text(.078,.018,'Share: Target fraction within its SDG. K01–K06: task fractions within that Target.',fontsize=6,color='#56616B')

# Data and layout checks remain runnable with each export.
assert len(seen)==85 and len(set(seen))==85 and set(seen)==set(targets)
assert len(values)+absent==1190 and absent==154  # 22 profiles × seven metrics.
fig.canvas.draw()
renderer=fig.canvas.get_renderer()
assert all(fig.bbox.contains(*p) for text in texts for p in text.get_window_extent(renderer).get_points())
assert np.allclose(fig.get_size_inches()*25.4,[183,110])
stem='Figure4d_全量Target_正文紧凑重构'
for ext in ['png','pdf','svg','tiff']:
    kwargs={'dpi':600,'facecolor':'white'}
    if ext=='tiff': kwargs['pil_kwargs']={'compression':'tiff_lzw'}
    fig.savefig(OUT/f'{stem}.{ext}',**kwargs)
fig.savefig(ROOT/'workspace/preview.png',dpi=240,facecolor='white')
checks={'canvas_mm':[183,110],'targets':len(seen),'sdgs':12,'paired_cells':595,'country_metric_slots':1190,
        'observed_slots':len(values),'unobserved_slots':absent,'target_share_slots':170,'task_slots':1020,
        'palette':COLORS,'source_values_unchanged':True,'scale':[0,1],'normalization_checks':'passed',
        'target_labels_within_canvas':True,'minimum_label_pt':5.6,'template':'09_REL_005',
        'meaning':'Actual within-SDG Target shares and within-Target task shares; not correlations.'}
(ROOT/'workspace/data_layout_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False))
plt.close(fig)
