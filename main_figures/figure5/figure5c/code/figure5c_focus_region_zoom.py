"""Full 54-theme scatter with linked magnified, annotated high-deviation regions.
All estimates and intervals are reused from the verified fine-theme source table.
"""
from pathlib import Path
import json,textwrap
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm,to_hex
from matplotlib.patches import Rectangle,ConnectionPatch
from matplotlib.path import Path as PlotPath
from figure5c import DATA,OUT,QA,AGENCIES
from figure5c_continuous_color_scale_version import CMAP

STEM='Figure5c_全量散点_重点区域放大标注版'
K=8
NORM=TwoSlopeNorm(vmin=-8,vcenter=0,vmax=8)

def main():
    d=pd.read_csv(DATA/'observed_research_theme_estimates_108_items.csv')
    assert len(d)==108 and not d.duplicated(['agency','theme']).any()
    assert np.allclose(d.standardized_pct-d.observed_pct,d.delta_pp)
    for agency in AGENCIES:
        t=d[d.agency.eq(agency)]
        assert len(t)==54 and np.isclose(t.observed_pct.sum(),100) and np.isclose(t.standardized_pct.sum(),100)
    plt.rcParams.update({'font.family':'Arial','font.size':7,'axes.labelsize':7,
        'xtick.labelsize':6.5,'ytick.labelsize':6.5,'svg.fonttype':'none','pdf.fonttype':42,'axes.linewidth':.6})
    width_mm,height_mm=183,193
    fig=plt.figure(figsize=(width_mm/25.4,height_mm/25.4),dpi=300)
    fig.text(.024,.979,'c',fontweight='bold',fontsize=9,va='top')
    fig.text(.54,.978,'Research-content differences under national SDG challenge weights',
             ha='center',va='top',fontsize=8.8)
    details,regions=[],[]
    label_texts=[]
    for agency,left in zip(AGENCIES,[.105,.565]):
        t=d[d.agency.eq(agency)].copy()
        t['absolute_shift']=t.delta_pp.abs()
        selected=t.sort_values(['absolute_shift','theme'],ascending=[False,True]).head(K)
        fig.text(left+.2075,.936,agency,ha='center',fontweight='bold',fontsize=10)
        zoom=fig.add_axes([left,.422,.415,.471],facecolor='#F7F7F6')
        full=fig.add_axes([left,.105,.415,.261])
        x0,x1=selected.observed_pct.min(),selected.observed_pct.max()
        y0,y1=selected.standardized_pct.min(),selected.standardized_pct.max()
        px=max((x1-x0)*.12,.5);py=max((y1-y0)*.12,.5)
        x0=max(0,x0-px);x1=min(16,x1+px)
        y0=max(0,y0-py);y1=min(16,y1+py)
        inside=t[t.observed_pct.between(x0,x1)&t.standardized_pct.between(y0,y1)]
        selected_keys=set(selected.theme)
        for ax,rows,region in [(full,t,'full'),(zoom,inside,'zoom')]:
            ax.plot([0,16],[0,16],color='#AAAAAA',ls='--',lw=.65,zorder=0)
            for row in rows.itertuples():
                highlight=row.theme in selected_keys
                point=ax.scatter(row.observed_pct,row.standardized_pct,
                    s=26 if highlight else 12,marker='o',color=CMAP(NORM(row.delta_pp)),
                    alpha=1 if highlight else .60,edgecolor='#444444' if highlight else 'white',
                    linewidth=.35,zorder=3 if highlight else 2)
                point.set_gid(f'{region}_point_{agency}_{row.theme}')
        full.set(xlim=(0,16),ylim=(0,16),xticks=[0,4,8,12,16],yticks=[0,4,8,12,16])
        full.set_xlabel('Observed research share (%)',labelpad=4)
        if agency=='NSF': full.set_ylabel('Challenge-standardized share (%)',labelpad=4)
        full.tick_params(direction='out',length=2.4,width=.55,pad=3)
        full.spines[['top','right']].set_visible(False)
        roi=Rectangle((x0,y0),x1-x0,y1-y0,facecolor='#878787',alpha=.065,edgecolor='none',zorder=0)
        full.add_patch(roi)
        full.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,edgecolor='#9B9B9B',lw=.7,zorder=4))
        zoom.set(xlim=(x0,x1),ylim=(y0,y1),xticks=[],yticks=[])
        assert selected.observed_pct.between(x0,x1).all() and selected.standardized_pct.between(y0,y1).all()
        assert np.allclose(zoom.get_xlim(),[x0,x1]) and np.allclose(zoom.get_ylim(),[y0,y1])
        for spine in zoom.spines.values(): spine.set_color('#B3B3B3');spine.set_linewidth(.6)
        for x in [x0,x1]:
            fig.add_artist(ConnectionPatch(xyA=(x,y1),coordsA='data',axesA=full,
                xyB=(x,y0),coordsB='data',axesB=zoom,color='#B5B5B5',lw=.55,zorder=1.5))
        fig.canvas.draw();renderer=fig.canvas.get_renderer()
        bounds=zoom.get_window_extent(renderer)
        anchors=zoom.transData.transform(selected[['observed_pct','standardized_pct']].to_numpy())
        occupied=[];leader_paths=[]
        for row in selected.itertuples():
            fs=6.5+3.0*abs(row.delta_pp)/d.delta_pp.abs().max()
            label=textwrap.fill(row.full_theme_name,width=23,break_long_words=False,break_on_hyphens=False)
            probe=zoom.text(.5,.5,label,transform=zoom.transAxes,ha='center',va='center',
                            fontsize=fs,linespacing=1.06,color=CMAP(NORM(row.delta_pp)))
            source=zoom.transData.transform([row.observed_pct,row.standardized_pct])
            choices=[]
            for yy in np.linspace(.035,.965,28):
                for xx in np.linspace(.025,.975,25):
                    probe.set_position((xx,yy));box=probe.get_window_extent(renderer).expanded(1.035,1.10)
                    if box.x0<bounds.x0+3 or box.x1>bounds.x1-3 or box.y0<bounds.y0+3 or box.y1>bounds.y1-3: continue
                    if any(box.overlaps(other) for other in occupied): continue
                    if any(box.x0-5<ax<box.x1+5 and box.y0-5<ay<box.y1+5 for ax,ay in anchors): continue
                    target=zoom.transAxes.transform([xx,yy])
                    leader=PlotPath([source,target])
                    crossings=sum(leader.intersects_bbox(other,filled=False) for other in occupied)
                    crossings+=sum(path.intersects_bbox(box,filled=False) for path in leader_paths)
                    cost=float(((target-source)**2).sum())+crossings*4*bounds.width**2
                    choices.append((cost,xx,yy,box))
            assert choices, f'Cannot place full theme name: {row.full_theme_name}'
            _,xx,yy,box=min(choices,key=lambda v:v[0]);probe.remove();occupied.append(box)
            leader_paths.append(PlotPath([source,zoom.transAxes.transform([xx,yy])]))
            text=zoom.annotate(label,xy=(row.observed_pct,row.standardized_pct),xytext=(xx,yy),
                textcoords='axes fraction',ha='center',va='center',fontsize=fs,linespacing=1.06,
                color=CMAP(NORM(row.delta_pp)),
                bbox=dict(boxstyle='square,pad=.05',facecolor='#F7F7F6',edgecolor='none',alpha=.92),
                arrowprops=dict(arrowstyle='-',color=CMAP(NORM(row.delta_pp)),alpha=.65,lw=.55,
                                shrinkA=3,shrinkB=3),zorder=5)
            text.set_gid(f'focus_label_{agency}_{row.theme}');label_texts.append(text)
            details.append(dict(agency=agency,theme=row.theme,full_theme_name=row.full_theme_name,
                observed_pct=row.observed_pct,standardized_pct=row.standardized_pct,delta_pp=row.delta_pp,
                absolute_shift=abs(row.delta_pp),font_size_pt=fs,color=to_hex(CMAP(NORM(row.delta_pp))),
                label_x_axes=xx,label_y_axes=yy))
        regions.append(dict(agency=agency,x_min=x0,x_max=x1,y_min=y0,y_max=y1,
                            selected_labels=K,context_points=len(inside),full_points=len(t)))
        assert np.allclose([zoom.get_position().x0,zoom.get_position().x1],
                           [full.get_position().x0,full.get_position().x1])
    fig.text(.542,.393,'Magnified regions above · All 54 research themes below',ha='center',fontsize=7,
             bbox=dict(facecolor='white',edgecolor='none',pad=1.5))
    colorax=fig.add_axes([.26,.037,.53,.010])
    bar=fig.colorbar(plt.cm.ScalarMappable(norm=NORM,cmap=CMAP),cax=colorax,orientation='horizontal')
    bar.set_ticks([-8,-4,0,4,8]);bar.set_ticklabels(['−8','−4','0','+4','+8'])
    bar.outline.set_visible(False);bar.ax.tick_params(length=2,width=.5,pad=2,labelsize=6.5)
    bar.set_label('Standardized − observed research share (percentage points)',fontsize=7,labelpad=3)
    fig.text(.24,.042,'Decrease',ha='right',va='center',fontsize=7,color='#A73B3B')
    fig.text(.81,.042,'Increase',ha='left',va='center',fontsize=7,color='#285D96')
    fig.canvas.draw();renderer=fig.canvas.get_renderer()
    boxes=[t.get_bbox_patch().get_window_extent(renderer) for t in label_texts]
    assert not any(b.overlaps(other) for i,b in enumerate(boxes) for other in boxes[i+1:]), 'Label overlap'
    for text in fig.findobj(matplotlib.text.Text):
        if text.get_visible() and text.get_text():
            b=text.get_window_extent(renderer)
            assert b.x0>=-1 and b.y0>=-1 and b.x1<=fig.bbox.width+1 and b.y1<=fig.bbox.height+1,text.get_text()
    pd.DataFrame(details).to_csv(DATA/f'focus_region_{2*K}个完整主题标注.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(regions).to_csv(DATA/'focus_region_upper_lower_panel_extent_mapping.csv',index=False,encoding='utf-8-sig')
    fig.savefig(OUT/f'{STEM}.pdf');fig.savefig(OUT/f'{STEM}.svg')
    fig.savefig(OUT/f'{STEM}.png',dpi=600)
    fig.savefig(OUT/f'{STEM}.tiff',dpi=600,pil_kwargs={'compression':'tiff_lzw'})
    fig.savefig(OUT/f'{STEM}_preview.png',dpi=300);plt.close(fig)
    svg=ET.parse(OUT/f'{STEM}.svg');root=svg.getroot();ns='{http://www.w3.org/2000/svg}'
    ids=[e.get('id','') for e in root.iter()]
    assert sum(s.startswith('full_point_') for s in ids)==108
    assert sum(s.startswith('focus_label_') for s in ids)==2*K
    lookup={(r.agency,r.theme):r for r in d.itertuples()}
    for e in root.iter():
        eid=e.get('id','')
        if any(eid.startswith(s) for s in ['full_point_','zoom_point_','focus_label_']):
            _,agency,theme=eid.rsplit('_',2);row=lookup[(agency,theme)]
            title=ET.Element(ns+'title')
            title.text=f'{agency}: {row.full_theme_name}; observed {row.observed_pct:.3f}%; standardized {row.standardized_pct:.3f}%; shift {row.delta_pp:+.3f} pp'
            e.insert(0,title)
    ET.register_namespace('',ns[1:-1]);svg.write(OUT/f'{STEM}.svg',encoding='utf-8',xml_declaration=True)
    report=dict(size_mm=[width_mm,height_mm],all_points=108,focus_full_names=2*K,
        estimates_unchanged=True,point_coordinates_unchanged=True,roi_matches_zoom=True,
        selection=f'{K} largest absolute share shifts within each agency; display only',
        no_numeric_word_labels=True,no_task_codes=True,label_overlap=False,canvas_clipping=False,
        label_font_min_pt=min(r['font_size_pt'] for r in details),label_font_max_pt=max(r['font_size_pt'] for r in details))
    (QA/'focus_region_version_visual_assertions.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PASS: all 108 theme points retained; {2*K} full-name labels in linked magnified regions; true coordinates and unchanged estimates; no label overlap or clipping.')

if __name__=='__main__': main()
