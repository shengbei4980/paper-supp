"""Full-location task contribution departures; reproduce from frozen allocations.

F = domestic overall share; T = domestic task share; departure = T - F (pp).
All 478 locations and 2,868 location-task cells are retained, including zeros.
Lines join categorical tasks; no temporal, causal or significance inference.
"""
from pathlib import Path
import hashlib
import json
import re
import textwrap
import platform
import argparse

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LogNorm, to_hex
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

ROOT = Path(__file__).resolve().parents[1]
DATA, FIG, QA = ROOT/'data', ROOT/'figures', ROOT/'audit'
INPUT = DATA/'input_snapshots'
TASKS = [f'K{i:02d}' for i in range(1,7)]
LABELS = pd.read_csv(INPUT/'knowledge_task_labels.csv').set_index('task')
assert LABELS.index.is_unique and set(LABELS.index)==set(TASKS)
NAMES = LABELS.loc[TASKS,'name_en'].tolist()
CN_NAMES = LABELS.loc[TASKS,'name_zh'].tolist()
PREFIX = 'Figure3d_all_location_task_contribution_deviation_profiles'
KEYS = ['agency','unit_id']
NORM = LogNorm(vmin=.001, vmax=25, clip=True)
BACKGROUND_GREY = '#CDD1D5'
Y_LIM = (-5.6,32)
Y_TICKS = [-5,-2,-1,-.5,0,.5,1,2,5,10,20]


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def gini(values):
    x = np.sort(np.asarray(values, dtype=float))
    assert x.min() >= 0 and x.sum() > 0
    return float(2*np.dot(np.arange(1,len(x)+1),x)/(len(x)*x.sum())-(len(x)+1)/len(x))


def build():
    e = pd.read_csv(INPUT/'project_level_target_task_allocations.csv', dtype={'record_id':str})
    assert not e.duplicated(KEYS+['record_id','sdg']).any()
    assert e.supply.gt(0).all() and set(e.task)==set(TASKS) and e.sdg.nunique()==12
    assert np.allclose(e.supply, e.city_weight/e.sdg_count)
    # Summing conserved allocations across SDGs recovers fractional family supply.
    mass = e.groupby(KEYS+['task']).supply.sum().unstack('task', fill_value=0)
    mass = mass.reindex(columns=TASKS, fill_value=0)
    support = e.groupby(KEYS+['task']).project_family_id.nunique().unstack('task',fill_value=0)
    support = support.reindex(index=mass.index,columns=TASKS,fill_value=0)
    units = e.groupby(KEYS).agg(unit_name=('unit_name','first'), unit_type=('unit_type','first'),
                              family_n=('project_family_id','nunique'))
    units['supply'] = mass.sum(axis=1)
    units['F_pct'] = 100*units.supply/units.groupby(level='agency').supply.transform('sum')
    units['overall_rank'] = units.groupby(level='agency').supply.rank(method='first',ascending=False).astype(int)
    states = pd.read_csv(INPUT/'us_county_mapping.csv', dtype={'GEOID':str})
    states = states.assign(unit_id='US_'+states.GEOID)[['unit_id','institution_region']].drop_duplicates()
    assert not states.unit_id.duplicated().any()
    state_map = states.set_index('unit_id').institution_region
    units['state'] = units.index.get_level_values('unit_id').map(state_map).fillna('')
    units['short_name'] = units.unit_name.str.replace(' County','',regex=False)
    us = units.index.get_level_values('agency')=='NSF'
    units.loc[us,'short_name'] += ', '+units.loc[us,'state']
    units.loc[units.unit_name.eq('District of Columbia'),'short_name'] = 'District of Columbia'
    source = (INPUT/'figure1a_sdg_target_ring.py').read_text(encoding='utf-8-sig')
    palette = {key:re.search(r'^'+key+r'\s*=\s*"(#[0-9A-Fa-f]{6})"',source,re.M).group(1)
               for key in ['NSF_DARK','NSF_MID','NSFC_DARK','NSFC_MID']}
    blue_light = re.search(r'"nsf_target",\s*\["(#[0-9A-Fa-f]{6})"',source).group(1)
    red_light = re.search(r'"nsfc_target",\s*\["(#[0-9A-Fa-f]{6})"',source).group(1)
    palette['NSF_LIGHT'],palette['NSFC_LIGHT'] = blue_light,red_light
    cmaps = {a:LinearSegmentedColormap.from_list(a,[palette[a+'_LIGHT'],palette[a+'_MID'],palette[a+'_DARK']])
             for a in ['NSF','NSFC']}
    records, concentration = [], []
    for agency in ['NSF','NSFC']:
        m = mass.loc[agency]
        g = units.loc[agency]
        national = m.sum()
        T = 100*m/national
        delta = T.sub(g.F_pct,axis=0)
        leaders = {k:delta[k].idxmax() for k in TASKS}
        selected = set(g[g.overall_rank.le(5)].index)|set(leaders.values())
        concentration.append(dict(agency=agency,category='Overall',gini=gini(g.supply),
                                  locations=len(g),allocated_supply=float(g.supply.sum())))
        for k in TASKS:
            concentration.append(dict(agency=agency,category=k,gini=gini(m[k]),
                                      locations=len(g),allocated_supply=float(national[k])))
        for uid,row in g.iterrows():
            peak = delta.loc[uid].idxmax()
            # Only annotation content avoids sparse K06 dominance; every value stays plotted.
            label_task = delta.loc[uid,TASKS[:5]].idxmax()
            if uid==leaders['K06'] and uid not in set(leaders[k] for k in TASKS[:5]):
                label_task='K06'
            for k in TASKS:
                records.append(dict(agency=agency,unit_id=uid,unit_name=row.unit_name,
                    unit_type=row.unit_type,state=row.state,short_name=row.short_name,task=k,
                    location_supply=row.supply,national_supply=float(g.supply.sum()),
                    task_supply=float(m.loc[uid,k]),national_task_supply=float(national[k]),
                    overall_share_pct=row.F_pct,task_share_pct=float(T.loc[uid,k]),
                    departure_pp=float(delta.loc[uid,k]),local_task_share_pct=float(100*m.loc[uid,k]/row.supply),
                    national_task_mix_pct=float(100*national[k]/national.sum()),
                    family_n=int(row.family_n),task_family_n=int(support.loc[(agency,uid),k]),
                    overall_rank=int(row.overall_rank),highlight=uid in selected,
                    task_leader=leaders[k]==uid,peak_task=peak,peak_departure_pp=float(delta.loc[uid,peak]),
                    label_task=label_task,label_departure_pp=float(delta.loc[uid,label_task]),
                    label_task_name=LABELS.loc[label_task,'name_en'],
                    color=to_hex(cmaps[agency](NORM(row.F_pct))) if uid in selected else BACKGROUND_GREY))
    full = pd.DataFrame(records)
    conc = pd.DataFrame(concentration)
    assert len(full)==2868 and len(units)==478
    assert full.groupby('agency').unit_id.nunique().to_dict()=={'NSF':352,'NSFC':126}
    assert np.allclose(units.groupby(level='agency').supply.sum(),[5000,5546])
    assert int(full.task_supply.eq(0).sum())==1425
    assert np.allclose(full.groupby(['agency','task']).task_share_pct.sum(),100)
    assert np.allclose(full.groupby(['agency','task']).departure_pp.sum(),0,atol=1e-10)
    weighted = full.assign(w=full.departure_pp*full.national_task_mix_pct/100).groupby(KEYS).w.sum()
    assert np.allclose(weighted,0,atol=1e-10)
    assert np.allclose(full.task_share_pct,full.overall_share_pct*full.local_task_share_pct/full.national_task_mix_pct)
    assert np.isfinite(full.select_dtypes('number').to_numpy()).all()
    assert full.departure_pp.between(*Y_LIM).all()
    full.to_csv(DATA/'all_locations_task_contributions_and_deviations.csv',index=False,encoding='utf-8-sig')
    units.reset_index().to_csv(DATA/'all_locations_overall_supply.csv',index=False,encoding='utf-8-sig')
    conc.to_csv(DATA/'all_locations_concentration.csv',index=False,encoding='utf-8-sig')
    full[full.task_leader].to_csv(DATA/'six_tasks_locations_with_largest_positive_deviation.csv',index=False,encoding='utf-8-sig')
    full[full.highlight].to_csv(DATA/'annotated_locations_full_contribution_profiles.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame({'task':TASKS,'name_en':NAMES,'name_zh':CN_NAMES}).to_csv(DATA/'knowledge_task_labels.csv',index=False,encoding='utf-8-sig')
    exact = full.pivot(index=KEYS,columns='task',values='departure_pp').round(12).reset_index()
    exact.groupby(['agency']+TASKS,dropna=False).agg(location_n=('unit_id','size'),
        unit_ids=('unit_id',lambda x:';'.join(x))).query('location_n > 1').to_csv(DATA/'identical_curve_records.csv',index=False,encoding='utf-8-sig')
    dump(DATA/'Figure1a_color_scale_parameters.json',dict(colors=palette,norm='LogNorm',vmin=.001,vmax=25,
         variable='overall national supply share (%) for highlighted locations only',alpha=1.0,
         other_locations_color=BACKGROUND_GREY))
    dump(QA/'input_snapshot_inventory.json',[dict(file=p.name,bytes=p.stat().st_size,
         sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(INPUT.iterdir()) if p.is_file()])
    return full,conc,palette,cmaps


def style():
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
        'font.size':7,'axes.labelsize':7,'xtick.labelsize':6.5,'ytick.labelsize':6,
        'axes.linewidth':.75,'axes.edgecolor':'black','text.color':'#202830',
        'axes.labelcolor':'#202830','svg.fonttype':'none','pdf.fonttype':42,
        'legend.frameon':False,'savefig.facecolor':'white'})


def panel(fig, bbox, agency, full, conc, palette, cmap, font_scale=1):
    ax = fig.add_axes(bbox)
    z = full[full.agency.eq(agency)]
    dark = palette[agency+'_DARK']
    ax.set_yscale('asinh',linear_width=.5)
    ax.set_ylim(*Y_LIM); ax.set_xlim(-.25,8.7)
    ax.yaxis.set_major_locator(FixedLocator(Y_TICKS))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y,pos:f'{y:g}'))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_xticks(range(6),['K01','K02','K03','K04','K05','K06*'])
    ax.tick_params(length=2.8,width=.7,labelsize=6.2*font_scale)
    for spine in ax.spines.values():
        spine.set_visible(True);spine.set_color('black');spine.set_linewidth(.75)
    ax.set_axisbelow(True)
    for y in Y_TICKS:
        ax.plot([-.25,5.25],[y,y],color='#E1E4E7',lw=.45,zorder=0)
    for x in range(6):
        ax.axvline(x,color='#E7E9EB',lw=.4,zorder=0)
    ax.axvspan(4.5,5.25,color='#F4F4F4',zorder=-1)
    ax.plot([-.25,5.25],[0,0],color='black',lw=.8,zorder=1)
    ax.axvline(5.38,color='#D0D4D8',lw=.5,zorder=0)
    ax.text(5.65,28,'Selected locations',fontsize=6*font_scale,fontweight='bold',va='top')
    marker = 'o' if agency=='NSF' else 's'
    # Sort by highlight then F so larger profiles are foreground; retain every line.
    order = z.drop_duplicates('unit_id').sort_values(['highlight','overall_share_pct'])
    profiles=[]
    for r in order.itertuples():
        g=z[z.unit_id.eq(r.unit_id)].set_index('task').loc[TASKS]
        h=bool(r.highlight)
        line,=ax.plot(range(6),g.departure_pp,color=r.color,lw=.9 if h else .36,alpha=1,
                      zorder=4 if h else 2)
        line.set_gid('profile_'+r.unit_id)
        for j,t in enumerate(g.itertuples()):
            point,=ax.plot(j,t.departure_pp,marker=marker,ls='none',markersize=(2.4 if h else 1.35),
                markeredgewidth=.5 if h else .28,markeredgecolor=r.color,
                markerfacecolor=r.color if t.task_family_n>=10 else 'white',zorder=5 if h else 3)
            point.set_gid('cell_'+r.unit_id+'_'+TASKS[j])
        if h:
            profiles.append((r,g))
    # Endpoint labels have sorted vertical positions to avoid crossing each other.
    profiles.sort(key=lambda pair:float(pair[1].iloc[-1].departure_pp))
    label_positions=np.linspace(.045,.885,len(profiles))
    annotations=[]
    for (r,g),yf in zip(profiles,label_positions):
        short='\n'.join(textwrap.wrap(r.short_name,width=19))
        label=f'{short}\n{r.label_task}  {r.label_departure_pp:+.2f} pp'
        a=ax.annotate(label,xy=(5,float(g.iloc[-1].departure_pp)),xycoords='data',
            xytext=(.666,yf),textcoords='axes fraction',ha='left',va='center',
            fontsize=5.65*font_scale,color=dark,linespacing=1.1,
            arrowprops=dict(arrowstyle='-',color=r.color,lw=.55,connectionstyle='arc3,rad=0',relpos=(0,.5)),
            bbox=dict(facecolor='white',edgecolor='none',pad=.4),zorder=8)
        a.set_gid('location_label_'+r.unit_id)
        annotations.append(a)
    # A concise label at each task's maximum directly ties a value to its x position.
    for j,k in enumerate(TASKS):
        r=z[z.task.eq(k)&z.task_leader].iloc[0]
        ax.annotate(f'{r.departure_pp:+.2f}',(j,r.departure_pp),xytext=(0,7),
            textcoords='offset points',ha='left' if j==0 else 'center',va='bottom',fontsize=5.8*font_scale,
            fontweight='bold',color=dark,zorder=7,
            bbox=dict(facecolor='white',edgecolor='none',pad=.25))
    left,bottom,width,height=bbox
    title='United States · NSF' if agency=='NSF' else 'China · NSFC'
    subtitle='352 counties and equivalents · observed 2015–2025' if agency=='NSF' else '126 prefecture-level units · observed 2015–2023'
    fig.text(left,bottom+height+.079,title,color=dark,fontsize=9.3*font_scale,fontweight='bold')
    fig.text(left,bottom+height+.058,subtitle,fontsize=5.8*font_scale,color='#56616B')
    c=conc[conc.agency.eq(agency)].set_index('category')
    fig.text(left,bottom+height+.036,f'Task Gini  |  Overall {c.loc["Overall","gini"]:.3f}',fontsize=5.8*font_scale,color='#56616B')
    for j,k in enumerate(TASKS):
        xf=left+width*(j+.25)/8.95
        fig.text(xf,bottom+height+.010,f'{c.loc[k,"gini"]:.3f}',ha='center',fontsize=5.8*font_scale)
    ax.set_xlabel('Knowledge task',fontsize=6.8*font_scale)
    ax.xaxis.set_label_coords(.30,-.074)
    return ax,annotations,dict(agency=agency,profiles=len(order),cells=len(z),highlighted=len(profiles),
        zero_task_supply=int(z.task_supply.eq(0).sum()),y_axis='asinh',linear_width_pp=.5,ylim=Y_LIM)


def colorbar(fig, bbox, cmap, scale=1):
    cax=fig.add_axes(bbox)
    cb=fig.colorbar(plt.cm.ScalarMappable(norm=NORM,cmap=cmap),cax=cax,orientation='horizontal')
    cb.set_ticks([.001,.01,.1,1,10,25]); cb.set_ticklabels(['0.001','0.01','0.1','1','10','25'])
    cb.ax.xaxis.set_minor_locator(NullLocator()); cb.ax.tick_params(labelsize=5.5*scale,length=2,width=.5)
    cb.outline.set_linewidth(.5)
    cb.set_label('Highlighted: supply share (%) · log scale',fontsize=5.5*scale,labelpad=2)


def export(fig, stem, preview_only=False):
    fig.savefig(FIG/(stem+'_preview.png'),dpi=300)
    if not preview_only:
        fig.savefig(FIG/(stem+'.png'),dpi=600)
        fig.savefig(FIG/(stem+'.tiff'),dpi=600,pil_kwargs={'compression':'tiff_lzw'})
        fig.savefig(FIG/(stem+'.pdf'))
        fig.savefig(FIG/(stem+'.svg'))


def draw(full,conc,palette,cmaps,preview_only=False):
    style()
    fig=plt.figure(figsize=(7.2047244094,7.2834645669),facecolor='white')
    fig.text(.025,.965,'d',fontsize=12,fontweight='bold')
    fig.text(.085,.966,'Where locations contribute beyond their overall supply share',fontsize=9.0,fontweight='bold')
    fig.text(.085,.941,'Task contribution minus overall supply · all 478 locations · all 12 SDGs',fontsize=7,color='#56616B')
    axes=[];labels=[];reports=[]
    for a,left in [('NSF',.085),('NSFC',.555)]:
        ax,ann,report=panel(fig,[left,.325,.42,.50],a,full,conc,palette,cmaps[a])
        axes.append(ax);labels.extend(ann);reports.append(report)
        colorbar(fig,[left,.265,.31,.008],cmaps[a])
    axes[0].set_ylabel('Task share − overall share (percentage points)',labelpad=4)
    fig.text(.085,.220,'Zero = task contribution matches overall supply share. Shared asinh axes expand small departures.',fontsize=6.0)
    handles=[Line2D([0],[0],marker='o',color='#65727D',mfc='white',lw=0,ms=3,label='<10 task project families'),
             Line2D([0],[0],marker='o',color='#65727D',mfc='#65727D',lw=0,ms=3,label='≥10 task project families'),
             Line2D([0],[0],color=BACKGROUND_GREY,lw=1,label='Other locations (grey)')]
    fig.legend(handles=handles,loc='center left',bbox_to_anchor=(.075,.195),ncol=3,fontsize=6,handletextpad=.5,columnspacing=2)
    fig.text(.085,.172,'* K06: low national support (fractional totals: NSF 42; NSFC 20). No significance test is implied.',fontsize=6,color='#56616B')
    for j in range(3):
        for col in range(2):
            i=j+col*3
            txt=f'{TASKS[i]}  {NAMES[i]}'
            wrapped=textwrap.fill(txt,width=53,subsequent_indent='         ')
            fig.text(.085+col*.47,.143-j*.030,wrapped,fontsize=5.8,va='top',linespacing=1.1)
    fig.text(.085,.036,'Labels: overall top five + task leaders. Label values prioritize K01–K05; the K06-only leader is also shown.',fontsize=5.6,color='#56616B')
    fig.text(.085,.019,'All profiles retained; exact overlaps remain superimposed. Contributions pool SDGs and describe observed samples.',fontsize=5.6,color='#56616B')
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    bounds=[]
    for ax in axes:
        texts=[a for a in labels if a.axes is ax]
        boxes=[a.get_bbox_patch().get_window_extent(renderer) for a in texts]
        assert all(ax.bbox.contains(b.x0,b.y0) and ax.bbox.contains(b.x1,b.y1) for b in boxes), 'Endpoint label outside frame'
        assert not any(b.overlaps(c) for i,b in enumerate(boxes) for c in boxes[i+1:]), 'Endpoint labels overlap'
        bounds.append(dict(label_count=len(boxes),within_frame=True,overlap=False))
    export(fig,PREFIX,preview_only)
    plt.close(fig)
    if not preview_only:
        for agency in ['NSF','NSFC']:
            sf=plt.figure(figsize=(160/25.4,180/25.4),facecolor='white')
            sf.text(.11,.965,'Task contributions relative to overall supply',fontsize=12,fontweight='bold')
            ax,_,_=panel(sf,[.11,.255,.85,.59],agency,full,conc,palette,cmaps[agency],font_scale=1.15)
            ax.set_ylabel('Task share − overall share (percentage points)',fontsize=9)
            ax.xaxis.set_label_coords(.30,-.045)
            colorbar(sf,[.11,.195,.59,.01],cmaps[agency],scale=1.15)
            sf.text(.11,.142,'Grey: other locations · open: <10 task families · asinh width = 0.5 pp',fontsize=7)
            national_k06=42 if agency=='NSF' else 20
            sf.text(.11,.123,f'* K06: low national support ({national_k06} fractional projects). Descriptive departures; no significance test.',fontsize=6.5)
            for i in range(6):
                sf.text(.11,.097-i*.014,f'{TASKS[i]}  {NAMES[i]}',fontsize=6.5)
            export(sf,PREFIX+'_'+agency)
            plt.close(sf)
    dump(QA/'plot_and_data_check.json',dict(status='PASS',panels=reports,endpoint_labels=bounds,
        locations=478,cells=2868,zero_task_cells=int(full.task_supply.eq(0).sum()),
        rows_dropped=0,confidence_intervals='none; descriptive profiles',
        versions=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,matplotlib=matplotlib.__version__)))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--preview-only',action='store_true')
    args=parser.parse_args()
    for p in [DATA,FIG,QA]:p.mkdir(parents=True,exist_ok=True)
    full,conc,palette,cmaps=build()
    draw(full,conc,palette,cmaps,args.preview_only)
    print(f'PASS: {full.unit_id.nunique()} locations, {len(full)} task cells; figures at {FIG}')
