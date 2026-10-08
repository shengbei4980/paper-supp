from pathlib import Path
import os,sys,json,hashlib
ENV=Path(sys.prefix)
os.environ.setdefault('GDAL_DATA',str(ENV/'Library/share/gdal'));os.environ.setdefault('PROJ_LIB',str(ENV/'Library/share/proj'))
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon
from matplotlib.colors import LinearSegmentedColormap,PowerNorm
from matplotlib.colorbar import ColorbarBase
from pyproj import CRS,Transformer,Geod
from shapely.geometry import box

P=Path(__file__).resolve().parents[1];D=P/'数据';O=P/'出图';Q=P/'复核'
plt.rcParams.update({'font.family':'Arial','font.size':9,'axes.linewidth':.6,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','savefig.facecolor':'white'})
gpkg=D/'Figure3a_州县底图与科研供给.gpkg'
gis_hash_before=hashlib.sha256(gpkg.read_bytes()).hexdigest()
us=gpd.read_file(gpkg,layer='US_counties').rename(columns={'supply_q':'city_supply'});cn=gpd.read_file(gpkg,layer='CN_cities')
states=gpd.read_file(gpkg,layer='US_states').to_crs(4326)
provinces=gpd.read_file(gpkg,layer='CN_provinces').to_crs(4326)
us_top=us.sort_values(['share_pct','GEOID'],ascending=[False,True]).head(10).copy();us_top['rank']=range(1,11)
cn_top=cn.sort_values(['share_pct','adcode'],ascending=[False,True]).head(10).copy();cn_top['rank']=range(1,11)
top_labels=[];bar_records=[];scale_records=[];bar_artists=[]
blue=LinearSegmentedColormap.from_list('supply_blue',['#ddeaf2','#91bcd5','#3a87af','#10466a'],N=1024)
red=LinearSegmentedColormap.from_list('supply_red',['#f4dddd','#d99595','#b84f55','#712432'],N=1024)
norms={'NSF':PowerNorm(.5,vmin=0,vmax=float(us.share_pct.max())),
       'NSFC':PowerNorm(.5,vmin=0,vmax=float(cn.share_pct.max()))}
neutral='#f1f2f3';line='#aab0b5'
state_codes={'06037':'CA','36061':'NY','25017':'MA','08013':'CO','53033':'WA','26161':'MI','04013':'AZ','48041':'TX','06073':'CA','25001':'MA'}
state_names=states.set_index('STUSPS')['NAME'].to_dict()
cn_names={'110000':'Beijing','320100':'Nanjing','420100':'Wuhan','310000':'Shanghai','440100':'Guangzhou','610100':"Xi'an",'620100':'Lanzhou','330100':'Hangzhou','510100':'Chengdu','120000':'Tianjin'}
fig=plt.figure(figsize=(14,10));geod=Geod(ellps='WGS84');decor=[];annotations=[];layout=[]
fig.text(.023,.970,'a',weight='bold',fontsize=19)
fig.text(.063,.970,'Subnational geography of research supply',weight='bold',fontsize=17)
fig.text(.025,.929,'United States · NSF',fontsize=14,weight='bold',color='#21688f')
fig.text(.525,.929,'China · NSFC',fontsize=14,weight='bold',color='#b84f55')
fig.text(.025,.908,f'Counties and equivalents · {us.city_supply.gt(0).sum()} units with supply',fontsize=8.5,color='#555d64')
fig.text(.525,.908,f'Prefecture-level units · {cn.city_supply.gt(0).sum()} units with supply',fontsize=8.5,color='#555d64')

def map_axis(rect,bounds,crs,agency,title=None,frame=False):
    ax=fig.add_axes(rect);ax.set_aspect('equal');proj=CRS.from_user_input(crs)
    src=states if agency=='NSF' else provinces;data=us if agency=='NSF' else cn;cmap=blue if agency=='NSF' else red
    # Clip source selection by geographic window, then project real polygons.
    xmin,ymin,xmax,ymax=bounds
    clip=box(*bounds)
    base=src.cx[xmin:xmax,ymin:ymax].copy();base.geometry=base.geometry.intersection(clip);base=base.to_crs(proj)
    frame_data=data.cx[xmin:xmax,ymin:ymax].copy();frame_data.geometry=frame_data.geometry.intersection(clip);frame_data=frame_data.to_crs(proj)
    base.plot(ax=ax,color=neutral,edgecolor='#b4b9bd' if agency=='NSF' else '#92999e',linewidth=.24 if agency=='NSF' else .38,zorder=1)
    frame_data.plot(ax=ax,color=neutral,edgecolor='#c3c7ca',linewidth=.20,zorder=2)
    positive=frame_data[frame_data.city_supply.gt(0)]
    positive.plot(ax=ax,column='share_pct',cmap=cmap,norm=norms[agency],edgecolor='#8d989f',linewidth=.22,zorder=3)
    base.boundary.plot(ax=ax,color='#93999e',linewidth=.34,zorder=4)
    top=us_top if agency=='NSF' else cn_top
    top_view=top.cx[xmin:xmax,ymin:ymax].copy()
    if not top_view.empty:
        top_view.geometry=top_view.geometry.intersection(clip)
        top_view.to_crs(proj).boundary.plot(ax=ax,color='#31566b' if agency=='NSF' else '#804148',linewidth=.65,zorder=5)
    fwd=Transformer.from_crs(4326,proj,always_xy=True)
    # Densified box determines limits without clipping curved projected map edges.
    xx=np.r_[np.linspace(xmin,xmax,60),np.linspace(xmin,xmax,60),np.full(60,xmin),np.full(60,xmax)]
    yy=np.r_[np.full(60,ymin),np.full(60,ymax),np.linspace(ymin,ymax,60),np.linspace(ymin,ymax,60)]
    xp,yp=fwd.transform(xx,yy)
    limits=base.total_bounds if not frame else [min(xp),min(yp),max(xp),max(yp)]
    cx,cy=(limits[0]+limits[2])/2,(limits[1]+limits[3])/2
    width,height=(limits[2]-limits[0])*1.10,(limits[3]-limits[1])*1.10
    panel_ratio=rect[2]*fig.get_figwidth()/(rect[3]*fig.get_figheight())
    if width/height<panel_ratio:width=height*panel_ratio
    else:height=width/panel_ratio
    ax.set_xlim(cx-width/2,cx+width/2);ax.set_ylim(cy-height/2,cy+height/2);ax.set_xticks([]);ax.set_yticks([])
    for spine in ax.spines.values():spine.set_visible(frame);spine.set_color('#b3b8bc');spine.set_linewidth(.5)
    if title:ax.set_title(title,loc='left',fontsize=8,pad=5,color='#3a4146')
    ax._geo=(proj,fwd,Transformer.from_crs(proj,4326,always_xy=True));ax._agency=agency;ax._bounds=bounds
    layout.append({'title':title or agency+'_main','frame':frame,'rectangle':rect})
    return ax

def scale(ax,total_km,xy=(.06,.06),fontsize=7,simple=False):
    proj,fwd,inv=ax._geo;x0,x1=ax.get_xlim();y0,y1=ax.get_ylim();x=x0+(x1-x0)*xy[0];y=y0+(y1-y0)*xy[1]
    lon0,lat0=inv.transform(x,y)
    def solve(km):
        lo=0.;hi=km*1000*2
        for _ in range(55):
            mid=(lo+hi)/2;lon,lat=inv.transform(x+mid,y);dist=geod.inv(lon0,lat0,lon,lat)[2]
            if dist<km*1000:lo=mid
            else:hi=mid
        return (lo+hi)/2
    pos=[0,solve(total_km/4),solve(total_km/2),solve(total_km)]
    h=(y1-y0)*.008
    for i in range(3):ax.add_patch(Rectangle((x+pos[i],y),pos[i+1]-pos[i],h,fc='#20272b' if i%2==0 else 'white',ec='#20272b',lw=.5,zorder=20))
    ticks=[(0,0),(total_km,pos[-1])] if simple else list(zip([0,total_km/4,total_km/2,total_km],pos))
    for v,px in ticks:
        text=f'{v:g}' if v!=total_km or not simple else f'{v:g} km'
        ax.text(x+px,y-h*1.7,text,ha='left' if simple and v==total_km else 'center',va='top',fontsize=fontsize,zorder=21,bbox=dict(fc='white',ec='none',alpha=.90,pad=.3))
    if not simple:ax.text(x+pos[-1]+(x1-x0)*.024,y-h*1.7,'km',ha='left',va='top',fontsize=fontsize,zorder=21)
    lon1,lat1=inv.transform(x+pos[-1],y)
    decor.append({'agency':ax._agency,'kind':'scale','declared_km':total_km,'geodesic_km':geod.inv(lon0,lat0,lon1,lat1)[2]/1000,'horizontal':True,'projection':proj.to_string()})

def north(ax,xy=(.93,.84),size=.070):
    proj,fwd,inv=ax._geo;x0,x1=ax.get_xlim();y0,y1=ax.get_ylim();x=x0+(x1-x0)*xy[0];y=y0+(y1-y0)*xy[1]
    # Reference true north at the projected map-frame centre; symbol placement is independent.
    reference_x,reference_y=(x0+x1)/2,(y0+y1)/2
    lon,lat=inv.transform(reference_x,reference_y)
    end_lon,end_lat,_=geod.fwd(lon,lat,0,1000)
    nx,ny=fwd.transform(end_lon,end_lat);v=np.array([nx-reference_x,ny-reference_y]);v=v/np.linalg.norm(v)
    h=(y1-y0)*size;perp=np.array([-v[1],v[0]])
    base=np.array([x,y]);tip=base+v*h;left=base-perp*h*.18;right=base+perp*h*.18;notch=base+v*h*.24
    ax.add_patch(Polygon([tip,left,notch],fc='#20272b',ec='#20272b',lw=.6,zorder=20))
    ax.add_patch(Polygon([tip,notch,right],fc='white',ec='#20272b',lw=.6,zorder=20))
    lab=tip+v*h*.24;ax.text(*lab,'N',ha='center',va='center',fontsize=8,zorder=21)
    decor.append({'agency':ax._agency,'kind':'north','reference':'projected_map_frame_center','longitude':lon,'latitude':lat,'reference_projected':[reference_x,reference_y],'symbol_position_axes':list(xy),'projection':proj.to_string(),'angle_from_vertical_deg':float(np.degrees(np.arctan2(v[0],v[1])))})

def label(ax,lon,lat,text,offset,textcoords='offset points'):
    x,y=ax._geo[1].transform(lon,lat)
    item=ax.annotate(text,(x,y),xytext=offset,textcoords=textcoords,fontsize=8,ha='left',va='center',color='#323a40',arrowprops=dict(arrowstyle='-',color='#7a858d',lw=.55),bbox=dict(fc='white',ec='none',alpha=.9,pad=1.2),zorder=30)
    annotations.append(item)

def ranked_label(ax,unit,offset,view,textcoords='offset points'):
    source,key=(us_top,'GEOID') if ax._agency=='NSF' else (cn_top,'adcode')
    row=source[source[key].astype(str).eq(unit)].iloc[0]
    if ax._agency=='NSF':
        name=f'{row.NAME} County'
        full_name=f'{name}, {state_names[state_codes[unit]]}'
    else:
        name=cn_names[unit];full_name=name
    # Use an interior point of the actual displayed administrative polygon.
    visible_geometry=row.geometry.intersection(box(*ax._bounds))
    assert not visible_geometry.is_empty,unit
    point=gpd.GeoSeries([visible_geometry],crs=4326).to_crs(ax._geo[0]).representative_point().to_crs(4326).iloc[0]
    # Exact percentages are shown on the bars rather than duplicated on the map.
    text=f'{int(row["rank"])}  {name}'
    label(ax,point.x,point.y,text,offset,textcoords)
    top_labels.append({'agency':ax._agency,'unit_id':unit,'rank':int(row['rank']),'name':name,'full_name':full_name,'share_pct':float(row.share_pct),'view':view,'longitude':point.x,'latitude':point.y})

u=map_axis([.025,.543,.465,.350],[-125,24,-66,50],'EPSG:5070','NSF')
c=map_axis([.520,.543,.465,.350],[73,18,136,54],'+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 +datum=WGS84 +units=m','NSFC')
scale(u,1200,xy=(.055,.05));north(u,(.965,.84))
scale(c,1200,xy=(.055,.05));north(c,(.965,.84))
for unit,offset in {'06037':(-57,10),'08013':(-85,25),'53033':(10,25),'26161':(-100,33),'04013':(16,-9),'48041':(-93,-16),'06073':(0,-30)}.items():ranked_label(u,unit,offset,'main')
for unit,offset in {'110000':(-74,29),'120000':(26,10),'420100':(22,-2),'440100':(-38,-34),'610100':(20,16),'620100':(-85,22),'510100':(-77,-9)}.items():ranked_label(c,unit,offset,'main')

ak=map_axis([.220,.399,.095,.115],[-170,51,-130,72],'EPSG:3338','NSF','Alaska',True)
hi=map_axis([.327,.399,.067,.115],[-161,18,-154,23],'+proj=aea +lat_1=18 +lat_2=23 +lat_0=20 +lon_0=-157 +datum=WGS84 +units=m','NSF','Hawaii',True)
pr=map_axis([.406,.399,.084,.115],[-67.4,17.55,-64.4,18.65],'+proj=aea +lat_1=17 +lat_2=20 +lat_0=18 +lon_0=-66 +datum=WGS84 +units=m','NSF','Puerto Rico and the\nU.S. Virgin Islands',True)
ne=map_axis([.025,.399,.183,.115],[-75.7,39.1,-69.8,43.2],'+proj=aea +lat_1=39 +lat_2=44 +lat_0=40 +lon_0=-73 +datum=WGS84 +units=m','NSF','Northeast detail',True)
for unit,offset in {'36061':(.025,.19),'25017':(.025,.87),'25001':(.025,.49)}.items():ranked_label(ne,unit,offset,'Northeast inset','axes fraction')
yr=map_axis([.545,.399,.250,.115],[118,29.6,122.3,33.2],'+proj=aea +lat_1=29 +lat_2=34 +lat_0=31 +lon_0=120 +datum=WGS84 +units=m','NSFC','Yangtze River Delta detail',True)
for unit,offset in {'320100':(.035,.73),'310000':(.72,.43),'330100':(.04,.14)}.items():ranked_label(yr,unit,offset,'Yangtze inset','axes fraction')
sc=map_axis([.817,.399,.153,.115],[105,3.5,123,24],'+proj=aea +lat_1=5 +lat_2=25 +lat_0=15 +lon_0=114 +datum=WGS84 +units=m','NSFC','South China Sea',True)

for x,cmap,agency in [(.055,blue,'NSF'),(.555,red,'NSFC')]:
    norm=norms[agency]
    ticks=([0,.1,.5,1,2,norm.vmax] if agency=='NSF' else [0,.1,.5,1,5,10,norm.vmax])
    fig.text(x,.378,('County' if agency=='NSF' else 'City')+' supply / national sample supply (%)',fontsize=8.5)
    cbax=fig.add_axes([x,.355,.395,.014])
    cb=ColorbarBase(cbax,cmap=cmap,norm=norm,ticks=ticks,orientation='horizontal')
    cb.ax.set_xticklabels([f'{v:g}' if i<len(ticks)-1 else f'{v:.3f}' for i,v in enumerate(ticks)])
    cb.ax.tick_params(labelsize=7,length=2,pad=2);cb.outline.set_linewidth(.45)
    scale_records.append({'agency':agency,'vmin':float(norm.vmin),'vmax':float(norm.vmax),'gamma':float(norm.gamma),'tick_values_pct':ticks})
fig.patches.append(Rectangle((.025,.320),.010,.009,transform=fig.transFigure,fc=neutral,ec=line,lw=.5))
fig.text(.042,.320,'No allocated sample supply',fontsize=7.5,color='#555d64')
fig.text(.305,.320,'Map colours: square-root scaling; separate national ranges. Dark outlines and ranks identify the top 10.',fontsize=7.5,color='#555d64')
fig.add_artist(plt.Line2D([.025,.985],[.309,.309],transform=fig.transFigure,color='#d6dadd',lw=.55))

def ranking_bars(agency: str, left: float, xmax: float) -> None:
    """Compact national ranking; bar values are untransformed percentage shares."""
    color,pale=('#327fa8','#e3edf3') if agency=='NSF' else ('#bb5059','#f3e4e5')
    rows=sorted((r for r in top_labels if r['agency']==agency),key=lambda r:r['rank'])
    fig.text(left,.293,'Top 10 '+('counties' if agency=='NSF' else 'cities'),weight='bold',fontsize=9,color=color)
    ax=fig.add_axes([left+.207,.101,.245,.181])
    y=np.arange(10);values=np.array([r['share_pct'] for r in rows])
    bars=ax.barh(y,values,height=.62,color=color,zorder=3)
    ax.set_ylim(9.7,-.7);ax.set_xlim(0,xmax)
    ax.set_yticks(y,[f'{r["rank"]:2d}  {r["full_name"]}' for r in rows])
    ax.tick_params(axis='y',length=0,pad=6,labelsize=7.5)
    ax.set_xticks(np.arange(0,xmax+.01,.5 if agency=='NSF' else 5))
    ax.tick_params(axis='x',length=2.5,pad=2,labelsize=7)
    ax.set_xlabel('National sample supply (%)',fontsize=7.5,labelpad=3)
    ax.grid(axis='x',color='#e3e6e8',lw=.45,zorder=0);ax.set_axisbelow(True)
    for side in ['top','right','left']:ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color('#aab0b5')
    for row,bar in zip(rows,bars):
        bar_artists.append(ax.text(row['share_pct']+xmax*.016,bar.get_y()+bar.get_height()/2,f'{row["share_pct"]:.2f}%',ha='left',va='center',fontsize=7.5,color=color))
        bar_records.append({**row,'bar_width_pct':float(bar.get_width()),'bar_axis_min':0.,'bar_axis_max':xmax})
    bar_artists.extend(ax.get_yticklabels()+ax.get_xticklabels()+[ax.xaxis.label])
    # Two identically sized 100% strips provide the common-scale comparison.
    total=float(values.sum());strip=fig.add_axes([left,.036,.452,.020])
    strip.barh([0],[total],height=1,color=color)
    strip.barh([0],[100-total],left=[total],height=1,color=pale)
    strip.set_xlim(0,100);strip.set_ylim(-.5,.5);strip.axis('off')
    for xpos,text,ink in [(total/2,f'Top 10  {total:.2f}%','white'),(total+(100-total)/2,f'Others  {100-total:.2f}%','#535d65')]:
        bar_artists.append(strip.text(xpos,0,text,ha='center',va='center',fontsize=8,color=ink))
    scale_records.append({'agency':agency,'bar_axis_range_pct':[0,xmax],'bar_rectangle':list(ax.get_position().bounds),'strip_rectangle':list(strip.get_position().bounds),'strip_axis_range_pct':[0,100],'top10_pct':total,'others_pct':100-total})

ranking_bars('NSF',.025,3.)
ranking_bars('NSFC',.525,25.)
fig.text(.025,.011,'Ranked bars use separate linear axes; concentration strips share a 0–100% scale. U.S. counties and Chinese cities are distinct administrative units.',fontsize=7.5,color='#555d64')
base=O/'Figure3a_县域与城市科研供给'
fig.canvas.draw()
renderer=fig.canvas.get_renderer()
out_of_canvas=[]
for item in annotations+fig.texts+bar_artists:
    bbox=item.get_window_extent(renderer)
    if not fig.bbox.contains(bbox.x0,bbox.y0) or not fig.bbox.contains(bbox.x1,bbox.y1):out_of_canvas.append(item.get_text())
assert not out_of_canvas,out_of_canvas
assert len(top_labels)==20
pd.DataFrame(top_labels).to_csv(D/'Figure3a_Top10标签对应.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(bar_records).to_csv(D/'Figure3a_Top10柱状图数据.csv',index=False,encoding='utf-8-sig')
(Q/'色带与柱状图参数.json').write_text(json.dumps(scale_records,ensure_ascii=False,indent=2),encoding='utf8')
assert hashlib.sha256(gpkg.read_bytes()).hexdigest()==gis_hash_before
(Q/'图面排版核验.json').write_text(json.dumps({'panels':layout,'out_of_canvas':out_of_canvas,'gis_sha256_before':gis_hash_before,'gis_sha256_after':hashlib.sha256(gpkg.read_bytes()).hexdigest(),'reference_note':'North direction is referenced to each main map-frame centre, independent of symbol placement.'},ensure_ascii=False,indent=2),encoding='utf8')
fig.savefig(base.with_suffix('.pdf'),dpi=600)
fig.savefig(base.with_suffix('.svg'),dpi=600)
fig.savefig(base.with_suffix('.png'),dpi=600)
fig.savefig(base.with_suffix('.tiff'),dpi=600,pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(O/'预览.png',dpi=300)
(Q/'比例尺与指北针参数.json').write_text(json.dumps(decor,ensure_ascii=False,indent=2),encoding='utf8')
print(base)
