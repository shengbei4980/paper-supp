"""Compact revision: full paired triangles, no column gutters, full-height lists.
Run directly; uses the already validated paired dataset without recomputing estimates.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
from matplotlib.colors import LinearSegmentedColormap

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'single_frame_left_right_version'
OUT.mkdir(exist_ok=True)
SOURCE=ROOT/'数据/paired_target_metrics.csv'
df=pd.read_csv(SOURCE,dtype={'target':str})
assert len(df)==595 and df.target.nunique()==85 and not df.duplicated(['target','metric']).any()
METRICS=['Share']+[f'K{i:02}' for i in range(1,7)]
COLORS={'nsf':'#3775BA','nsfc':'#B64342'}
CMAPS={c:LinearSegmentedColormap.from_list(c,['white',v],N=1024) for c,v in COLORS.items()}
lookup=df.set_index(['target','metric'])
def key(t):
    a,b=t.split('.')
    return int(a),(0,int(b)) if b.isdigit() else (1,b)
targets=sorted(df.target.unique(),key=key)
plt.rcParams.update({'font.family':'Arial','font.size':6,'pdf.fonttype':42,'svg.fonttype':'none','text.color':'#20262C'})
fig=plt.figure(figsize=(183/25.4,110/25.4),facecolor='white')
ax=fig.add_axes([0,0,1,1]); ax.set(xlim=(0,183),ylim=(110,0)); ax.axis('off')
ax.text(3,4.3,'d',fontsize=10,fontweight='bold',va='center')
ax.text(10,4.3,'Target carriers and knowledge-task profiles',fontsize=9,fontweight='bold',va='center')
ax.text(177,4.3,'85 Targets · 12 SDGs',fontsize=6,ha='right',va='center',color='#56616B')

ax.add_patch(Rectangle((3,8.5),177,91.7,fill=False,edgecolor='black',lw=.7,zorder=6))
ax.plot([91.5,91.5],[8.5,100.2],color='#D2D6DA',lw=.4,zorder=6)
texts=[]; seen=[]; absent=0; marks=[]; intervals=[]
for base,sdgs in [(3,[2,3,6,7,9,10]),(91.5,[11,12,13,15,16,17])]:
    ax.text(base+1.2,11,'SDG',fontsize=6,fontweight='bold',va='center')
    ax.text(base+8.4,11,'Target',fontsize=6,fontweight='bold',va='center')
    cell_width=9.85
    starts=[base+18+i*cell_width for i in range(7)]
    for x,m in zip(starts,METRICS):
        ax.text(x+cell_width/2,11,m,ha='center',va='center',fontsize=6.2,fontweight='bold')
    n=sum(int(t.split('.')[0]) in sdgs for t in targets)
    row_height=86/n
    y=13.2
    group_edges=[]
    for gi,sdg in enumerate(sdgs):
        group=[t for t in targets if t.startswith(str(sdg)+'.')]
        if gi: group_edges.append(y)
        ax.text(base+1.2,y+row_height/2,str(sdg),fontsize=6.1,fontweight='bold',va='center')
        for t in group:
            label=ax.text(base+8.4,y+row_height/2,t,fontsize=5.5,va='center')
            texts.append(label); seen.append(t)
            intervals.append((base,y,y+row_height))
            for x,m in zip(starts,METRICS):
                r=lookup.loc[(t,m)]
                for ci,c in enumerate(COLORS):
                    value=r[f'value_{c}']; missing=not bool(r[f'observed_{c}']) or pd.isna(value)
                    if not missing: assert 0<=value<=1.000001
                    vertices=([(x,y),(x+cell_width,y),(x,y+row_height)] if ci==0 else
                              [(x+cell_width,y),(x+cell_width,y+row_height),(x,y+row_height)])
                    ax.add_patch(Polygon(vertices,closed=True,facecolor='#E6E8EB' if missing else CMAPS[c](value),edgecolor='none'))
                    if missing:
                        cx=x+cell_width*(1/3 if ci==0 else 2/3)
                        cy=y+row_height*(1/3 if ci==0 else 2/3)
                        ax.plot([cx-.45,cx+.45],[cy]*2,color='#737980',lw=.4)
                        absent+=1
                    marks.append((t,m,c,None if missing else float(value)))
            y+=row_height
    assert np.isclose(y,99.2)
    # Hairline grid only: no blank space between metric columns or Target rows.
    for x in starts+[starts[-1]+cell_width]:
        ax.plot([x,x],[13.2,99.2],color='#D2D6DA',lw=.18,zorder=4)
    for yy in np.linspace(13.2,99.2,n+1):
        ax.plot([starts[0],starts[-1]+cell_width],[yy]*2,color='#D2D6DA',lw=.18,zorder=4)
    for yy in group_edges:
        ax.plot([base+1,base+86.95],[yy]*2,color='#AEB6BF',lw=.4,zorder=5)
    ax.plot([starts[1],starts[1]],[13.2,99.2],color='#939DA7',lw=.45,zorder=5)
# Country color scales share a horizontal row and the same 0-100% mapping.
legend_labels=[]; legend_regions=[]
legend_labels.append(ax.text(3,103.5,'Share (%)',fontsize=5.8,va='center'))
gradient=np.linspace(0,1,1024).reshape(1,-1)
for c,start in [('nsf',22),('nsfc',82)]:
    legend_labels.append(ax.text(start-2,103.5,c.upper(),ha='right',va='center',fontsize=5.8,color=COLORS[c]))
    bar=ax.imshow(gradient,extent=(start,start+48,104.2,102.8),cmap=CMAPS[c],vmin=0,vmax=1,aspect='auto')
    legend_regions.append(bar)
    for value in [0,25,50,75,100]:
        legend_labels.append(ax.text(start+48*value/100,106.1,str(value),fontsize=5.5,ha='center',va='center'))
legend_labels.append(ax.text(135,102.3,'Upper left: NSF · Lower right: NSFC',fontsize=5.3,va='center'))
legend_labels.append(ax.text(135,104.7,'Gray / dash: unobserved',fontsize=5.5,va='center'))
legend_labels.append(ax.text(135,106.9,'White: observed zero',fontsize=5.5,va='center'))
ax.text(3,108.3,'Share: within-SDG Target fraction. K01–K06: within-Target task fractions. Full labels and intervals: accompanying data.',fontsize=5.5,va='center',color='#56616B')

assert len(seen)==len(set(seen))==85 and set(seen)==set(targets)
assert len(marks)==1190 and absent==154
assert np.allclose(fig.get_size_inches()*25.4,[183,110])
fig.canvas.draw(); renderer=fig.canvas.get_renderer()
assert all('†' not in t.get_text() for t in ax.texts)
legend_bounds=[t.get_window_extent(renderer) for t in legend_labels]
assert all(fig.bbox.contains(*p) for b in legend_bounds for p in b.get_points())
assert all(not a.overlaps(b) for i,a in enumerate(legend_bounds) for b in legend_bounds[i+1:]),'Legend labels overlap'
assert legend_regions[0].get_extent()[2:]==legend_regions[1].get_extent()[2:]
assert legend_regions[0].get_extent()[1]<legend_regions[1].get_extent()[0]
for label in texts:
    bounds=label.get_window_extent(renderer)
    assert all(fig.bbox.contains(*p) for p in bounds.get_points())
for offset,n in [(0,40),(40,45)]:
    boxes=[t.get_window_extent(renderer) for t in texts[offset:offset+n]]
    assert all(boxes[i].y0>=boxes[i+1].y1 for i in range(n-1)), 'Target labels overlap'
    frame_left=ax.transData.transform((21 if offset==0 else 109.5,13.2))[0]
    assert all(box.x1<frame_left for box in boxes), 'Target label enters color frame'
stem='Figure4d_full_Target_single_frame_left_right_compact_full_width_without_a59d9b9a'
for ext in ['png','pdf','svg','tiff']:
    kwargs={'dpi':600,'facecolor':'white'}
    if ext=='tiff': kwargs['pil_kwargs']={'compression':'tiff_lzw'}
    fig.savefig(OUT/f'{stem}.{ext}',**kwargs)
fig.savefig(OUT/f'{stem}_preview.png',dpi=240,facecolor='white')
report={'canvas_mm':[183,110],'targets':85,'left_targets':40,'right_targets':45,'country_metric_slots':len(marks),
        'missing_slots':absent,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'palette':COLORS,'row_height_mm':{'left':86/40,'right':86/45},'cell_width_mm':9.85,
        'metric_column_gap_mm':0,'target_font_pt':5.5,'target_labels_overlap':False,
        'outer_frames':1,'target_labels_inside_frame':True,'dagger_marks_removed':True,'legend_arrangement':'left NSF / right NSFC',
        'encoding':'equal-area upper-left NSF / lower-right NSFC triangles; linear 0-100% shade',
        'stats_recomputed':False,'all_values_from_validated_source':True}
(OUT/f'{stem}_核查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
