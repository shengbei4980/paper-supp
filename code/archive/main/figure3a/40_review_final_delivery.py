from pathlib import Path
import os,sys,json,hashlib
ENV=Path(sys.prefix)
os.environ.setdefault('GDAL_DATA',str(ENV/'Library/share/gdal'));os.environ.setdefault('PROJ_LIB',str(ENV/'Library/share/proj'))
import numpy as np
import pandas as pd
import geopandas as gpd
from PIL import Image
from pyproj import Proj
P=Path(__file__).resolve().parents[1];D=P/'数据';G=D/'Figure3a_州县底图与科研供给.gpkg';checks=[]
def check(name,ok): checks.append({'check':name,'passed':bool(ok)})
expected={'US_states':56,'US_counties':3235,'CN_provinces':34,'CN_cities':370,'city_supply_points':637,'source_city_points':653,'NSF_project_locations':6207}
layers={x:gpd.read_file(G,layer=x) for x in expected}
for n,f in layers.items():
    check(n+'数量',len(f)==expected[n]);check(n+'坐标系',f.crs.to_epsg()==4326);check(n+'几何非空',f.geometry.notna().all() and ~f.geometry.is_empty.any())
us=layers['US_counties'];cn=layers['CN_cities'];points=layers['NSF_project_locations']
check('县GEOID唯一',us.GEOID.is_unique);check('项目ID唯一',points.record_id.is_unique)
check('全部项目均有县归属',points.GEOID.notna().all())
check('县域供给全国总和5000',np.isclose(us.supply_q.sum(),5000))
check('中国供给全国总和5546',np.isclose(cn.city_supply.sum(),5546))
check('县域份额全国总和100%',np.isclose(us.share_pct.sum(),100))
check('中国份额全国总和100%',np.isclose(cn.share_pct.sum(),100))
independent=points.groupby('GEOID').city_weight.sum()
check('县域供给逐县独立重算',np.allclose(us.supply_q,us.GEOID.map(independent).fillna(0)))
check('全部项目点在对应县内',all(p.within(g) for p,g in zip(points.geometry,points.GEOID.map(us.set_index('GEOID').geometry))))
check('有供给县352个',us.supply_q.gt(0).sum()==352)
check('有供给中国城市126个',cn.city_supply.gt(0).sum()==126)
labels=pd.read_csv(D/'Figure3a_Top10标签对应.csv',dtype={'unit_id':str})
check('图中共20个Top10标签且不重复',len(labels)==20 and not labels.duplicated(['agency','unit_id']).any())
for agency,frame,key in [('NSF',us,'GEOID'),('NSFC',cn,'adcode')]:
    expected_top=frame.sort_values(['share_pct',key],ascending=[False,True]).head(10)
    displayed=labels[labels.agency.eq(agency)].sort_values('rank')
    check(agency+'标签恰为供给前10名',displayed.unit_id.tolist()==expected_top[key].astype(str).tolist())
    check(agency+'标签份额与数据逐项一致',np.allclose(displayed.share_pct.to_numpy(),expected_top.share_pct.to_numpy()))
    check(agency+'标签份额之和与Top10说明一致',np.isclose(displayed.share_pct.sum(),expected_top.share_pct.sum()))
bars=pd.read_csv(D/'Figure3a_Top10柱状图数据.csv',dtype={'unit_id':str})
chart_meta=json.loads((P/'复核/色带与柱状图参数.json').read_text(encoding='utf8'))
check('20根排名柱对应20个不重复单元',len(bars)==20 and not bars.duplicated(['agency','unit_id']).any())
for agency,frame,key in [('NSF',us,'GEOID'),('NSFC',cn,'adcode')]:
    ranked=frame.sort_values(['share_pct',key],ascending=[False,True]).head(10)
    shown=bars[bars.agency.eq(agency)].sort_values('rank')
    color=next(x for x in chart_meta if x['agency']==agency and 'gamma' in x)
    bar=next(x for x in chart_meta if x['agency']==agency and 'top10_pct' in x)
    check(agency+'色带覆盖真实范围且以真实最大值为端点',color['vmin']==0 and np.isclose(color['vmax'],frame.share_pct.max(),rtol=0,atol=1e-12))
    check(agency+'色带使用平方根映射且刻度均在真实范围内',color['gamma']==.5 and all(0<=v<=color['vmax'] for v in color['tick_values_pct']))
    check(agency+'柱状图排序与源数据一致',shown.unit_id.tolist()==ranked[key].astype(str).tolist())
    check(agency+'实际绘制柱长等于源份额',np.allclose(shown.bar_width_pct,ranked.share_pct))
    check(agency+'排名柱线性轴起点为零且覆盖全部柱',bar['bar_axis_range_pct'][0]==0 and bar['bar_axis_range_pct'][1]>ranked.share_pct.max())
    check(agency+'集中份额条与独立求和一致',np.isclose(bar['top10_pct'],ranked.share_pct.sum()) and np.isclose(bar['top10_pct']+bar['others_pct'],100))
    check(agency+'集中份额条统一0至100刻度',bar['strip_axis_range_pct']==[0,100])
full_states=layers['US_states'].NAME.tolist()
check('美国柱标签包含County及完整州名',all(' County, ' in n and n.rsplit(', ',1)[1] in full_states for n in bars[bars.agency.eq('NSF')].full_name))
bar_rects=[x['bar_rectangle'] for x in chart_meta if 'bar_rectangle' in x]
strip_rects=[x['strip_rectangle'] for x in chart_meta if 'strip_rectangle' in x]
check('两列排名柱统一高度宽度和基线',np.allclose(np.array(bar_rects)[0,1:],np.array(bar_rects)[1,1:]))
check('两条集中份额条统一宽度高度和基线',np.allclose(np.array(strip_rects)[0,1:],np.array(strip_rects)[1,1:]))
meta=json.loads((P/'复核/数据及GIS核验.json').read_text(encoding='utf8'))
check('输入源文件未改动',all(hashlib.sha256((P/k).read_bytes()).hexdigest()==h for k,h in meta['input_hashes'].items()))
decorations=json.loads((P/'复核/比例尺与指北针参数.json').read_text(encoding='utf8'))
scales=[x for x in decorations if x['kind']=='scale']
check('仅保留两幅主图比例尺',len(scales)==2 and {x['agency'] for x in scales}=={'NSF','NSFC'} and all(x['declared_km']==1200 for x in scales))
for item in decorations:
    if item['kind']=='scale':check('水平比例尺测地校准:'+str(item['declared_km']),item['horizontal'] and abs(item['declared_km']-item['geodesic_km'])<1e-5)
    if item['kind']=='north':
        convergence=Proj(item['projection']).get_factors(item['longitude'],item['latitude']).meridian_convergence
        check(item['agency']+'指北针以主图中心为参考',item['reference']=='projected_map_frame_center')
        check(item['agency']+'指北方向与独立子午线收敛角计算一致',abs(item['angle_from_vertical_deg']+convergence)<1e-5)
        bounds=(-125,24,-66,50) if item['agency']=='NSF' else (73,18,136,54)
        check(item['agency']+'真北参考点位于主图地理范围内',bounds[0]<item['longitude']<bounds[2] and bounds[1]<item['latitude']<bounds[3])
layout=json.loads((P/'复核/图面排版核验.json').read_text(encoding='utf8'))
check('GIS文件本轮未改动',layout['gis_sha256_before']==layout['gis_sha256_after']==hashlib.sha256(G.read_bytes()).hexdigest())
check('文字标注未超出画布',not layout['out_of_canvas'])
main=[x['rectangle'] for x in layout['panels'] if not x['frame']]
insets=[x['rectangle'] for x in layout['panels'] if x['frame']]
check('两幅主图统一高度及基线',len({(x[1],x[3]) for x in main})==1)
check('六幅插图统一高度及基线',len(insets)==6 and len({(x[1],x[3]) for x in insets})==1)
for ext in ['png','pdf','svg','tiff']:
    f=P/'出图'/('Figure3a_县域与城市科研供给.'+ext);check('输出格式:'+ext,f.is_file() and f.stat().st_size>10000)
im=Image.open(P/'出图/Figure3a_县域与城市科研供给.png');check('600dpi PNG尺寸',im.size==(8400,6000))
out={'passed':sum(c['passed'] for c in checks),'total':len(checks),'county_top10_pct':float(us.share_pct.nlargest(10).sum()),'china_top10_pct':float(cn.share_pct.nlargest(10).sum()),'checks':checks,'known_limitation':'中国既有边界含相邻面重叠；按行政代码归并，未用面积分摊。美国县归属依据源项目坐标，并不等于逐机构门牌核验。'}
(P/'复核/最终交付核验.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in out.items() if k!='checks'},ensure_ascii=False,indent=2))
assert all(c['passed'] for c in checks),[c for c in checks if not c['passed']]
