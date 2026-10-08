"""Independent CSV/dictionary reconstruction; does not import the build module."""
from pathlib import Path
from collections import defaultdict
import csv,json,hashlib,math
import xml.etree.ElementTree as ET
from PIL import Image

ROOT=Path(__file__).resolve().parents[1];D=ROOT/'数据';I=D/'输入快照';O=ROOT/'图'
PREFIX='Figure3c_固定主要科研承担地的跨目标贡献'
def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def verify():
    p=read(I/'projects.csv');m={x['record_id']:x['GEOID'] for x in read(I/'us_county_mapping.csv')}
    totals=defaultdict(float);local=defaultdict(float);national=defaultdict(float)
    local_families=defaultdict(set);national_families=defaultdict(set);local_records=defaultdict(set)
    for r in p:
        a=r['agency'];u='US_'+m[r['record_id']] if a=='NSF' else r['gis_unit_id']
        w=float(r['city_weight']);totals[(a,u)]+=w
        goals=r['sdg_goal_multi'].replace('|',';').split(';')
        assert len(goals)==int(r['sdg_count']) and len(goals)==len(set(goals))
        for g in goals:
            k=(a,u,g);local[k]+=w/len(goals);national[(a,g)]+=w/len(goals)
            local_families[k].add(r['project_family_id']);national_families[(a,g)].add(r['project_family_id'])
            local_records[k].add(r['record_id'])
    tops={a:[u for (aa,u),v in sorted(totals.items(),key=lambda item:(-item[1],item[0][1])) if aa==a][:10] for a in ['NSF','NSFC']}
    saved_tops=read(D/'固定总体前十地点.csv')
    assert len(saved_tops)==20
    for a in tops:
        assert [r['unit_id'] for r in sorted(saved_tops,key=lambda r:int(r['overall_rank'])) if r['agency']==a]==tops[a]
    rows=read(D/'Figure3c_12SDG固定前十贡献.csv');errors=[]
    for r in rows:
        a,g=r['agency'],r['sdg'];num=sum(local[(a,u,g)] for u in tops[a]);den=national[(a,g)]
        errors.extend([abs(num-float(r['top10_goal_supply'])),abs(den-float(r['national_goal_supply'])),abs(100*num/den-float(r['fixed_top10_share_pct']))])
        assert len(national_families[(a,g)])==int(r['national_goal_family_n'])
        fam=set().union(*(local_families[(a,u,g)] for u in tops[a]))
        assert len(fam)==int(r['top10_goal_family_n'])
        assert sum(local[(a,u,g)]>0 for u in tops[a])==int(r['top10_positive_location_n'])
        assert math.isclose(float(r['other_locations_share_pct'])+float(r['fixed_top10_share_pct']),100,abs_tol=1e-10)
    assert max(errors)<1e-8,max(errors)
    details=read(D/'固定前十_12SDG_逐地点明细.csv')
    assert len(details)==240 and len({(r['agency'],r['unit_id'],r['sdg']) for r in details})==240
    for r in details:
        k=(r['agency'],r['unit_id'],r['sdg'])
        assert abs(local[k]-float(r['supply']))<1e-8
        assert len(local_families[k])==int(float(r['project_family_n']))
    draws=read(D/'Figure3c_点位绘制对应.csv')
    truth={(r['agency'],r['sdg']):r for r in rows}
    assert len(draws)==len(truth)==24
    goals=['S02','S03','S06','S07','S09','S10','S11','S12','S13','S15','S16','S17']
    for r in draws:
        value=float(truth[(r['agency'],r['sdg'])]['fixed_top10_share_pct'])
        assert abs(float(r['x_pct'])-value)<1e-10
        assert int(r['y_row'])==goals.index(r['sdg'])
        assert r['display_value']==f'{value:.1f}'
    svg=ET.parse(O/(PREFIX+'.svg')).getroot()
    markers=[e for e in svg.iter() if e.get('id','').startswith('observation_')]
    assert len(markers)==24 and {e.get('id') for e in markers}=={r['glyph_id'] for r in draws}
    assert all(e.find('{http://www.w3.org/2000/svg}title') is not None for e in markers)
    raster={}
    for ext in ['png','tiff']:
        with Image.open(O/(PREFIX+'.'+ext)) as im:
            assert min(im.info.get('dpi',(0,0)))>=599
            assert im.size==(4320,2430)
            raster[ext]={'pixels':im.size,'dpi':[float(v) for v in im.info['dpi']]}
    for item in json.loads((D/'输入清单.json').read_text(encoding='utf-8')):
        h=hashlib.sha256((I/item['file']).read_bytes()).hexdigest()
        assert h==item['sha256']==hashlib.sha256(Path(item['source']).read_bytes()).hexdigest()
    report={'passed':True,'source_records':len(p),'independently_checked_goal_pairs':24,
            'independently_checked_top_location_goal_rows':240,'max_independent_numerical_error':max(errors),
            'unique_top_locations':20,'svg_unique_observations':len(markers),'all_input_hashes_match':True,
            'all_numeric_labels_and_coordinates_match':True,'raster_exports':raster,
            'NSFC_all_12_above_50':all(float(r['fixed_top10_share_pct'])>50 for r in rows if r['agency']=='NSFC'),
            'NSF_all_12_below_30':all(float(r['fixed_top10_share_pct'])<30 for r in rows if r['agency']=='NSF')}
    (D/'独立数据与导出复核.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':verify()
