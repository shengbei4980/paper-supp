"""Curved, concentric adaptation of 20260516-环形热图.py.

The centre is a computed N/P/O/K/L profile map, never a hand-packed point cloud.
The heatmap uses exactly the validated 144 statistics from the preceding version.
"""
from pathlib import Path
import argparse,json,textwrap
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.neighbors import NearestNeighbors
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap,TwoSlopeNorm
from matplotlib.patches import Circle,Rectangle
import matplotlib.patheffects as pe
from 读取原始名称与Figure1a色带 import load_names,load_figure1a_palette,value_rgba

ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'数据';OUT=ROOT/'图'
PALETTE={'K01':'#287D8E','K02':'#679D7A','K03':'#C3A253',
         'K04':'#D38658','K05':'#AC627A','K06':'#8276A5'}
INK='#252B31';GRAY='#69737D'
SUBS=[f'K{k:02d}.{j}' for k,n in enumerate([2,2,3,3,3,3],1) for j in range(1,n+1)]
LS=[f'L{i:02d}' for i in range(1,10)]
plt.rcParams.update({'font.family':'Arial','font.sans-serif':['Arial','Helvetica','Liberation Sans'],
 'font.size':7,'text.color':INK,'axes.spines.top':False,'axes.spines.right':False,
 'axes.linewidth':.6,'xtick.direction':'out','ytick.direction':'out','legend.frameon':False,
 'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','hatch.linewidth':.28})

def fit_to_circle(Y,radius=9.05):
    start=(Y.min(axis=0)+Y.max(axis=0))/2
    fit=minimize(lambda c:np.square(Y-c).sum(axis=1).max(),start,method='Powell',
                 options={'xtol':1e-10,'ftol':1e-10,'maxiter':300})
    centre=fit.x;scale=radius/np.sqrt(np.square(Y-centre).sum(axis=1).max())
    return (Y-centre)*scale,centre,scale

def plot_advanced_forest_chart(model,alternate=False):
    full_names=load_names()
    stats=pd.read_csv(DATA/'144项子级干预完整比较.csv')
    maps=pd.read_csv(DATA/(model+'_坐标.csv'),dtype={'record_id':str})
    XY,translation,scale=fit_to_circle(maps[['x','y']].to_numpy())
    maps['plot_x']=XY[:,0];maps['plot_y']=XY[:,1]
    maps['color']=maps.primary_knowledge_task.map(PALETTE)
    def matrix(col):return stats.pivot(index='intervention',columns='subtype',values=col).loc[LS,SUBS].to_numpy()
    z_scores=matrix('difference_pp');sig_mask=matrix('significant');low_support=matrix('low_support')
    # Template inheritance: north origin, counterclockwise 270-degree sweep,
    # per-layer meshgrid and pcolormesh; resolve each cell into smooth sub-arcs.
    inner_radius=9.70;outer_radius=13.50;rmax=18.50
    r_edges=np.linspace(inner_radius,outer_radius,10);r_centres=(r_edges[:-1]+r_edges[1:])/2
    theta_edges=np.linspace(0,1.5*np.pi,17);theta_centres=(theta_edges[:-1]+theta_edges[1:])/2
    subdivisions=80
    theta_fine=np.linspace(0,1.5*np.pi,16*subdivisions+1)
    fig=plt.figure(figsize=(183/25.4,210/25.4),facecolor='white')
    ax_rect=[.045,.19,.91,.91*183/210]
    ax=fig.add_axes(ax_rect,projection='polar');ax.set_theta_zero_location('N');ax.set_theta_direction(1)
    ax.set_ylim(0,rmax);ax.set_axis_off()
    blue_cmap,red_cmap,zero_color,cmap=load_figure1a_palette()
    norm=TwoSlopeNorm(vmin=-90,vcenter=0,vmax=90)
    trace=[];texts=[]
    for i in range(9):
        ri=8-i
        R_ring,Theta_ring=np.meshgrid(r_edges[ri:ri+2],theta_fine)
        values=np.repeat(z_scores[i],subdivisions).reshape(-1,1)
        rgba=value_rgba(values,blue_cmap,red_cmap,zero_color)
        ax.pcolormesh(Theta_ring,R_ring,rgba,
            edgecolors='none',linewidth=0,antialiased=False,zorder=2)
        for j in range(16):
            th=theta_centres[j];rr=r_centres[ri];val=z_scores[i,j];status='value'
            if not np.isfinite(val):
                ax.text(th,rr,'×',fontsize=5.3,ha='center',va='center',color=GRAY,zorder=6);status='NA'
            elif low_support[i,j]:
                # Keep the true cell value unobscured; the sector label carries †.
                # No polar hatch patches: they produced unwanted crossing strokes.
                status='low_support'
            if sig_mask[i,j]:ax.plot(th,rr,'o',ms=1.65,mfc=INK,mec='white',mew=.25,zorder=7)
            trace.append({'subtype':SUBS[j],'intervention':LS[i],'rendered_value':val,
                          'marked':bool(sig_mask[i,j]),'status':status,
                          'rgba':','.join(f'{x:.12f}' for x in value_rgba(np.array([val]),blue_cmap,red_cmap,zero_color)[0])})
    # White separators follow true circular arcs, not 16-sided chords.
    for rr in r_edges:ax.plot(theta_fine,np.full_like(theta_fine,rr),color='white',lw=.35,zorder=5)
    for th in theta_edges:ax.plot([th,th],[inner_radius,outer_radius],color='white',lw=.40,zorder=5)
    for rr in [inner_radius,outer_radius]:ax.plot(theta_fine,np.full_like(theta_fine,rr),color=INK,lw=.45,zorder=6)
    for th in [0,1.5*np.pi]:ax.plot([th,th],[inner_radius,outer_radius],color=INK,lw=.45,zorder=6)
    # Same K colour on its entire nested subtype sector; no text inside the strip.
    start=0
    for k,count in enumerate([2,2,3,3,3,3],1):
        end=start+count;ts=np.linspace(theta_edges[start]+.005,theta_edges[end]-.005,321)
        ax.fill_between(ts,9.35,9.61,color=PALETTE[f'K{k:02d}'],alpha=.72,linewidth=0,zorder=3)
        if start:ax.plot([theta_edges[start]]*2,[inner_radius,outer_radius],color='white',lw=.95,zorder=6)
        start=end
    for j,sub in enumerate(SUBS):
        ang=(np.degrees(theta_centres[j])+90)%360;rotation=ang;ha='left'
        if 90<ang<270:rotation=ang-180;ha='right'
        suffix=' †' if sub=='K06.1' else (' ‡' if sub=='K06.3' else '')
        texts.append(ax.text(theta_centres[j],outer_radius+.22,f'{sub}{suffix}',
            rotation=rotation,rotation_mode='anchor',ha=ha,va='center',fontsize=6.0,
            weight='bold' if sub.startswith('K05') else 'normal'))
    cart=fig.add_axes(ax_rect,frameon=False,xlim=(-rmax,rmax),ylim=(-rmax,rmax))
    cart.set_aspect('equal');cart.axis('off')
    for parent,color in PALETTE.items():
        rows=maps.primary_knowledge_task.eq(parent)
        cart.scatter(maps.loc[rows,'plot_x'],maps.loc[rows,'plot_y'],s=.50,c=color,
                     alpha=.75,linewidths=0,zorder=2,rasterized=False)
    # Six essential group labels, no record counts, child captions or packing labels.
    # Each anchor is computed from a dense observed neighbourhood of its own class.
    label_data=[];occupied=[]
    for parent in PALETTE:
        q=maps[maps.primary_knowledge_task.eq(parent)]
        coords=q[['plot_x','plot_y']].to_numpy()
        nn=NearestNeighbors(n_neighbors=min(35,len(coords))).fit(coords)
        dist,_=nn.kneighbors(coords)
        # Prefer dense areas away from the outer arc, then avoid previous labels.
        scores=dist.mean(axis=1)+.12*np.maximum(0,np.linalg.norm(coords,axis=1)-7.5)
        for ii in np.argsort(scores):
            x,y=coords[ii];yy=y+.30
            if all(np.hypot(x-px,yy-py)>1.2 for px,py in occupied):break
        occupied.append((x,yy));label_data.append({'parent':parent,'x':float(x),'y':float(yy),
                                                  'anchor_record_id':str(q.iloc[ii].record_id)})
        texts.append(cart.text(x,yy,parent,fontsize=7.2,ha='center',va='center',color=INK,
            path_effects=[pe.withStroke(linewidth=2.1,foreground='white')],zorder=4))
    cart.text(.65,14.02,'Intervention layers',fontsize=6.9,weight='bold')
    for i,l in enumerate(LS):
        yy=r_centres[8-i]
        cart.plot([0,.48],[yy,yy],color=GRAY,lw=.35,ls=':',zorder=7)
        texts.append(cart.text(.65,yy,f'{l}  {full_names[l]}',fontsize=5.3,va='center'))
    cart.text(8.75,9.00,'Knowledge task',fontsize=7.3,weight='bold')
    for i,(parent,color) in enumerate(PALETTE.items()):
        yy=8.18-i*1.04
        cart.add_patch(Rectangle((8.75,yy-.16),.30,.30,facecolor=color,edgecolor='none'))
        texts.append(cart.text(9.2,yy,parent,fontsize=5.6,va='top',weight='bold'))
        wrapped=textwrap.fill(full_names[parent],width=32,break_long_words=False,break_on_hyphens=False)
        texts.append(cart.text(10.3,yy,wrapped,fontsize=5.6,va='top',linespacing=1.08))
    # Annotation located in opening; centre remains a continuous data-based map.
    fig.text(.025,.975,'d',fontsize=12,weight='bold')
    cax=fig.add_axes([.20,.110,.60,.0105])
    cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),cax=cax,orientation='horizontal',ticks=[-90,-60,-30,0,30,60,90])
    cb.outline.set_linewidth(.45);cb.ax.tick_params(labelsize=6,length=2,width=.45,pad=2)
    cb.set_label('Conditional intervention share: NSF − NSFC (percentage points)',fontsize=6.8,labelpad=4)
    fig.text(.20,.126,'NSFC higher',fontsize=6,color='#8B0000');fig.text(.80,.126,'NSF higher',fontsize=6,color='#003366',ha='right')
    fig.text(.07,.048,'● 95% bootstrap interval excludes zero; BH q < 0.05; both effective sample sizes ≥ 10.',fontsize=5.5)
    fig.text(.07,.030,'† Low support (K06.1: NSF n = 5; NSFC n = 1).  ‡ ×: undefined comparison (no NSFC K06.3 records).',fontsize=5.5)
    fig.text(.07,.012,'Centre: 11,753 projects; descriptive t-SNE of coded profiles, not a test of country differences.',fontsize=5.3,color=GRAY)
    fig.canvas.draw();renderer=fig.canvas.get_renderer();fb=fig.bbox
    clipped=[]
    for t in texts:
        b=t.get_window_extent(renderer)
        if b.x0<fb.x0 or b.x1>fb.x1 or b.y0<fb.y0 or b.y1>fb.y1:clipped.append(t.get_text())
    assert not clipped,clipped
    # Fine arc discretization has <0.000023 plot-unit radial chord error.
    chord_error=outer_radius*(1-np.cos((theta_edges[1]-theta_edges[0])/subdivisions/2))
    report={'selected_layout':model,'size_mm':[183,210],'points':len(maps),
      'group_palette':PALETTE,'centre_label_count':len(label_data),'ring_cells':144,
      'angular_subdivisions_per_cell':subdivisions,'maximum_arc_chord_error':float(chord_error),
      'concentric_radii':{'point_max':float(np.linalg.norm(XY,axis=1).max()),'K_band_inner':9.35,
      'K_band_outer':9.61,'heatmap_inner':inner_radius,'heatmap_outer':outer_radius},
      'uniform_coordinate_transform':{'translation':translation.tolist(),'scale':float(scale)},
      'text_outside_canvas':clipped,'artificial_jitter':False,'hand_packed_clusters':False}
    report.update({'low_support_rendering':'sector dagger only; no hatch or extra strokes',
      'hatch_overlay_count':0,'legend_full_names':full_names,'palette_source':'Figure1a original two 3-stop maps'})
    if alternate:
        stem=OUT/'布局比较'/('完整图_'+model)
        fig.savefig(str(stem)+'.png',dpi=300)
    else:
        maps.to_csv(DATA/'最终中心点位与颜色.csv',index=False,encoding='utf-8-sig')
        pd.DataFrame(trace).to_csv(DATA/'最终圆环单元追溯.csv',index=False,encoding='utf-8-sig')
        pd.DataFrame(label_data).to_csv(DATA/'中心必要标签.csv',index=False,encoding='utf-8-sig')
        (ROOT/'说明/最终绘图核查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        stem=OUT/'Figure2d_六类任务色系与子级结构'
        fig.savefig(str(stem)+'.pdf')
        fig.savefig(str(stem)+'.svg')
        fig.savefig(str(stem)+'.png',dpi=600)
        fig.savefig(OUT/'Figure2d_预览.png',dpi=300)
    plt.close(fig);print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--model',default='I_taskTSNE80')
    parser.add_argument('--alternate',action='store_true');args=parser.parse_args()
    plot_advanced_forest_chart(args.model,args.alternate)
