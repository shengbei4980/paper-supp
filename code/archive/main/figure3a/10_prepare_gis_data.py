from pathlib import Path
import os,sys,json,hashlib,re
ENV=Path(sys.prefix)
os.environ.setdefault('GDAL_DATA',str(ENV/'Library/share/gdal'));os.environ.setdefault('PROJ_LIB',str(ENV/'Library/share/proj'))
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point

P=Path(__file__).resolve().parents[1];D=P/'数据';I=D/'输入';Q=P/'复核'
sources={str(x.relative_to(P)):hashlib.sha256(x.read_bytes()).hexdigest() for x in I.iterdir() if x.is_file()}
cross=pd.read_csv(I/'全部机构城市_行政归属校正表.csv').fillna({'gis_unit_id':''})
cross.loc[cross.city_id.eq('NSF|NY|CLINTON'),['longitude_wgs84','latitude_wgs84']]=cross.loc[cross.city_id.eq('NSF|NY|CLINTON'),['gis_anchor_lon','gis_anchor_lat']].to_numpy()
cross['unit_id']=cross.gis_unit_id.where(cross.gis_unit_id.ne(''),'unresolved_'+cross.city_id)
rows=[]
for (agency,unit),group in cross.groupby(['agency','unit_id']):
    ordered=group.sort_values('city_supply',ascending=False)
    legal=str(ordered.iloc[0].gis_unit_name)
    candidates=ordered[ordered.city_name_en.map(lambda x:legal.lower().startswith(str(x).lower()+' '))]
    rep=(candidates if not candidates.empty else ordered).iloc[0]
    name=rep.city_name_en
    if agency=='NSF' and not unit.startswith('unresolved_'):
        name=re.sub(r' (city and borough|city|township|town|village|borough|municipality|CDP)$','',legal)
    rows.append(dict(agency=agency,city_id=unit,city_name_en=name,city_supply=group.city_supply.sum(),share_pct=group.city_supply.sum()/(5000 if agency=='NSF' else 5546)*100,longitude_wgs84=rep.longitude_wgs84,latitude_wgs84=rep.latitude_wgs84,source_city_n=len(group),source_city_ids=';'.join(group.city_id),point_basis='source representative city location; not exact institution address'))
cities=pd.DataFrame(rows);cities['top10']=False
for agency in ['NSF','NSFC']:
    idx=cities[cities.agency.eq(agency)].nlargest(10,'city_supply').index;cities.loc[idx,'top10']=True
cities['manuscript_example']=cities.city_name_en.isin(['College Station','Houston','Beijing','Nanjing'])
cities.to_csv(D/'城市供给点.csv',index=False,encoding='utf-8-sig')
points=gpd.GeoDataFrame(cities,geometry=gpd.points_from_xy(cities.longitude_wgs84,cities.latitude_wgs84),crs=4326)
original_points=gpd.GeoDataFrame(cross,geometry=gpd.points_from_xy(cross.longitude_wgs84,cross.latitude_wgs84),crs=4326)
layers={x:gpd.read_file(I/'地理边界.gpkg',layer=x).to_crs(4326) for x in ['US_states','US_counties','CN_provinces','CN_cities']}
counties=layers['US_counties'];counties['GEOID']=counties.GEOID.astype(str).str.zfill(5)
raw=pd.read_csv(I/'NSF_编码结果_城市归属校正版.csv',dtype={'record_id':str})
projects=pd.read_csv(I/'项目级城市归属_校正版.csv',dtype={'record_id':str})
records=raw[['record_id','organization','institution_region','institution_city','longitude_wgs84','latitude_wgs84']].merge(projects[projects.agency.eq('NSF')][['record_id','city_weight','city_id']],on='record_id',validate='one_to_one')
locations=gpd.GeoDataFrame(records,geometry=gpd.points_from_xy(records.longitude_wgs84,records.latitude_wgs84),crs=4326)
located=gpd.sjoin(locations,counties[['GEOID','NAME','geometry']],how='left',predicate='within').drop(columns='index_right')
assert not located.record_id.duplicated().any(),'Boundary ambiguity requires explicit review'
located['county_match_method']=np.where(located.GEOID.notna(),'source_coordinate_within_county','unmatched')
# Do not snap out-of-boundary points or reassign unresolved records without evidence.
totals=located.dropna(subset=['GEOID']).groupby('GEOID').agg(supply_q=('city_weight','sum'),project_n=('record_id','size'),source_city_n=('city_id','nunique'))
counties=counties.merge(totals,on='GEOID',how='left');counties[['supply_q','project_n','source_city_n']]=counties[['supply_q','project_n','source_city_n']].fillna(0)
counties['share_pct']=counties.supply_q/5000*100;counties['has_supply']=counties.supply_q.gt(0).astype(int);layers['US_counties']=counties
cnstats=pd.read_csv(I/'NSFC_城市面供给汇总.csv',dtype={'adcode':str})
cn=layers['CN_cities'];cn['adcode']=cn.adcode.astype(str)
cn=cn.merge(cnstats[['adcode','city_supply','share_pct']],on='adcode',how='left',validate='one_to_one')
cn[['city_supply','share_pct']]=cn[['city_supply','share_pct']].fillna(0);cn['has_supply']=cn.city_supply.gt(0).astype(int);layers['CN_cities']=cn
gpkg=D/'Figure3a_州县底图与科研供给.gpkg'
for name,frame in list(layers.items())+[('city_supply_points',points),('source_city_points',original_points),('NSF_project_locations',located)]:
    frame.to_file(gpkg,layer=name,driver='GPKG')
    reread=gpd.read_file(gpkg,layer=name);assert len(reread)==len(frame)
counties.drop(columns='geometry').to_csv(D/'NSF_县域供给汇总.csv',index=False,encoding='utf-8-sig')
located.drop(columns='geometry').to_csv(D/'NSF_项目到县对应.csv',index=False,encoding='utf-8-sig')
located[located.GEOID.isna()].drop(columns='geometry').to_csv(D/'NSF_县域未匹配项目.csv',index=False,encoding='utf-8-sig')
summary=cities.groupby('agency').agg(cities=('city_id','size'),supply=('city_supply','sum'))
summary['top10_pct']=cities[cities.top10].groupby('agency').share_pct.sum();summary.reset_index().to_csv(D/'集中份额.csv',index=False,encoding='utf-8-sig')
checks={'city_supply_NSF':float(cities[cities.agency.eq('NSF')].city_supply.sum()),'city_supply_NSFC':float(cities[cities.agency.eq('NSFC')].city_supply.sum()),'NSF_county_assigned':float(counties.supply_q.sum()),'NSF_county_unassigned':float(located.loc[located.GEOID.isna(),'city_weight'].sum()),'unmatched_records':int(located.GEOID.isna().sum()),'input_hashes':sources,'layers':{n:len(f) for n,f in list(layers.items())+[('city_supply_points',points),('source_city_points',original_points),('NSF_project_locations',located)]}}
assert np.isclose(checks['city_supply_NSF'],5000) and np.isclose(checks['city_supply_NSFC'],5546)
assert np.isclose(checks['NSF_county_assigned']+checks['NSF_county_unassigned'],5000)
assert all(hashlib.sha256((P/name).read_bytes()).hexdigest()==h for name,h in sources.items())
(Q/'数据及GIS核验.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in checks.items() if k!='input_hashes'},ensure_ascii=False,indent=2))
