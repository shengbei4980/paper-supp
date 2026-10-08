"""Single quantitative quadrant frame; exact coordinates and area-scaled markers.

Ellipses retain equal-link covariance orientation and expand to include every
stage point. They are descriptive coverage envelopes, not confidence regions.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.markers import MarkerStyle
from matplotlib.patches import Ellipse, Rectangle
from matplotlib.lines import Line2D
from sci_style import apply_journal_style

ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data';OUT=ROOT/'figures';NOTE=ROOT/'notes'
STAGES=['Need → pressure','Pressure → system','System → knowledge']
STAGE_LABELS=['Need → pressure','Pressure → system','System → task']
STYLES=['solid',(0,(5,3)),(0,(5,2,1,2))]
ELLIPSE_COLORS=['#287D63','#B88727','#8064A2']
# Quadrant fills encode the sign after balancing: cool blue above zero,
# warm red below zero. The reversal quadrants use distinct, softer tints.
QUADRANT_COLORS={'I':'#EEF4FA','II':'#E5EEF6','III':'#FBF0EF','IV':'#F8E9E9'}
BLUE='#347CAB';RED='#BC5353';GREY='#606972';AREA_PER_PERCENT=7.0;TOL=1e-10
LABELS={
 'N02→P04':('Disaster response →\nSpatial pressure',(-1.8,-2.55)),
 'N06→P04':('Ecological integrity →\nSpatial pressure',(-5.6,-1.3)),
 'N02→P01':('Disaster response →\nHazard shocks',(6.15,-1.2)),
 'P04→O02':('Spatial pressure →\nBuilt environment',(-7.0,-2.3)),
 'P01→O01':('Hazard shocks →\nPopulation & communities',(3.0,3.45)),
 'P01→O08':('Hazard shocks →\nGreen-blue ecosystems',(6.75,1.55)),
 'O07→K01':('Digital infrastructure →\nMeasurement & diagnosis',(-1.3,3.15)),
 'O06→K04':('Resource-circulation system →\nDesign & optimization',(1.8,2.0)),
 'O08→K02':('Green-blue ecosystems →\nMechanism analysis',(-5.5,1.0)),
}

def polygon_area(vertices):
    v=np.asarray(vertices);return abs(float(np.sum(v[:,0]*np.roll(v[:,1],-1)-v[:,1]*np.roll(v[:,0],-1))*.5))

def marker(stage_index):
    if stage_index==0:
        theta=np.linspace(0,2*np.pi,128,endpoint=False);verts=np.column_stack([np.cos(theta),np.sin(theta)])
    elif stage_index==1:verts=np.array([[0,1],[-1,-1],[1,-1]])
    else:verts=np.array([[-1,-1],[1,-1],[1,1],[-1,1]])
    path=MPath(np.vstack([verts,verts[0]]),[MPath.MOVETO]+[MPath.LINETO]*(len(verts)-1)+[MPath.CLOSEPOLY])
    ms=MarkerStyle(path);transformed=ms.get_path().transformed(ms.get_transform())
    return path,polygon_area(transformed.vertices[:-1])

def prepare():
    links=pd.read_csv(DATA/'Figure2b_all_link_shifts.csv',float_precision='round_trip',keep_default_na=False)
    flow=pd.read_csv(DATA/'original_2a_all_need_translation_flows.csv',float_precision='round_trip')
    summary=pd.read_csv(DATA/'Figure2b_stage_commonality_and_divergence.csv',float_precision='round_trip')
    links['x_observed_gap_pp']=100*(links.observed_nsf_share-links.observed_nsfc_share)
    links['y_balanced_gap_pp']=100*(links.balanced_nsf_share-links.balanced_nsfc_share)
    links['mean_balanced_share_percent']=50*(links.balanced_nsf_share+links.balanced_nsfc_share)
    x=links.x_observed_gap_pp;y=links.y_balanced_gap_pp
    links['quadrant']=np.select([(x>TOL)&(y>TOL),(x<-TOL)&(y>TOL),(x<-TOL)&(y<-TOL),(x>TOL)&(y<-TOL)],['I','II','III','IV'],default='axis')
    links['gap_change']=np.select([abs(y)<abs(x)-TOL,abs(y)>abs(x)+TOL],['smaller','larger'],default='equal')
    links['sign_flip']=x*y<0
    links['stage_index']=links.stage.map(dict(zip(STAGES,range(3))))
    links['colour']=np.where(y>TOL,BLUE,np.where(y<-TOL,RED,GREY))
    links['gid']=[f'link_{i}_{s}_{t}' for i,s,t in links[['stage_index','source','target']].itertuples(index=False,name=None)]
    links['geometric_area_pt2']=AREA_PER_PERCENT*links.mean_balanced_share_percent
    areas={i:marker(i)[1] for i in range(3)}
    links['marker_unit_area']=links.stage_index.map(areas)
    links['matplotlib_s']=links.geometric_area_pt2/links.marker_unit_area
    for agency in ['NSF','NSFC']:
        lookup=flow[flow.agency==agency].set_index(['stage','source','target']).fractional_project_n
        links[agency+'_observed_fractional_projects']=[float(lookup.get(tuple(k),0)) for k in links[['stage','source','target']].itertuples(index=False,name=None)]
    records=[];ellipses=[];selected=[]
    for i,stage in enumerate(STAGES):
        sub=links[links.stage==stage]
        obs=summary[(summary.scope==stage)&(summary.specification=='Observed')].iloc[0]
        bal=summary[(summary.scope==stage)&(summary.specification=='Target–year balanced')].iloc[0]
        records.append(dict(stage=stage,stage_index=i,links=len(sub),smaller=int((sub.gap_change=='smaller').sum()),larger=int((sub.gap_change=='larger').sum()),flips=int(sub.sign_flip.sum()),observed_contribution=obs.absolute_contribution,balanced_contribution=bal.absolute_contribution,retained_percent=100*bal.retained_fraction,nsf_covered=int((sub.observed_nsf_share>0).sum()),nsfc_covered=int((sub.observed_nsfc_share>0).sum()),both_covered=int(((sub.observed_nsf_share>0)&(sub.observed_nsfc_share>0)).sum()),**{f'quadrant_{q}':int((sub.quadrant==q).sum()) for q in ['I','II','III','IV','axis']}))
        points=sub[['x_observed_gap_pp','y_balanced_gap_pp']].to_numpy();mu=points.mean(axis=0)
        cov=(points-mu).T@(points-mu)/len(points);eigen,vec=np.linalg.eigh(cov);idx=np.argsort(eigen)[::-1];eigen=eigen[idx];vec=vec[:,idx]
        assert np.all(eigen>0),('Degenerate covariance: do not inflate ellipse',stage)
        angle=np.degrees(np.arctan2(vec[1,0],vec[0,0]))
        mahal_sq=np.einsum('ij,jk,ik->i',points-mu,np.linalg.inv(cov),points-mu)
        scale=float(np.sqrt(mahal_sq.max()))*(1+1e-10)
        normalized=mahal_sq/scale**2
        euclidean=np.linalg.norm(points-mu,axis=1)
        links.loc[sub.index,'ellipse_distance_squared']=normalized
        links.loc[sub.index,'inside_stage_ellipse']=normalized<=1+1e-12
        assert np.all(normalized<=1+1e-12)
        ellipses.append(dict(stage=stage,stage_index=i,center_x=mu[0],center_y=mu[1],cov_xx=cov[0,0],cov_xy=cov[0,1],cov_yy=cov[1,1],width=2*scale*np.sqrt(eigen[0]),height=2*scale*np.sqrt(eigen[1]),angle_degrees=angle,scale=scale,denominator=len(sub),covered_count=int((normalized<=1+1e-12).sum()),max_normalized_distance_squared=float(normalized.max()),boundary_link=sub.iloc[int(np.argmax(mahal_sq))].pair_code,nearest_euclidean_link=sub.iloc[int(np.argmin(euclidean))].pair_code,farthest_euclidean_link=sub.iloc[int(np.argmax(euclidean))].pair_code))
        residual=sub.sort_values(['balanced_absolute_contribution','source','target'],ascending=[False,True,True]).head(2)
        mass=sub.sort_values(['mean_balanced_share_percent','source','target'],ascending=[False,True,True]).head(1)
        chosen=pd.concat([residual,mass]).drop_duplicates('gid')
        for _,r in chosen.iterrows():
            reason=[]
            if r.gid in residual.gid.values:reason.append('top 2 balanced JSD contribution within stage')
            if r.gid in mass.gid.values:reason.append('largest mean balanced share within stage')
            selected.append(dict(gid=r.gid,pair_code=r.pair_code,stage=stage,selection='; '.join(reason)))
    links['labelled']=links.gid.isin([r['gid'] for r in selected])
    for name,frame in [('all_link_coordinates_and_shares.csv',links),('stage_and_quadrant_statistics.csv',pd.DataFrame(records)),('stage_ellipse_parameters.csv',pd.DataFrame(ellipses)),('key_label_selection_rationale.csv',pd.DataFrame(selected))]:
        frame.to_csv(DATA/name,index=False,encoding='utf-8-sig')
    return links,pd.DataFrame(records),pd.DataFrame(ellipses)

def draw():
    apply_journal_style(base_font_size=6.7,axes_line_width=.6)
    plt.rcParams.update({'path.simplify':False,'xtick.labelsize':6.4,'ytick.labelsize':6.4})
    links,stats,ellipses=prepare()
    fig=plt.figure(figsize=(180/25.4,120/25.4))
    ax=fig.add_axes([.12,.30,.84,(180*.84*8.4/18.5)/120])
    ax.set(xlim=(-9.25,9.25),ylim=(-4.2,4.2),xticks=np.arange(-8,9,2),yticks=np.arange(-4,5,2));ax.set_aspect('equal',adjustable='box')
    fig.text(.035,.968,'b',weight='bold',fontsize=10)
    fig.text(.12,.968,'Connection differences before and after balancing',fontsize=9.3,weight='bold')
    fig.text(.12,.939,'311 links  |  NSF: 6,207 project records; NSFC: 5,546  |  Target–year balancing',fontsize=6.6,color=GREY)
    for quadrant,origin in [('I',(0,0)),('II',(-9.25,0)),('III',(-9.25,-4.2)),('IV',(0,-4.2))]:
        background=Rectangle(origin,9.25,4.2,facecolor=QUADRANT_COLORS[quadrant],edgecolor='none',zorder=-4)
        background.set_gid('quadrant_background_'+quadrant);ax.add_patch(background)
    for k in ['top','right']:ax.spines[k].set_visible(False)
    ax.axhline(0,color='#9EA4AA',lw=.55,zorder=1);ax.axvline(0,color='#9EA4AA',lw=.55,zorder=1)
    for slope,name in [(1,'unchanged_signed_gap'),(-1,'unchanged_absolute_gap_reversed')]:
        line,=ax.plot([-4.2,4.2],[-4.2*slope,4.2*slope],ls=(0,(4,3)),color='#B2B7BD',lw=.6,zorder=0);line.set_gid(name)
    ax.text(3.62,3.91,'y = x',color='#848B92',fontsize=5.5,rotation=45,ha='center',va='center')
    ax.text(-3.62,3.91,'y = −x',color='#848B92',fontsize=5.5,rotation=-45,ha='center',va='center')
    for i,e in ellipses.iterrows():
        patch=Ellipse((e.center_x,e.center_y),e.width,e.height,angle=e.angle_degrees,facecolor='none',edgecolor=ELLIPSE_COLORS[i],lw=.95,linestyle=STYLES[i],alpha=.95,zorder=4)
        patch.set_gid(f'ellipse_stage_{i}');ax.add_patch(patch)
    for _,r in links.sort_values('geometric_area_pt2',ascending=False).iterrows():
        col=ax.scatter(r.x_observed_gap_pp,r.y_balanced_gap_pp,s=r.matplotlib_s,marker=marker(int(r.stage_index))[0],facecolors=r.colour,edgecolors='white',linewidths=.13,alpha=.76,zorder=3)
        col.set_gid(r.gid)
    quadrants=[(.015,.972,'NSFC → NSF',39,'left','top'),(.985,.972,'NSF higher before & after',129,'right','top'),(.015,.025,'NSFC higher before & after',112,'left','bottom'),(.985,.025,'NSF → NSFC',31,'right','bottom')]
    for q,(xx,yy,title,n,ha,va) in zip(['II','I','III','IV'],quadrants):
        ax.text(xx,yy,f'{title}\n{n} links',transform=ax.transAxes,ha=ha,va=va,fontsize=6.0,color='#4C535A',linespacing=1.3,zorder=5,bbox=dict(facecolor=QUADRANT_COLORS[q],edgecolor='none',pad=1))
    annotations=[]
    for _,r in links[links.labelled].iterrows():
        label,pos=LABELS[r.pair_code]
        annotation=ax.annotate(label,xy=(r.x_observed_gap_pp,r.y_balanced_gap_pp),xytext=pos,fontsize=6.0,ha='center',va='center',linespacing=1.15,color='#272D32',bbox=dict(boxstyle='round,pad=.13',fc='white',ec='none',alpha=.90),arrowprops=dict(arrowstyle='-',lw=.45,color='#7C848C',shrinkA=2,shrinkB=3,connectionstyle='arc3,rad=0'),zorder=6)
        annotation.set_gid('label_'+r.gid);annotations.append((r.gid,annotation))
    ax.set_xlabel('Observed connection share difference: NSF − NSFC (percentage points)',fontsize=6.8,labelpad=6)
    ax.set_ylabel('Balanced connection share difference:\nNSF − NSFC (percentage points)',fontsize=6.8,labelpad=6)
    ax.tick_params(length=2.5,width=.6)
    colour_handles=[Line2D([],[],marker='o',color='none',markerfacecolor=c,markeredgecolor='none',markersize=4,label=t) for c,t in [(BLUE,'NSF share higher after balancing'),(RED,'NSFC share higher after balancing')]]
    fig.legend(handles=colour_handles,loc='center left',bbox_to_anchor=(.115,.214),ncol=2,frameon=False,fontsize=6.4,columnspacing=2.2)
    stage_handles=[Line2D([],[],marker=marker(i)[0],color=ELLIPSE_COLORS[i],linestyle=STYLES[i],markerfacecolor='#818991',markeredgecolor='none',markersize=4,label=STAGE_LABELS[i]) for i in range(3)]
    fig.legend(handles=stage_handles,loc='center left',bbox_to_anchor=(.115,.175),ncol=3,frameon=False,fontsize=6.4,columnspacing=2,handlelength=2.5)
    fig.text(.12,.130,'Area: mean balanced share',fontsize=6.3,color=GREY)
    for xx,m in [(.455,1),(.58,5),(.72,15)]:
        size_legend=ax.scatter(xx+.013,.134,s=AREA_PER_PERCENT*m/marker(0)[1],marker=marker(0)[0],c='#88919A',edgecolors='none',clip_on=False,transform=fig.transFigure)
        size_legend.set_gid(f'area_legend_{m}')
        fig.text(xx+.038,.130,f'{m}%',fontsize=6.3,color=GREY)
    fig.text(.12,.081,'Ellipses enclose all links in each stage (covariance-shaped envelopes), not confidence regions.',fontsize=6.0,color=GREY)
    fig.text(.12,.042,'Axes show point estimates; sign reversals do not imply statistical significance.',fontsize=5.6,color=GREY)
    fig.canvas.draw();renderer=fig.canvas.get_renderer()
    span=fig.transFigure.inverted()
    positions=[dict(gid=gid,text=a.get_text(),bbox_figure=span.transform(a.get_bbox_patch().get_window_extent(renderer).get_points()).tolist()) for gid,a in annotations]
    points_pixels=ax.transData.transform(links[['x_observed_gap_pp','y_balanced_gap_pp']].to_numpy())
    obscured=[]
    for gid,a in annotations:
        bb=a.get_bbox_patch().get_window_extent(renderer)
        for (_,point),xy in zip(links.iterrows(),points_pixels):
            if bb.contains(*xy):obscured.append({'label':gid,'point':point.gid})
    assert not obscured,('Label box covers data coordinates',obscured)
    scale_x=np.linalg.norm(ax.transData.transform((1,0))-ax.transData.transform((0,0)))
    scale_y=np.linalg.norm(ax.transData.transform((0,1))-ax.transData.transform((0,0)))
    record={'width_mm':180,'height_mm':140,'links':len(links),'main_data_axes':1,'unit_scale_pixels':[scale_x,scale_y],'area_pt2_per_share_percent':AREA_PER_PERCENT,'labels':positions,'quadrants':links.quadrant.value_counts().to_dict(),'smaller':int((links.gap_change=='smaller').sum()),'larger':int((links.gap_change=='larger').sum()),'sign_flips':int(links.sign_flip.sum()),'ellipse_scale':1,'ellipse_covariance':'unweighted population covariance; denominator n; no added ridge or minimum dimensions','colour_semantics':'blue: balanced NSF share higher; red: balanced NSFC share higher','area_semantics':'geometric marker fill area calibrated across circle, triangle and square; no minimum area'}
    record.update(height_mm=120,summary_rows_drawn=False,main_data_axes=len(fig.axes),ellipse_colours=dict(zip(STAGES,ELLIPSE_COLORS)),quadrant_background_colours=QUADRANT_COLORS)
    record.update(ellipse_scale=ellipses[['stage','scale','covered_count']].to_dict(orient='records'),ellipse_covariance='Equal-link population covariance orientation; scaled by maximum Mahalanobis distance to cover every stage link; 1e-10 relative boundary tolerance',xlim=[-9.25,9.25],ylim=[-4.2,4.2])
    (NOTE/'plot_definition_and_object_records.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),'utf8')
    stem=OUT/'Figure2b_link_difference_quadrants_and_stage_ellipses'
    for ext in ['pdf','svg','png']:fig.savefig(stem.with_suffix('.'+ext),dpi=600)
    fig.savefig(NOTE/'Figure2b_preview.png',dpi=180);plt.close(fig)
    print(stem.with_suffix('.pdf'))

if __name__=='__main__':draw()
